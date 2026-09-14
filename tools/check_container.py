"""CI smoke check against a real, running container. Does not emit MAVLink."""

import json
import subprocess
import time
import urllib.error
import urllib.request

# Validate metadata from the actual running image, not just the Dockerfile text.
# BlueOS manifest Author requires both name and email:
# https://github.com/BlueRobotics/BlueOS/blob/master/core/services/kraken/manifest/models.py
inspection = json.loads(subprocess.check_output(["docker", "inspect", "landing-test"], text=True))[
    0
]
labels = inspection["Config"].get("Labels") or {}
authors = json.loads(labels.get("authors", "null"))
assert isinstance(authors, list) and authors, "BlueOS author metadata is missing"
for author in authors:
    assert isinstance(author, dict), "BlueOS authors must be JSON objects"
    for field in ("name", "email"):
        assert isinstance(author.get(field), str) and author[field].strip(), (
            f"BlueOS author metadata requires a non-empty {field}"
        )

for attempt in range(30):
    try:
        with urllib.request.urlopen("http://127.0.0.1:8077/health", timeout=1) as response:
            assert json.load(response)["alive"]
        break
    except (urllib.error.URLError, TimeoutError):
        time.sleep(1)
else:
    raise SystemExit("Container did not become healthy")

with urllib.request.urlopen("http://127.0.0.1:8077/api/status", timeout=2) as response:
    status = json.load(response)
assert status["mode"] == "stopped"
assert status["sent_count"] == 0
assert status["calibration"]["valid"] is False
with urllib.request.urlopen("http://127.0.0.1:8077/register_service", timeout=2) as response:
    assert json.load(response)["works_in_relative_paths"]
print(
    "Container metadata includes BlueOS author name/email, starts healthy, registers with BlueOS, "
    "and starts with target output disabled"
)
