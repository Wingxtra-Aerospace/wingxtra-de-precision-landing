import cv2
import numpy as np
import pytest

from wingxtra_pl.calibration import Calibration, CalibrationSession, chessboard_svg


def test_synthetic_calibration_recovers_intrinsics_with_diverse_views(camera, intrinsics):
    session = CalibrationSession(camera)
    rng = np.random.default_rng(2026)
    for i in range(27):
        r = np.array([(-0.55, 0.2, 0.6)[i % 3], (-0.5, 0.4, 0.15)[i // 3 % 3], 0.04 * (i % 3)])
        depth = [0.55, 0.8, 1.0][i // 9]
        centre_pixel = np.array([[330, 640, 950][i % 3], [190, 360, 530][i // 3 % 3]])
        centre_obj = session.objects.mean(axis=0)
        transformed_centre = cv2.Rodrigues(r)[0] @ centre_obj
        centre_cam = np.r_[(centre_pixel - intrinsics[:2, 2]) / 850 * depth, depth]
        t = centre_cam - transformed_centre
        points = cv2.projectPoints(session.objects, r, t, intrinsics, np.zeros(5))[0]
        points += rng.normal(0, 0.08, points.shape)
        session.points.append(points.astype(np.float32))
    assert session.status()["ready"]
    calibration = session.solve()
    assert calibration.rms_px < 0.2
    assert np.array(calibration.camera_matrix)[:2, :3] == pytest.approx(intrinsics[:2, :3], abs=4)
    assert calibration.matches(camera)
    changed = camera.model_copy(update={"lens_profile": "refocused"})
    assert not calibration.matches(changed)
    assert not calibration.matches(camera.model_copy(update={"source": "rtsp://127.0.0.1/new"}))


def test_real_chessboard_capture_rejects_duplicate_and_wrong_resolution(camera):
    session = CalibrationSession(camera)
    image = np.full((720, 1280, 3), 255, np.uint8)
    square, left, top = 45, 360, 180
    for y in range(7):
        for x in range(10):
            if (x + y) % 2 == 0:
                cv2.rectangle(
                    image,
                    (left + x * square, top + y * square),
                    (left + (x + 1) * square - 1, top + (y + 1) * square - 1),
                    (0, 0, 0),
                    -1,
                )
    assert session.capture(image, 1)["views"] == 1
    with pytest.raises(ValueError, match="new camera frame"):
        session.capture(image, 1)
    with pytest.raises(ValueError, match="too similar"):
        session.capture(image, 2)
    with pytest.raises(ValueError, match="resolution"):
        session.capture(image[:500], 3)
    with pytest.raises(ValueError, match="More varied"):
        session.solve()
    assert 'width="294.0mm"' in chessboard_svg()


@pytest.mark.parametrize(
    "change",
    [
        {"rms_px": 1.5},
        {"rms_px": float("nan")},
        {"views": 10},
        {"per_view_rms_px": [0.3] * 14 + [3]},
        {"camera_matrix": [[-1, 0, 640], [0, 850, 360], [0, 0, 1]]},
        {"distortion_coefficients": [float("inf")] * 5},
    ],
)
def test_bad_calibration_is_rejected(calibration, change):
    with pytest.raises(ValueError):
        Calibration.model_validate({**calibration.model_dump(), **change})
