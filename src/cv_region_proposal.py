from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Iterable
from typing import Literal
from typing import TypedDict

import cv2
import numpy as np


@dataclass
class Box:
    x1: int
    y1: int
    x2: int
    y2: int
    score: float
    # scoring breakdown (useful for reporting/debug)
    score_color: float = 0.0
    score_shape: float = 0.0
    score_edge: float = 0.0


@dataclass(frozen=True)
class DetectorConfig:
    # --- Ch.2: illumination + denoise ---
    gamma: float | None = 0.85
    clahe_clip_limit: float | None = 2.0
    clahe_grid_size: int = 8
    denoise: Literal["none", "median", "gaussian"] = "median"
    denoise_ksize: int = 3

    # --- Ch.2 + Ch.4: color thresholding (HSV) ---
    red_1: tuple[int, int, int] = (0, 70, 50)
    red_2: tuple[int, int, int] = (10, 255, 255)
    red_3: tuple[int, int, int] = (170, 70, 50)
    red_4: tuple[int, int, int] = (180, 255, 255)
    blue_1: tuple[int, int, int] = (90, 60, 50)
    blue_2: tuple[int, int, int] = (130, 255, 255)
    yellow_1: tuple[int, int, int] = (15, 70, 50)
    yellow_2: tuple[int, int, int] = (35, 255, 255)

    morph_kernel: int = 3
    morph_open_iter: int = 1
    morph_close_iter: int = 2

    # --- Ch.3: edges + shape priors ---
    canny_low: int = 80
    canny_high: int = 160
    edge_dilate_iter: int = 1

    polygon_eps_ratio: float = 0.03
    use_hough_circle: bool = True
    use_hough_lines: bool = True
    hough_max_dim: int = 720
    hough_dp: float = 1.2
    hough_param1: float = 120
    hough_param2: float = 28
    hough_min_radius: int = 8
    hough_max_radius: int = 0

    hough_lines_rho: float = 1.0
    hough_lines_theta_deg: float = 1.0
    hough_lines_threshold: int = 60
    hough_lines_min_line_length: int = 25
    hough_lines_max_line_gap: int = 8

    # --- Filtering + scoring ---
    min_area_ratio: float = 0.0001
    min_area_abs: int = 50
    min_side: int = 12
    aspect_min: float = 0.4
    aspect_max: float = 1.8
    nms_iou: float = 0.35

    # Expand boxes (useful when the contour captures only the sign interior but GT includes border/background)
    bbox_pad_ratio: float = 0.25

    # scoring weights (keep simple + reportable)
    w_color: float = 0.45
    w_shape: float = 0.35
    w_edge: float = 0.20

    # thresholds
    min_color_ratio: float = 0.05
    min_circularity: float = 0.15
    min_fill: float = 0.12
    min_solidity: float = 0.0


class DebugOutputs(TypedDict, total=False):
    preprocessed: np.ndarray
    mask_color: np.ndarray
    edges: np.ndarray
    combined: np.ndarray
    overlay_shapes: np.ndarray
    overlay: np.ndarray


def _downscale_for_hough(gray: np.ndarray, max_dim: int) -> tuple[np.ndarray, float]:
    """Return (resized_gray, scale) where scale maps resized -> original."""
    h, w = gray.shape[:2]
    if max_dim <= 0:
        return gray, 1.0
    m = max(h, w)
    if m <= max_dim:
        return gray, 1.0
    scale = m / float(max_dim)
    new_w = max(1, int(round(w / scale)))
    new_h = max(1, int(round(h / scale)))
    resized = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale


def _apply_gamma(image_bgr: np.ndarray, gamma: float) -> np.ndarray:
    if gamma <= 0:
        return image_bgr
    inv = 1.0 / gamma
    table = (np.power(np.arange(256, dtype=np.float32) / 255.0, inv) * 255.0).clip(0, 255).astype(np.uint8)
    return cv2.LUT(image_bgr, table)


def _apply_clahe(image_bgr: np.ndarray, clip_limit: float, grid_size: int) -> np.ndarray:
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=float(clip_limit), tileGridSize=(int(grid_size), int(grid_size)))
    l2 = clahe.apply(l)
    merged = cv2.merge((l2, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def _apply_denoise(image_bgr: np.ndarray, mode: str, ksize: int) -> np.ndarray:
    ksize = int(ksize)
    if ksize <= 1:
        return image_bgr
    if mode == "median":
        return cv2.medianBlur(image_bgr, ksize if ksize % 2 == 1 else ksize + 1)
    if mode == "gaussian":
        k = ksize if ksize % 2 == 1 else ksize + 1
        return cv2.GaussianBlur(image_bgr, (k, k), 0)
    return image_bgr


def _iou(a: Box, b: Box) -> float:
    inter_x1 = max(a.x1, b.x1)
    inter_y1 = max(a.y1, b.y1)
    inter_x2 = min(a.x2, b.x2)
    inter_y2 = min(a.y2, b.y2)

    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = max(0, a.x2 - a.x1) * max(0, a.y2 - a.y1)
    area_b = max(0, b.x2 - b.x1) * max(0, b.y2 - b.y1)
    union = area_a + area_b - inter_area
    return inter_area / union if union > 0 else 0.0


def _nms(boxes: Iterable[Box], threshold: float = 0.4) -> list[Box]:
    ordered = sorted(boxes, key=lambda b: b.score, reverse=True)
    kept: list[Box] = []

    while ordered:
        current = ordered.pop(0)
        kept.append(current)
        ordered = [b for b in ordered if _iou(current, b) < threshold]

    return kept


def propose_regions(
    image: np.ndarray,
    config: DetectorConfig | None = None,
    *,
    return_debug: bool = False,
) -> list[Box] | tuple[list[Box], DebugOutputs]:
    """Classical CV region proposal for traffic sign candidates.

    - Input: BGR image (OpenCV).
    - Output: list[Box] in pixel coordinates + heuristic score.
    - Designed for detect(1-class) → crop → classify(43+bg) pipeline.
    """

    cfg = config or DetectorConfig()

    work = image
    if cfg.gamma is not None:
        work = _apply_gamma(work, float(cfg.gamma))
    if cfg.clahe_clip_limit is not None:
        work = _apply_clahe(work, float(cfg.clahe_clip_limit), int(cfg.clahe_grid_size))
    work = _apply_denoise(work, cfg.denoise, int(cfg.denoise_ksize))

    hsv = cv2.cvtColor(work, cv2.COLOR_BGR2HSV)
    lower_red_1 = np.array(cfg.red_1, dtype=np.uint8)
    upper_red_1 = np.array(cfg.red_2, dtype=np.uint8)
    lower_red_2 = np.array(cfg.red_3, dtype=np.uint8)
    upper_red_2 = np.array(cfg.red_4, dtype=np.uint8)
    mask_red = cv2.inRange(hsv, lower_red_1, upper_red_1) | cv2.inRange(hsv, lower_red_2, upper_red_2)

    lower_blue = np.array(cfg.blue_1, dtype=np.uint8)
    upper_blue = np.array(cfg.blue_2, dtype=np.uint8)
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    lower_yellow = np.array(cfg.yellow_1, dtype=np.uint8)
    upper_yellow = np.array(cfg.yellow_2, dtype=np.uint8)
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

    kernel = np.ones((int(cfg.morph_kernel), int(cfg.morph_kernel)), np.uint8)

    # Apply morphology per-color to avoid connecting adjacent objects of different colors.
    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel, iterations=int(cfg.morph_open_iter))
    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_CLOSE, kernel, iterations=int(cfg.morph_close_iter))
    mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_OPEN, kernel, iterations=int(cfg.morph_open_iter))
    mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_CLOSE, kernel, iterations=int(cfg.morph_close_iter))
    mask_yellow = cv2.morphologyEx(mask_yellow, cv2.MORPH_OPEN, kernel, iterations=int(cfg.morph_open_iter))
    mask_yellow = cv2.morphologyEx(mask_yellow, cv2.MORPH_CLOSE, kernel, iterations=int(cfg.morph_close_iter))

    mask_color = cv2.bitwise_or(cv2.bitwise_or(mask_red, mask_blue), mask_yellow)

    gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, int(cfg.canny_low), int(cfg.canny_high))
    if cfg.edge_dilate_iter > 0:
        edges = cv2.dilate(edges, kernel, iterations=int(cfg.edge_dilate_iter))

    combined = cv2.bitwise_or(mask_color, edges)

    # Find contours per-color to avoid different-color adjacency merging (e.g., yellow sign touching a blue billboard).
    contours = []
    for _mask in (mask_red, mask_blue, mask_yellow):
        cs, _ = cv2.findContours(_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours.extend(cs)

    height, width = image.shape[:2]
    min_area = max(int(cfg.min_area_abs), int(cfg.min_area_ratio * width * height))

    # Optional Hough circle prior (Ch.3). We use it as a weak signal.
    circles = None
    if cfg.use_hough_circle:
        hough_gray, scale = _downscale_for_hough(gray, int(cfg.hough_max_dim))
        circles = cv2.HoughCircles(
            hough_gray,
            cv2.HOUGH_GRADIENT,
            dp=float(cfg.hough_dp),
            minDist=max(20, min(hough_gray.shape[:2]) // 20),
            param1=float(cfg.hough_param1),
            param2=float(cfg.hough_param2),
            minRadius=int(cfg.hough_min_radius),
            maxRadius=int(cfg.hough_max_radius),
        )
        if circles is not None and circles.size:
            circles = np.round(circles[0, :, :]).astype(int)
            if scale != 1.0:
                circles[:, 0:2] = np.round(circles[:, 0:2] * scale).astype(int)
                circles[:, 2] = np.round(circles[:, 2] * scale).astype(int)
        else:
            circles = None

    # Optional Hough line prior (Ch.3). Again, weak signal.
    lines = None
    if cfg.use_hough_lines:
        hough_edges, scale = _downscale_for_hough(edges, int(cfg.hough_max_dim))
        theta = float(cfg.hough_lines_theta_deg) * np.pi / 180.0
        raw_lines = cv2.HoughLinesP(
            hough_edges,
            rho=float(cfg.hough_lines_rho),
            theta=theta,
            threshold=int(cfg.hough_lines_threshold),
            minLineLength=int(cfg.hough_lines_min_line_length),
            maxLineGap=int(cfg.hough_lines_max_line_gap),
        )
        if raw_lines is not None and raw_lines.size:
            lines = raw_lines.reshape(-1, 4).astype(int)
            if scale != 1.0:
                lines = np.round(lines * scale).astype(int)
        else:
            lines = None

    boxes: list[Box] = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        if w < int(cfg.min_side) or h < int(cfg.min_side):
            continue

        aspect = w / float(h)
        if aspect < float(cfg.aspect_min) or aspect > float(cfg.aspect_max):
            continue

        # Pad bbox after basic geometry filtering.
        pad = int(round(float(cfg.bbox_pad_ratio) * max(w, h)))
        if pad > 0:
            x1p = max(0, x - pad)
            y1p = max(0, y - pad)
            x2p = min(width, x + w + pad)
            y2p = min(height, y + h + pad)
            x, y, w, h = x1p, y1p, max(1, x2p - x1p), max(1, y2p - y1p)

        perimeter = cv2.arcLength(contour, True)
        if perimeter <= 0:
            continue

        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = float(area / hull_area) if hull_area > 0 else 0.0

        circularity = float(4.0 * np.pi * area / (perimeter * perimeter))
        fill = float(area / float(w * h))
        if (
            circularity < float(cfg.min_circularity)
            or fill < float(cfg.min_fill)
            or solidity < float(cfg.min_solidity)
        ):
            continue

        x1, y1, x2, y2 = int(x), int(y), int(x + w), int(y + h)
        x1 = max(0, min(width - 1, x1))
        y1 = max(0, min(height - 1, y1))
        x2 = max(0, min(width, x2))
        y2 = max(0, min(height, y2))
        if x2 <= x1 or y2 <= y1:
            continue

        roi_mask = mask_color[y1:y2, x1:x2]
        roi_edges = edges[y1:y2, x1:x2]
        box_area = float((x2 - x1) * (y2 - y1))
        color_ratio = float(np.count_nonzero(roi_mask)) / box_area if box_area > 0 else 0.0
        if color_ratio < float(cfg.min_color_ratio):
            continue

        edge_density = float(np.count_nonzero(roi_edges)) / box_area if box_area > 0 else 0.0

        # Polygon approximation (Ch.3 shape prior)
        eps = float(cfg.polygon_eps_ratio) * perimeter
        approx = cv2.approxPolyDP(contour, eps, True)
        vertices = int(len(approx))
        shape_score = 0.0
        if 3 <= vertices <= 5:
            shape_score = 0.75
        elif 6 <= vertices <= 10:
            shape_score = 0.55

        # Hough circle prior: boost if any circle center falls inside bbox.
        if circles is not None:
            for cx, cy, _r in circles:
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    shape_score = max(shape_score, 0.9)
                    break

        # Hough line prior: boost if multiple line midpoints fall inside bbox.
        if lines is not None:
            inside = 0
            for x3, y3, x4, y4 in lines:
                mx = (x3 + x4) // 2
                my = (y3 + y4) // 2
                if x1 <= mx <= x2 and y1 <= my <= y2:
                    inside += 1
                    if inside >= 2:
                        shape_score = max(shape_score, 0.8)
                        break

        score = (
            float(cfg.w_color) * color_ratio
            + float(cfg.w_shape) * shape_score
            + float(cfg.w_edge) * edge_density
        )
        score = float(np.clip(score, 0.0, 1.0))

        boxes.append(
            Box(
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                score=score,
                score_color=float(color_ratio),
                score_shape=float(shape_score),
                score_edge=float(edge_density),
            )
        )

    kept = _nms(boxes, threshold=float(cfg.nms_iou))

    if not return_debug:
        return kept

    overlay_shapes = image.copy()
    cv2.drawContours(overlay_shapes, contours, -1, (255, 0, 0), 1)
    if circles is not None:
        for cx, cy, r in circles:
            cv2.circle(overlay_shapes, (int(cx), int(cy)), int(r), (0, 255, 255), 1)
    if lines is not None:
        for x3, y3, x4, y4 in lines:
            cv2.line(overlay_shapes, (int(x3), int(y3)), (int(x4), int(y4)), (0, 255, 255), 1)

    overlay = image.copy()
    for b in kept:
        cv2.rectangle(overlay, (b.x1, b.y1), (b.x2, b.y2), (0, 255, 0), 2)
        cv2.putText(
            overlay,
            f"{b.score:.2f}",
            (b.x1, max(15, b.y1 - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )

    debug: DebugOutputs = {
        "preprocessed": work,
        "mask_color": mask_color,
        "edges": edges,
        "combined": combined,
        "overlay_shapes": overlay_shapes,
        "overlay": overlay,
    }
    return kept, debug
