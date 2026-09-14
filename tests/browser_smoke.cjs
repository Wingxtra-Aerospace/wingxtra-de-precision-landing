/* End-to-end UI checks against the local fixture, including the BlueOS URL prefix.
 * Run with playwright installed and PL_TEST_PYTHON set to the test Python interpreter.
 * Optional PL_CHROMIUM_PATH chooses an existing local browser binary.
 */
const { spawn } = require("node:child_process");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const { chromium } = require("playwright");
const prefix = "http://127.0.0.1:18077/extensionv2/wingxtraprecisionlanding/";
const server = spawn(
  process.env.PL_TEST_PYTHON || "python",
  ["tests/ui_fixture.py"],
  { stdio: ["ignore", "ignore", "pipe"] },
);
let serverError = "";
server.stderr.on("data", (chunk) => (serverError += chunk));
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
async function main() {
  let ready = false;
  for (let i = 0; i < 50; i++) {
    try {
      ready = (await fetch(prefix + "health")).ok;
    } catch {}
    if (ready) break;
    await delay(200);
  }
  assert(ready, serverError || "Fixture failed to start");
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.PL_CHROMIUM_PATH || undefined,
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  try {
    const page = await browser.newPage({
      viewport: { width: 1440, height: 1000 },
    });
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto(prefix);
    await page.locator("#camera-state").waitFor();
    await page.locator("#preview-button").click();
    await page.waitForFunction(
      () => document.getElementById("camera-state").textContent === "Connected",
    );
    await page.waitForFunction(
      () => document.getElementById("position-z").textContent !== "—",
    );
    await page.locator("#preview").waitFor({ state: "visible" });
    assert.equal(await page.locator("#packet-count").textContent(), "0");
    assert(await page.locator("#publish-button").isDisabled());
    fs.mkdirSync("test-results", { recursive: true });
    await page.screenshot({
      path: "test-results/overview-desktop.png",
      fullPage: true,
    });
    for (const tab of [
      "camera",
      "calibration",
      "board",
      "connection",
      "diagnostics",
      "overview",
    ]) {
      await page.locator(`nav [data-tab="${tab}"]`).click();
      assert(await page.locator("#" + tab).isVisible());
    }
    await page.locator('nav [data-tab="camera"]').click();
    await page.locator("#camera-fps").fill("28");
    await page
      .getByRole("button", { name: "Save camera & mount", exact: true })
      .click();
    await page.waitForFunction(() =>
      document.getElementById("notice").textContent.includes("Settings saved"),
    );
    assert.equal(
      (await (await fetch(prefix + "api/config")).json()).camera.fps,
      28,
    );
    await page.locator('nav [data-tab="calibration"]').click();
    await page.locator("#cal-start").click();
    await page.waitForFunction(
      () => !document.getElementById("cal-capture").disabled,
    );
    await page.locator("#cal-capture").click();
    await page.waitForFunction(() =>
      document
        .getElementById("notice")
        .textContent.includes("Chessboard not found"),
    );
    await page.locator("#cal-cancel").click();
    await page.waitForFunction(
      () => document.getElementById("cal-capture").disabled,
    );
    await page.setViewportSize({ width: 390, height: 844 });
    for (const tab of [
      "overview",
      "camera",
      "calibration",
      "board",
      "connection",
      "diagnostics",
    ]) {
      await page.locator(`nav [data-tab="${tab}"]`).click();
      assert(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth + 1,
        ),
        `Horizontal overflow: ${tab}`,
      );
    }
    await page.locator('nav [data-tab="calibration"]').click();
    await page.screenshot({
      path: "test-results/calibration-mobile.png",
      fullPage: true,
    });
    await page.locator('nav [data-tab="overview"]').click();
    await page.locator("#stop-button").click();
    await page.waitForFunction(
      () => document.getElementById("camera-state").textContent === "Offline",
    );
    assert.equal(
      (await (await fetch(prefix + "api/status")).json()).sent_count,
      0,
    );
    assert.deepEqual(errors, []);
    console.log(
      "Browser checks passed: prefixed routes, preview, six tabs, setup save, calibration rejection/cancel, mobile layout, stop and zero output.",
    );
  } finally {
    await browser.close();
  }
}
main()
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(() => server.kill("SIGTERM"));
