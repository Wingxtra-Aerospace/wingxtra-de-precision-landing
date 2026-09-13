"""CI smoke check against a real, running container. Does not emit MAVLink."""
import json
import time
import urllib.error
import urllib.request

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
print("Container starts healthy, registers with BlueOS, and starts with target output disabled")
