from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Literal
from typing import TypedDict

import cv2
import numpy as np

from cv_region_proposal import Box
from cv_region_proposal import DetectorConfig
from cv_region_proposal import propose_regions


class ClassicalDetectorOutput(TypedDict, total=False):
    bboxes: list[list[int]]
    scores: list[float]
    debug: dict[str, Any]


@dataclass(frozen=True)
class ClassicalDetectorParams:
    proposal: DetectorConfig = DetectorConfig()
    det_threshold: float = 0.25


def _coerce_tuple3(value: Any) -> tuple[int, int, int]:
    if isinstance(value, tuple) and len(value) == 3:
        return tuple(int(x) for x in value)  # type: ignore[return-value]
    if isinstance(value, list) and len(value) == 3:
        return (int(value[0]), int(value[1]), int(value[2]))
    raise ValueError(f"Expected 3-int list/tuple, got: {value!r}")


def load_params(path: str | Path) -> ClassicalDetectorParams:
    """Load detector parameters from a JSON file.

    The JSON keys match fields of `DetectorConfig` plus an extra `det_threshold`.
    """

    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Config JSON must be an object")

    det_threshold = float(raw.pop("det_threshold", 0.25))

    # Convert list -> tuple for HSV thresholds.
    for key in (
        "red_1",
        "red_2",
        "red_3",
        "red_4",
        "blue_1",
        "blue_2",
        "yellow_1",
        "yellow_2",
    ):
        if key in raw:
            raw[key] = _coerce_tuple3(raw[key])

    proposal = DetectorConfig(**raw)
    return ClassicalDetectorParams(proposal=proposal, det_threshold=det_threshold)


def _clip_xyxy(x1: int, y1: int, x2: int, y2: int, w: int, h: int) -> tuple[int, int, int, int]:
    x1 = max(0, min(w - 1, int(x1)))
    y1 = max(0, min(h - 1, int(y1)))
    x2 = max(0, min(w, int(x2)))
    y2 = max(0, min(h, int(y2)))
    if x2 <= x1:
        x2 = min(w, x1 + 1)
    if y2 <= y1:
        y2 = min(h, y1 + 1)
    return x1, y1, x2, y2


def detect_classical(
    image_rgb: np.ndarray,
    params: ClassicalDetectorParams | None = None,
    *,
    return_debug: bool = False,
    min_side: int = 12,
) -> ClassicalDetectorOutput:
    """Classical traffic sign candidate detector (image-only).

    Contract (for integration):
    - Input: RGB image, any size.
    - Output:
      - `bboxes`: list of pixel boxes [x1,y1,x2,y2] (int) on original image.
      - `scores`: list of floats in [0,1] (rule-based).
      - `debug`: optional debug images (BGR) when return_debug=True.

    Notes:
    - Bboxes are clipped to image bounds.
    - Very small boxes (< min_side x min_side) are filtered out.
    - Internally uses `src/cv_region_proposal.py` (Ch.2–Ch.4 pipeline).
    """

    if image_rgb.ndim != 3 or image_rgb.shape[2] != 3:
        raise ValueError("image_rgb must be HxWx3")

    cfg = params or ClassicalDetectorParams()

    # OpenCV works in BGR.
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

    if return_debug:
        boxes, dbg = propose_regions(image_bgr, cfg.proposal, return_debug=True)
    else:
        boxes = propose_regions(image_bgr, cfg.proposal, return_debug=False)
        dbg = None

    h, w = image_bgr.shape[:2]

    # Apply a final threshold here (keeps `propose_regions` reusable).
    filtered: list[Box] = [b for b in boxes if float(b.score) >= float(cfg.det_threshold)]

    bboxes: list[list[int]] = []
    scores: list[float] = []
    for b in filtered:
        x1, y1, x2, y2 = _clip_xyxy(b.x1, b.y1, b.x2, b.y2, w, h)
        if (x2 - x1) < int(min_side) or (y2 - y1) < int(min_side):
            continue
        bboxes.append([int(x1), int(y1), int(x2), int(y2)])
        scores.append(float(np.clip(b.score, 0.0, 1.0)))

    out: ClassicalDetectorOutput = {"bboxes": bboxes, "scores": scores}
    if return_debug and dbg is not None:
        out["debug"] = {
            # these are BGR arrays (OpenCV) for convenient saving
            "preprocessed": dbg.get("preprocessed"),
            "mask_color": dbg.get("mask_color"),
            "edges": dbg.get("edges"),
            "combined": dbg.get("combined"),
            "overlay_shapes": dbg.get("overlay_shapes"),
            "overlay": dbg.get("overlay"),
        }

    return out
