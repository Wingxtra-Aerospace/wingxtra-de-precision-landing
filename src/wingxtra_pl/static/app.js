"use strict";
const $ = (id) => document.getElementById(id);
let config,
  board,
  cameraProfiles = {},
  lastStatus,
  lastStatusAt = 0,
  previewBusy = { preview: false, "cal-preview": false },
  activeTab = "overview";
const pendingCalibration = new Set();
const setupFields =
  "#camera-form input,#camera-form select,#camera-form textarea,#camera-form button,#connection-form input,#connection-form select,#connection-form textarea,#connection-form button,#board-save,#board-import,#cal-start,#cal-import";
const titles = {
  overview: "Landing overview",
  camera: "Camera & mount",
  calibration: "Camera calibration",
  board: "Landing board",
  connection: "MAVLink connection",
  diagnostics: "Diagnostics",
};
function notice(message, good = false) {
  $("notice").textContent = message;
  $("notice").className = good ? "ok" : "";
  $("notice").hidden = false;
}
async function api(path, method = "GET", body) {
  const response = await fetch("api/" + path, {
    method,
    headers: { "Content-Type": "application/json", "X-Wingxtra-Request": "1" },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
    signal: method === "GET" ? AbortSignal.timeout(3000) : undefined,
  });
  if (!response.ok) {
    let error;
    try {
      error = await response.json();
    } catch {
      error = { detail: response.statusText };
    }
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : JSON.stringify(error.detail),
    );
  }
  return response.json();
}
async function action(task) {
  try {
    await task();
  } catch (error) {
    notice(error.message);
  }
}
function text(id, value) {
  $(id).textContent = value;
}
function num(id) {
  return Number($(id).value);
}
function chooseTab(tab) {
  if (!titles[tab]) tab = "overview";
  activeTab = tab;
  document
    .querySelectorAll(".tab")
    .forEach((s) => s.classList.toggle("active", s.id === tab));
  document
    .querySelectorAll("nav button")
    .forEach((b) => b.classList.toggle("selected", b.dataset.tab === tab));
  text("page-title", titles[tab]);
}
document.querySelectorAll("nav button").forEach((b) =>
  b.addEventListener("click", () => {
    location.hash = b.dataset.tab;
    chooseTab(b.dataset.tab);
  }),
);
window.addEventListener("hashchange", () => chooseTab(location.hash.slice(1)));
chooseTab(location.hash.slice(1));
function populateProfileChoices() {
  const select = $("camera-profile");
  select.replaceChildren();
  for (const [id, profile] of Object.entries(cameraProfiles)) {
    const option = document.createElement("option");
    option.value = id;
    option.textContent = profile.label;
    select.append(option);
  }
}
function toggleGimbalFields() {
  $("gimbal-fields").hidden = $("camera-mode").value !== "gimbal";
}
function applyCameraProfile() {
  const id = $("camera-profile").value;
  const profile = cameraProfiles[id];
  if (!profile || id === "custom") return;
  for (const [field, key] of [
    ["camera-kind", "kind"],
    ["camera-source", "source"],
    ["camera-id", "camera_id"],
    ["camera-lens", "lens_profile"],
    ["camera-width", "width"],
    ["camera-height", "height"],
    ["camera-fps", "fps"],
  ])
    if (profile[key] !== undefined) $(field).value = profile[key];
  $("camera-mode").value = profile.recommended_mode || "gimbal";
  toggleGimbalFields();
  notice(
    "Profile defaults applied. Calibrate and bench-test this exact stream before publishing.",
  );
}
$("camera-profile").addEventListener("change", applyCameraProfile);
$("camera-mode").addEventListener("change", toggleGimbalFields);
function populate() {
  const c = config.camera,
    g = config.gimbal,
    o = config.output;
  for (const [id, value] of Object.entries({
    "camera-profile": c.profile,
    "camera-mode": c.mode,
    "camera-kind": c.kind,
    "camera-source": c.source,
    "camera-id": c.camera_id,
    "camera-lens": c.lens_profile,
    "camera-width": c.width,
    "camera-height": c.height,
    "camera-fps": c.fps,
    "gimbal-component": g.component_id,
    "gimbal-device": g.device_id,
    "gimbal-timeout": g.status_timeout_s,
    "gimbal-skew": g.max_sample_skew_s,
    "gimbal-down-error": g.max_downward_error_deg,
    "output-mode": o.mode,
    "listen-host": o.listen_host,
    "listen-port": o.listen_port,
    "peer-host": o.peer_host,
    "target-system": o.target_system,
    "source-component": o.source_component,
    "send-hz": o.send_hz,
    "heartbeat-timeout": o.heartbeat_timeout_s,
    "databus-host": o.databus_host,
    "databus-port": o.databus_port,
    "databus-key": o.databus_module_key,
    "startup-mode": config.startup_mode,
  }))
    $(id).value = value;
  $("mount-matrix").value = JSON.stringify(
    config.mount.camera_to_body,
    null,
    2,
  );
  $("camera-to-gimbal").value = JSON.stringify(g.camera_to_gimbal, null, 2);
  $("quality-json").value = JSON.stringify(config.quality, null, 2);
  toggleGimbalFields();
}
async function saveConfig(next) {
  config = await api("config", "PUT", next);
  populate();
  notice("Settings saved. Start preview when ready.", true);
  await refresh();
}
$("camera-form").addEventListener("submit", (event) => {
  event.preventDefault();
  action(async () => {
    const next = structuredClone(config);
    next.camera = {
      profile: $("camera-profile").value,
      mode: $("camera-mode").value,
      kind: $("camera-kind").value,
      source: $("camera-source").value,
      camera_id: $("camera-id").value,
      lens_profile: $("camera-lens").value,
      width: num("camera-width"),
      height: num("camera-height"),
      fps: num("camera-fps"),
    };
    next.mount.camera_to_body = JSON.parse($("mount-matrix").value);
    next.gimbal = {
      camera_to_gimbal: JSON.parse($("camera-to-gimbal").value),
      component_id: num("gimbal-component"),
      device_id: num("gimbal-device"),
      status_timeout_s: num("gimbal-timeout"),
      max_sample_skew_s: num("gimbal-skew"),
      max_downward_error_deg: num("gimbal-down-error"),
    };
    await saveConfig(next);
  });
});
$("connection-form").addEventListener("submit", (event) => {
  event.preventDefault();
  action(async () => {
    const next = structuredClone(config);
    Object.assign(next.output, {
      mode: $("output-mode").value,
      listen_host: $("listen-host").value,
      listen_port: num("listen-port"),
      peer_host: $("peer-host").value,
      target_system: num("target-system"),
      source_component: num("source-component"),
      send_hz: num("send-hz"),
      heartbeat_timeout_s: num("heartbeat-timeout"),
      databus_host: $("databus-host").value,
      databus_port: num("databus-port"),
      databus_module_key: $("databus-key").value,
    });
    next.startup_mode = $("startup-mode").value;
    next.quality = JSON.parse($("quality-json").value);
    await saveConfig(next);
  });
});
for (const [id, mode] of [
  ["preview-button", "monitor"],
  ["publish-button", "publish"],
  ["stop-button", "stopped"],
])
  $(id).addEventListener("click", () =>
    action(async () => {
      await api("control", "POST", { mode });
      notice(
        mode === "publish"
          ? "Output enabled. Sending requires a fresh accepted target and autopilot heartbeat."
          : mode === "monitor"
            ? "Preview enabled. MAVLink target output is off."
            : "Output and camera stopped.",
        true,
      );
      await refresh();
    }),
  );
function calSetup() {
  return {
    columns: num("cal-columns"),
    rows: num("cal-rows"),
    square_m: num("cal-square") / 1000,
  };
}
$("chessboard-download").addEventListener("click", () => {
  $("chessboard-download").href =
    `api/chessboard.svg?columns=${num("cal-columns")}&rows=${num("cal-rows")}&square_mm=${num("cal-square")}`;
});
for (const [id, command] of [
  ["cal-start", "start"],
  ["cal-capture", "capture"],
  ["cal-solve", "solve"],
  ["cal-cancel", "cancel"],
])
  $(id).addEventListener("click", () =>
    action(async () => {
      const button = $(id);
      if (pendingCalibration.has(id)) return;
      pendingCalibration.add(id);
      button.disabled = true;
      try {
        const result = await api(
          "calibration/" + command,
          "POST",
          command === "start" ? calSetup() : {},
        );
        notice(
          command === "solve"
            ? `Calibration saved. RMS ${result.rms_px.toFixed(3)} px. Verify physical distance before enabling output.`
            : command === "capture"
              ? `View captured (${result.views} total). Move or tilt the board for the next view.`
              : command === "cancel"
                ? "Calibration session cancelled."
                : "Calibration session started. Camera preview is on.",
          true,
        );
        await refresh();
      } finally {
        pendingCalibration.delete(id);
        await refresh();
      }
    }),
  );
async function importFile(input) {
  const file = input.files[0];
  if (!file) return;
  if (file.size > 1000000) throw new Error("File exceeds 1 MB");
  return JSON.parse(await file.text());
}
$("cal-import").addEventListener("change", () =>
  action(async () => {
    const data = await importFile($("cal-import"));
    if (data) {
      await api("calibration", "PUT", data);
      notice("Calibration restored.", true);
      await refresh();
    }
  }),
);
$("board-import").addEventListener("change", () =>
  action(async () => {
    const data = await importFile($("board-import"));
    if (data) $("board-json").value = JSON.stringify(data, null, 2);
  }),
);
$("board-save").addEventListener("click", () =>
  action(async () => {
    const data = JSON.parse($("board-json").value);
    await api("board", "PUT", data);
    board = data;
    $("board-preview").src = "api/board.svg?t=" + Date.now();
    notice(
      "Board validated and saved. Check printed dimensions before use.",
      true,
    );
    await refresh();
  }),
);
async function refresh() {
  const s = await api("status");
  lastStatus = s;
  lastStatusAt = performance.now();
  const m = s.measurement;
  const fresh = m && m.current_age_ms <= config.quality.max_frame_age_s * 1000;
  const valid = fresh && m.accepted && s.camera.connected && s.engine_alive;
  text(
    "mode",
    s.dry_run
      ? "Dry run"
      : s.mode === "publish"
        ? "Output enabled"
        : s.mode === "monitor"
          ? "Preview only"
          : "Stopped",
  );
  $("mode").classList.toggle("live", s.mode === "publish");
  text("version", "v" + s.version);
  text("camera-state", s.camera.connected ? "Connected" : "Offline");
  text(
    "camera-detail",
    s.camera.error ||
      (s.camera.connected
        ? `${s.camera.width} × ${s.camera.height} · ${s.camera.mode}`
        : "Start preview to connect"),
  );
  text("cal-state", s.calibration.valid ? "Calibrated" : "Required");
  text(
    "cal-detail",
    s.calibration.valid
      ? `${s.calibration.rms_px.toFixed(3)} px RMS · ${s.calibration.views} views`
      : "Calibrate the installed camera",
  );
  text("fc-state", s.connection.connected ? "Connected" : "Waiting");
  text(
    "fc-detail",
    s.connection.connected
      ? s.connection.armed
        ? "Aircraft armed"
        : "Aircraft disarmed"
      : "No fresh autopilot heartbeat",
  );
  text("packet-count", s.sent_count);
  text(
    "frame-age",
    s.camera.age_ms !== null ? `${Math.round(s.camera.age_ms)} MS` : "NO FRAME",
  );
  text(
    "target-reason",
    s.error ||
      (s.mode === "stopped"
        ? "Output is stopped"
        : m
          ? m.reason
          : s.tracking_reason),
  );
  text(
    "tag-ids",
    fresh && m.used_ids.length
      ? "IDs " + m.used_ids.join(", ")
      : "No accepted tags",
  );
  ["x", "y", "z"].forEach((axis, i) =>
    text(
      "position-" + axis,
      valid && m.body_frd_m ? m.body_frd_m[i].toFixed(3) : "—",
    ),
  );
  text(
    "distance",
    valid && m.distance_m !== null ? m.distance_m.toFixed(3) + " m" : "—",
  );
  text(
    "reprojection",
    fresh && m.reprojection_px !== null
      ? m.reprojection_px.toFixed(2) + " px"
      : "—",
  );
  $("publish-button").disabled =
    s.dry_run ||
    !s.calibration.valid ||
    Boolean(s.calibration.session) ||
    s.mode === "publish";
  if (!s.camera.connected) {
    for (const [image, empty] of [
      ["preview", "preview-empty"],
      ["cal-preview", "cal-preview-empty"],
    ]) {
      $(image).hidden = true;
      $(empty).hidden = false;
    }
  }
  const session = s.calibration.session;
  text("cal-views", session?.views ?? 0);
  $("cal-progress").value = session?.views ?? 0;
  text("cal-cells", `${session?.coverage_cells ?? 0} / 4`);
  text("cal-scale", `${session?.scale_ratio ?? 0} / 1.5`);
  text("cal-tilts", `${session?.tilted_views ?? 0} / 3`);
  text(
    "cal-guidance",
    session?.guidance ?? "Start a session to capture calibration views.",
  );
  const locked = Boolean(s.setup_lock_reason);
  $("cal-capture").disabled =
    locked || pendingCalibration.has("cal-capture") || !session;
  $("cal-solve").disabled =
    locked || pendingCalibration.has("cal-solve") || !session?.ready;
  $("cal-cancel").disabled =
    locked || pendingCalibration.has("cal-cancel") || !session;
  text(
    "board-detail",
    `${s.board.tags} tags · tag36h11 · IDs ${s.board.ids.join(", ")}`,
  );
  const diagnostics = { ...s };
  delete diagnostics.events;
  text("diagnostic-json", JSON.stringify(diagnostics, null, 2));
  document
    .querySelectorAll(setupFields)
    .forEach((el) => (el.disabled = locked || pendingCalibration.has(el.id)));
}
for (const [image, empty] of [
  ["preview", "preview-empty"],
  ["cal-preview", "cal-preview-empty"],
]) {
  $(image).addEventListener("load", () => {
    previewBusy[image] = false;
    if (lastStatus?.camera.connected) {
      $(image).hidden = false;
      $(empty).hidden = true;
    }
  });
  $(image).addEventListener("error", () => {
    previewBusy[image] = false;
    $(image).hidden = true;
    $(empty).hidden = false;
  });
}
setInterval(() => {
  if (lastStatus && performance.now() - lastStatusAt > 1500) disconnected();
  const image =
    activeTab === "overview"
      ? "preview"
      : activeTab === "calibration"
        ? "cal-preview"
        : null;
  if (image && lastStatus?.camera.connected && !previewBusy[image]) {
    previewBusy[image] = true;
    $(image).src = "api/preview.jpg?t=" + Date.now();
  }
}, 250);
function disconnected() {
  lastStatus = undefined;
  text("mode", "Disconnected");
  $("mode").classList.remove("live");
  $("publish-button").disabled = true;
  for (const image of ["preview", "cal-preview"]) {
    $(image).hidden = true;
    $(image + "-empty").hidden = false;
  }
  for (const id of [
    "position-x",
    "position-y",
    "position-z",
    "distance",
    "reprojection",
    "packet-count",
  ])
    text(id, "—");
  text("camera-state", "Unknown");
  text("camera-detail", "Extension disconnected");
  text("fc-state", "Unknown");
  text("fc-detail", "No current telemetry");
  text("frame-age", "NO STATUS");
  text("tag-ids", "No current tags");
  text("target-reason", "Extension disconnected; measurements unavailable");
  document
    .querySelectorAll(setupFields + ",#cal-capture,#cal-solve,#cal-cancel")
    .forEach((el) => (el.disabled = true));
}
async function poll() {
  try {
    await refresh();
  } catch (error) {
    disconnected();
  } finally {
    setTimeout(poll, 700);
  }
}
action(async () => {
  [config, board, cameraProfiles] = await Promise.all([
    api("config"),
    api("board"),
    api("camera-profiles"),
  ]);
  populateProfileChoices();
  populate();
  $("board-json").value = JSON.stringify(board, null, 2);
  poll();
});
