"""Printable board generated from authoritative detection corners, in metres."""

import cv2
import numpy as np

from .landing_target_layout import LandingTargetLayout


def board_svg(layout: LandingTargetLayout) -> str:
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
    groups, bounds = [], []
    first = next(iter(layout.markers.values())).corners_xyz
    # Display the printed face for either y-up or y-down imported board coordinates.
    # A reflection inside a marker changes its bit pattern and makes it unreadable.
    y_sign = np.sign(np.cross(first[1] - first[0], first[2] - first[1])[2])
    for mid, marker in layout.markers.items():
        corners = marker.corners_xyz[:, :2] * [1000, 1000 * y_sign]
        p, a, b = corners[0], (corners[1] - corners[0]) / 8, (corners[3] - corners[0]) / 8
        bits = (
            cv2.aruco.generateImageMarker(dictionary, mid, 8)
            if hasattr(cv2.aruco, "generateImageMarker")
            else cv2.aruco.drawMarker(dictionary, mid, 8)
        )
        transform = f"matrix({a[0]} {a[1]} {b[0]} {b[1]} {p[0]} {p[1]})"
        squares = "".join(
            f'<rect x="{x}" y="{y}" width="1" height="1"/>'
            for y in range(8)
            for x in range(8)
            if bits[y, x] == 0
        )
        groups.append(
            f'<g transform="{transform}"><rect x="-1" y="-1" width="10" '
            f'height="10" fill="white"/><g fill="black">{squares}</g></g>'
        )
        bounds.extend([p - a - b, p + 9 * a - b, p + 9 * a + 9 * b, p - a + 9 * b])
    points = np.array(bounds)
    low, high = points.min(axis=0) - 10, points.max(axis=0) + 10
    w, h = high - low
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" '
        f'viewBox="{low[0]} {low[1]} {w} {h}" shape-rendering="crispEdges">'
        f'<rect x="{low[0]}" y="{low[1]}" width="{w}" height="{h}" fill="white"/>'
        + "".join(groups)
        + "</svg>"
    )
