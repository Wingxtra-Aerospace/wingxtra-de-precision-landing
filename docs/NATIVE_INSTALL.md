# Native Debian / Raspberry Pi installation

The BlueOS container is the primary packaged deployment. A native installation is useful when Raspberry Pi's supported Picamera2 stack must own a CSI camera directly. Do not run both the native service and the extension against the same camera or MAVLink endpoint.

Clone the candidate commit to `/opt/wingxtra-de-precision-landing`, inspect `scripts/install.sh`, then run it with sudo. It installs Debian OpenCV and a separate virtual environment, creates a `wingxtra-pl` service account with video/render group access, and installs a systemd service. It does not start target publishing. The provided NumPy constraint is for Debian Bookworm's OpenCV ABI; use the matching distribution on the native host.

For CSI, install the Raspberry Pi distribution's `python3-picamera2` package. The generic Docker image does not contain this package. Set camera kind `picamera2`, source `0` (or the actual camera index). Picamera2's RGB888 format provides the BGR byte order expected by OpenCV. The implementation disables completed-request queuing; actual driver/exposure latency still needs measurement.

Start with:

```bash
sudo systemctl start wingxtra-precision-landing
sudo journalctl -u wingxtra-precision-landing -f
```

The UI is on port 8077. Persistent data is in `/var/lib/wingxtra-precision-landing`. The service account needs access only to the camera devices and its data directory, not FC serial devices.

For development without installing a service:

```bash
python3 -m venv --system-site-packages .venv
. .venv/bin/activate
pip install -e '.[test]'
wingxtra-pl --data-dir ./data --dry-run
```

Use the same browser camera calibration and commissioning procedure as the BlueOS deployment. A Pi camera must have fixed focus and stable crop/geometry; configure lens controls in the camera service/driver before calibration. This application does not silently change focus or exposure to manufacture a test result.
