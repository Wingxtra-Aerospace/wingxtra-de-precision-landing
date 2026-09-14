import copy

import numpy as np
import pytest

from wingxtra_pl.landing_target_layout import LandingTargetLayout
from wingxtra_pl.vision_multitag import DetectorConfig, MultiTagPoseEstimator
from conftest import projected_corners, render_board


def estimator(layout, k):
    return MultiTagPoseEstimator(DetectorConfig(), layout, k, np.zeros(5))


def test_real_detector_reads_multiple_tags_and_shared_origin(layout, intrinsics):
    pose = estimator(layout, intrinsics).estimate(render_board(layout, intrinsics))
    assert pose is not None
    assert set(pose["used_ids"]) == set(layout.markers)
    assert np.allclose(pose["tvec"], [0.05, -0.04, 1.4], atol=0.015)
    assert pose["reproj_rmse_px"] < 1


def test_original_ten_tag_layout_actually_detects_multiple_tags(original_layout, intrinsics):
    r, t = [np.pi - 0.08, 0.03, 0.02], [0, 0, 0.9]
    pose = estimator(original_layout, intrinsics).estimate(
        render_board(original_layout, intrinsics, r=r, t=t)
    )
    assert pose is not None
    assert len(pose["used_ids"]) >= 3
    assert np.allclose(pose["tvec"], t, atol=0.02)


def test_single_offset_tag_still_estimates_board_origin(layout, intrinsics):
    corners, ids = projected_corners(layout, intrinsics)
    pose = estimator(layout, intrinsics).estimate_corners(corners[:1], ids[:1])
    assert pose is not None
    assert pose["used_ids"] == [3]
    assert np.allclose(pose["tvec"], [0.05, -0.04, 1.4], atol=1e-5)


def test_whole_corrupt_tag_is_excluded(layout, intrinsics):
    corners, ids = projected_corners(layout, intrinsics)
    corners[-1] = corners[-1] + [70, -40]
    pose = estimator(layout, intrinsics).estimate_corners(corners, ids)
    assert pose is not None
    assert set(pose["used_ids"]) == {3, 12, 41}
    assert np.allclose(pose["tvec"], [0.05, -0.04, 1.4], atol=1e-5)


def test_conflicting_two_tags_do_not_fall_back_to_one(layout, intrinsics):
    corners, ids = projected_corners(layout, intrinsics)
    corners[1] = corners[1] + [100, 80]
    assert estimator(layout, intrinsics).estimate_corners(corners[:2], ids[:2]) is None


def test_unknown_tiny_and_duplicate_tags_are_ignored(layout, intrinsics):
    e = estimator(layout, intrinsics)
    corners, ids = projected_corners(layout, intrinsics)
    assert e.estimate_corners(corners[:1], np.array([[500]])) is None
    assert e.estimate_corners([corners[0] / 100], ids[:1]) is None
    assert e.estimate_corners(corners[:2], np.array([[3], [3]])) is None
    assert e.estimate(np.full((720, 1280, 3), 255, np.uint8)) is None


@pytest.mark.parametrize(
    "mutation", ["duplicate", "family", "nan", "units", "crossed", "nonplanar"]
)
def test_invalid_board_rejected(board_data, mutation):
    b = copy.deepcopy(board_data)
    m = b["markers"][0]
    if mutation == "duplicate":
        b["markers"].append(copy.deepcopy(m))
    if mutation == "family":
        m["family"] = "tag16h5"
    if mutation == "nan":
        m["object_points"][0][0] = float("nan")
    if mutation == "units":
        m["object_points"] = (np.array(m["object_points"]) * 1000).tolist()
    if mutation == "crossed":
        m["object_points"][1], m["object_points"][2] = m["object_points"][2], m["object_points"][1]
    if mutation == "nonplanar":
        m["object_points"][0][2] = 0.1
    with pytest.raises(ValueError):
        LandingTargetLayout.from_dict(b)
