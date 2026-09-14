# BlueOS installation and first setup

## Supported candidate deployment

Use a 64-bit BlueOS host (ARM64 Raspberry Pi 4/5 or compatible ARM64 companion; x86-64 for development) with Linux 5.1 or newer. The heartbeat receiver requires Linux kernel receive timestamps and blocks output if they are unavailable. The default container supports RTSP, HTTP MJPEG and explicitly mapped USB/V4L2 devices. It does not bundle Raspberry Pi libcamera/Picamera2, GPU acceleration or 32-bit ARM support. BlueOS 1.4 or newer provides the documented relative-path extension interface; validate the actual BlueOS release in the commissioning record.

The image is a release candidate. No aircraft receives an automatic installation, configuration change, arming command or flight-mode command.

## 1. Obtain a tested image

Open the repository's **Actions → Validate and package BlueOS extension** workflow for the exact desired commit. Require successful Python, both container jobs and manifest publication. The image is:

```
ghcr.io/wingxtra-aerospace/wingxtra-de-precision-landing:sha-<full-40-character-commit-sha>
```

The image tag is tied to that commit; do not guess a version tag. The workflow also provides `blueos-image-arm64` and `blueos-image-amd64` artifacts with Docker image archives. If GHCR access is denied, the repository owner must make the new package public or configure registry authentication; package visibility is separate from repository visibility.

An alternative is to build on the target architecture and publish to your own registry:

```bash
docker build --target test -t wingxtra-pl-test .
docker build --target final -t YOUR_REGISTRY/wingxtra-pl:1.0.0-rc.2 .
docker push YOUR_REGISTRY/wingxtra-pl:1.0.0-rc.2
```

For an offline bench machine, load the workflow's matching architecture archive with `docker load -i wingxtra-pl-arm64.tar.gz`. This gives a local `wingxtra-pl:arm64` image; it is not an automatic Bazaar listing. The extension can then be run locally with the network and volume settings below, or pushed to an accessible registry for the BlueOS manager.

## 2. Add the extension

In BlueOS **Extensions → Installed**, use the manual add option. Enter the image registry/repository and the exact commit tag. If the manager asks for permissions/settings, use the complete [blueos-permissions.json](../blueos-permissions.json).

The settings use host networking, TCP port **8077**, a persistent bind mount, a two-core CPU limit and 1 GiB memory limit. They do not request privileged mode, the Docker socket, the whole `/dev` tree or a flight-controller serial device. Allow headroom for BlueOS and video processing; adjust the deployment only after measuring load.

Persistent host directory:

```
/usr/blueos/extensions/wingxtra-precision-landing
```

The service should appear as **Wingxtra Precision Landing** in the BlueOS sidebar. Direct access is `http://<companion-ip>:8077/`. BlueOS 1.4+ can proxy it at `/extensionv2/wingxtraprecisionlanding/`. If port 8077 is already occupied, resolve that collision before installation; the image, health check and metadata consistently use that port.

The interface is intended for the trusted BlueOS vehicle network. It has no public-internet authentication service. Keep network access restricted to authorized operators; remote access should use the existing authenticated BlueOS/VPN path.

## 3. Give the camera one owner

Preferred setup: one camera service owns the device and provides a low-latency local stream. Configure this extension to consume that stream. Calibration and landing use the identical stream, resolution, fixed focus and lens settings.

- **RTSP:** set `rtsp` and the actual stream URL, e.g. `rtsp://127.0.0.1:8554/landing`. That example is not a stream automatically created by BlueOS. The container requests TCP transport and low-buffer decoding.
- **HTTP MJPEG:** set `mjpeg` and an actual continuous MJPEG stream URL. A JPEG snapshot URL is not sufficient.
- **USB:** make this extension the sole camera owner and add only the selected device mapping, e.g. `HostConfig.Devices = [{"PathOnHost":"/dev/video0","PathInContainer":"/dev/video0","CgroupPermissions":"rw"}]`. Choose `v4l2`, source `/dev/video0`. A reconnect that changes the device path needs setup correction; stable device identity is part of commissioning.
- **Raspberry Pi CSI:** use a compatible host camera/video service that exposes RTSP or MJPEG and calibrate that delivered stream. Native Picamera2 operation is documented separately. Do not select Picamera2 in the generic container or map broad host libraries into it to make an untested camera stack work.

Set the camera identity, fixed focus profile, delivered width and height in **Camera & mount**. Frames with a different resolution are rejected; the detector never silently rescales intrinsics. Preview is resized only for display.

Network image timestamps are local decode receipt times. They cannot reveal camera-side buffering, a frozen image repeatedly encoded as new frames, or hidden stream delay. Measure end-to-end exposure-to-output latency on the actual camera and verify the installed video pipeline under load.

## 4. Add the MAVLink endpoint

BlueOS must remain the only owner of the flight-controller serial/USB link. In **MAVLink Endpoints**, add a UDP **client/output** endpoint with destination **127.0.0.1:14771**. The extension listens there and replies to the source endpoint of valid incoming autopilot heartbeats. Do not configure both sides as passive UDP servers.

In this extension's **Connection** tab:

| Field | Default | Meaning |
|---|---:|---|
| Output transport | UDP | Standard MAVLink router integration |
| Listen address | 127.0.0.1 | Local host only |
| Listen port | 14771 | Dedicated extension endpoint |
| Allowed router host | 127.0.0.1 | Reject other source addresses |
| Autopilot system ID | 1 | Must equal the aircraft's MAVLink system ID |
| Extension component ID | 193 | Must be unique on that MAVLink system |
| Maximum output rate | 20 Hz | Actual rate also depends on fresh accepted images |
| Heartbeat timeout | 3 s | No target output after telemetry becomes stale |
| Restart mode | Stopped | Set publish only after commissioning |

The **Flight controller** card must show the correct connected/armed state. Confirm a bidirectional raw MAVLink path. The extension emits no GCS heartbeat, so it cannot keep a GCS failsafe artificially satisfied. Signed-only MAVLink links need the router to accept and handle this unsigned local stream appropriately; signing keys are not configured by this extension.

If DroneEngage runs on the same companion, connect it to a different BlueOS router endpoint. It must not compete for the physical serial port. Disable any other precision-landing extension or target-message generator. Prefer the UDP transport on BlueOS; the advanced [DataBus option](DATABUS_PORTS.md) is for a separately verified deployment.

## 5. Calibrate and verify the board

Start camera preview. In **Calibration**, download the chessboard, print it at 100%, attach it to a rigid flat backing, and measure a square. Enter inner-corner counts and the measured square size. Capture at least 15 different views, spanning at least four of the nine image regions, with varied distance and at least three tilted views. Click **Solve & save**.

The solver uses the actual numerical RMS returned by OpenCV. It accepts overall RMS at most 1 px and each view at most 2 px, plausible finite intrinsics and the required view diversity. A good fit does not prove correct physical scale or absence of video latency. Export `camera.json` for the aircraft record. Only this extension's matching exports are directly importable; legacy `camera.yaml` and other extensions' NPZ files require a new calibration session.

In **Landing board**, import the exact physical board's JSON. The supplied board is an example from the original repository. `object_points` in metres are authoritative; verify printed detection-corner distances with a ruler. The exported SVG is to scale, but the print dialogue must preserve that scale. Large boards may require a larger paper size. Place the board's common `(0,0,0)` origin at the desired touchdown point.

## 6. Configure ArduPilot and commission

For the supported ArduCopter companion backend, enable `PLND_ENABLED=1` and select `PLND_TYPE=1` (MAVLink). Reboot if required by the installed firmware. Verify these meanings on the actual firmware. The service sends only measurements; it does not write parameters.

The service already applies the complete camera-to-BODY_FRD rotation. Keep `PLND_YAW_ALIGN=0` and the downward/default `PLND_ORIENT=25` where that parameter is exposed by the installed firmware; an additional rotation would rotate the vector twice. Enter the physical camera lever arm in `PLND_CAM_POS_X/Y/Z`. Review the installed firmware's estimator, latency, acquisition, loss/retry and descent behavior. Verify these meanings on the exact firmware and follow [COMMISSIONING.md](COMMISSIONING.md) before operational flight or enabling publish-on-restart.

**QuadPlane:** receiving this sensor's MAVLink message does not by itself establish that landing corrections are enabled. ArduPilot's official [Plane precision-landing applet instructions](https://github.com/ArduPilot/ardupilot/blob/master/libraries/AP_Scripting/applets/plane_precland.md) describe the flight-controller-side `plane_precland.lua` integration. Follow the version-matched upstream instructions, confirm scripting/precision-landing support in the actual firmware build, and validate QLOITER/QLAND/QRTL/AUTO behavior separately. This extension does not install that applet or change flight-controller parameters.

After the first autopilot heartbeat, setup changes require a fresh disarmed heartbeat. Following an endpoint change, wait for telemetry on the new endpoint. If a wrong endpoint prevents recovery, stop work, physically verify the aircraft is disarmed on the bench, and correct persistent configuration or restart the extension there. Restart is not a way to bypass an armed-state lock during flight.

Reference: [BlueOS extension packaging and web interface](https://blueos.cloud/docs/stable/development/extensions/), [ArduPilot precision landing](https://ardupilot.org/copter/docs/precision-landing-and-loiter.html), [MAVLink landing target](https://mavlink.io/en/services/landing_target.html).
