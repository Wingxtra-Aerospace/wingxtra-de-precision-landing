"use strict";
const $ = (id) => document.getElementById(id);
let config,
  board,
  lastStatus,
  previewBusy = { preview: false, "cal-preview": false },
  activeTab = "overview";
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
function populate() {
  const c = config.camera,
    o = config.output;
  for (const [id, value] of Object.entries({
    "camera-kind": c.kind,
    "camera-source": c.source,
    "camera-id": c.camera_id,
    "camera-lens": c.lens_profile,
    "camera-width": c.width,
    "camera-height": c.height,
    "camera-fps": c.fps,
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
  $("quality-json").value = JSON.stringify(config.quality, null, 2);
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
      kind: $("camera-kind").value,
      source: $("camera-source").value,
      camera_id: $("camera-id").value,
      lens_profile: $("camera-lens").value,
      width: num("camera-width"),
      height: num("camera-height"),
      fps: num("camera-fps"),
    };
    next.mount.camera_to_body = JSON.parse($("mount-matrix").value);
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
        button.disabled = false;
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
  const m = s.measurement;
  const fresh = m && m.current_age_ms <= config.quality.max_frame_age_s * 1000;
  const valid = fresh && m.accepted;
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
        ? `${s.camera.width} × ${s.camera.height}`
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
  $("cal-capture").disabled = !session;
  $("cal-solve").disabled = !session?.ready;
  $("cal-cancel").disabled = !session;
  text(
    "board-detail",
    `${s.board.tags} tags · tag36h11 · IDs ${s.board.ids.join(", ")}`,
  );
  const diagnostics = { ...s };
  delete diagnostics.events;
  text("diagnostic-json", JSON.stringify(diagnostics, null, 2));
  const locked = s.mode === "publish" || s.connection.armed === true;
  document
    .querySelectorAll(
      "#camera-form input,#camera-form select,#camera-form textarea,#camera-form button,#connection-form input,#connection-form select,#connection-form textarea,#connection-form button,#board-save,#board-import,#cal-start,#cal-import",
    )
    .forEach((el) => (el.disabled = locked));
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
  });
}
setInterval(() => {
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
async function poll() {
  try {
    await refresh();
  } catch (error) {
    text("mode", "Disconnected");
    $("mode").classList.remove("live");
    $("publish-button").disabled = true;
    $("preview").hidden = true;
    $("preview-empty").hidden = false;
    $("cal-preview").hidden = true;
    $("cal-preview-empty").hidden = false;
    text("target-reason", "Extension disconnected; measurements unavailable");
  } finally {
    setTimeout(poll, 700);
  }
}
action(async () => {
  [config, board] = await Promise.all([api("config"), api("board")]);
  populate();
  $("board-json").value = JSON.stringify(board, null, 2);
  poll();
});
