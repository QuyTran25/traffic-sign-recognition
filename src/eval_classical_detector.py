from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np

from classical_detector import detect_classical
from classical_detector import load_params


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = ROOT / "data" / "detection"
DEFAULT_CONFIG = ROOT / "configs" / "classical_detector.json"
DEFAULT_OUTDIR = ROOT / "output" / "classical_detector_eval"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate classical detector on YOLO-labeled dataset (IoU@0.5 + P/R/F1).")
    p.add_argument("--dataset", type=str, default=str(DEFAULT_DATASET), help="Dataset root containing images/ and labels/.")
    p.add_argument("--split", type=str, default="val", choices=["train", "val"], help="Split to evaluate.")
    p.add_argument("--config", type=str, default=str(DEFAULT_CONFIG), help="JSON config for detector.")
    p.add_argument("--outdir", type=str, default=str(DEFAULT_OUTDIR), help="Output directory.")
    p.add_argument("--iou", type=float, default=0.5, help="IoU threshold for a match.")
    return p.parse_args()


def yolo_line_to_xyxy(line: str, w: int, h: int) -> tuple[int, int, int, int] | None:
    parts = line.strip().split()
    if len(parts) != 5:
        return None
    try:
        _cls = int(parts[0])
        xc, yc, bw, bh = map(float, parts[1:])
    except ValueError:
        return None

    x_center = xc * w
    y_center = yc * h
    box_w = bw * w
    box_h = bh * h

    x1 = int(round(x_center - box_w / 2.0))
    y1 = int(round(y_center - box_h / 2.0))
    x2 = int(round(x_center + box_w / 2.0))
    y2 = int(round(y_center + box_h / 2.0))

    x1 = max(0, min(w - 1, x1))
    y1 = max(0, min(h - 1, y1))
    x2 = max(0, min(w, x2))
    y2 = max(0, min(h, y2))
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def read_yolo_labels(path: Path, w: int, h: int) -> list[list[int]]:
    if not path.exists():
        return []
    boxes: list[list[int]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        xyxy = yolo_line_to_xyxy(raw, w, h)
        if xyxy is None:
            continue
        boxes.append([int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])])
    return boxes


def iou_xyxy(a: list[int], b: list[int]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    iw = max(0, inter_x2 - inter_x1)
    ih = max(0, inter_y2 - inter_y1)
    inter = iw * ih

    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = area_a + area_b - inter
    return float(inter / union) if union > 0 else 0.0


def match_greedy(preds: list[list[int]], scores: list[float], gts: list[list[int]], iou_thr: float) -> tuple[int, int, int]:
    """Return (tp, fp, fn) with greedy matching by descending score."""

    order = sorted(range(len(preds)), key=lambda i: scores[i], reverse=True)
    gt_used = [False] * len(gts)

    tp = 0
    fp = 0

    for idx in order:
        p = preds[idx]
        best_iou = 0.0
        best_j = -1
        for j, gt in enumerate(gts):
            if gt_used[j]:
                continue
            v = iou_xyxy(p, gt)
            if v > best_iou:
                best_iou = v
                best_j = j

        if best_j >= 0 and best_iou >= iou_thr:
            gt_used[best_j] = True
            tp += 1
        else:
            fp += 1

    fn = int(sum(1 for used in gt_used if not used))
    return tp, fp, fn


def main() -> None:
    args = parse_args()
    dataset = Path(args.dataset)
    split = args.split

    img_dir = dataset / "images" / split
    lbl_dir = dataset / "labels" / split

    outdir = Path(args.outdir) / split
    outdir.mkdir(parents=True, exist_ok=True)

    params = load_params(args.config)

    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    total_images = 0
    total_tp = 0
    total_fp = 0
    total_fn = 0

    per_image = []

    for img_path in sorted(img_dir.iterdir()):
        if img_path.suffix.lower() not in exts:
            continue

        bgr = cv2.imread(str(img_path))
        if bgr is None:
            continue

        h, w = bgr.shape[:2]
        label_path = lbl_dir / f"{img_path.stem}.txt"
        gts = read_yolo_labels(label_path, w, h)

        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        det = detect_classical(rgb, params, return_debug=False)
        preds = det["bboxes"]
        scores = det["scores"]

        tp, fp, fn = match_greedy(preds, scores, gts, float(args.iou))

        total_images += 1
        total_tp += tp
        total_fp += fp
        total_fn += fn

        per_image.append(
            {
                "image": img_path.name,
                "gt": len(gts),
                "pred": len(preds),
                "tp": tp,
                "fp": fp,
                "fn": fn,
            }
        )

    precision = float(total_tp / (total_tp + total_fp)) if (total_tp + total_fp) > 0 else 0.0
    recall = float(total_tp / (total_tp + total_fn)) if (total_tp + total_fn) > 0 else 0.0
    f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    summary = {
        "dataset": str(dataset),
        "split": split,
        "iou_threshold": float(args.iou),
        "images": total_images,
        "tp": total_tp,
        "fp": total_fp,
        "fn": total_fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "det_threshold": float(params.det_threshold),
        "config_path": str(Path(args.config)),
    }

    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (outdir / "per_image.json").write_text(json.dumps(per_image, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Saved logs to: {outdir}")


if __name__ == "__main__":
    main()
