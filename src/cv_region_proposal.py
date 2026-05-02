from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import cv2
import numpy as np


@dataclass
class Box:
    x1: int
    y1: int
    x2: int
    y2: int
    score: float


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


def propose_regions(image: np.ndarray) -> list[Box]:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Red mask (common for prohibition/speed limit signs).
    lower_red_1 = np.array([0, 70, 50])
    upper_red_1 = np.array([10, 255, 255])
    lower_red_2 = np.array([170, 70, 50])
    upper_red_2 = np.array([180, 255, 255])
    mask_red = cv2.inRange(hsv, lower_red_1, upper_red_1) | cv2.inRange(hsv, lower_red_2, upper_red_2)

    # Blue mask (mandatory signs).
    lower_blue = np.array([90, 60, 50])
    upper_blue = np.array([130, 255, 255])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    mask = cv2.bitwise_or(mask_red, mask_blue)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    edges = cv2.Canny(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), 80, 160)
    edges = cv2.dilate(edges, kernel, iterations=1)

    combined = cv2.bitwise_or(mask, edges)

    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    height, width = image.shape[:2]
    min_area = max(50, int(0.0001 * width * height))

    boxes: list[Box] = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        if w < 8 or h < 8:
            continue

        aspect = w / float(h)
        if aspect < 0.4 or aspect > 1.8:
            continue

        perimeter = cv2.arcLength(contour, True)
        if perimeter <= 0:
            continue

        circularity = 4.0 * np.pi * area / (perimeter * perimeter)
        fill = area / float(w * h)
        score = (0.6 * circularity) + (0.4 * fill)

        boxes.append(Box(x, y, x + w, y + h, score))

    return _nms(boxes, threshold=0.35)
