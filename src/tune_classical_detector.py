from __future__ import annotations

import argparse
import itertools
import json
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path

import cv2

from classical_detector import ClassicalDetectorParams
from classical_detector import detect_classical
from cv_region_proposal import DetectorConfig


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = ROOT / "data" / "detection"
DEFAULT_BASE_CONFIG = ROOT / "configs" / "classical_detector.json"
DEFAULT_OUTDIR = ROOT / "output" / "classical_detector_tuning"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Small grid search for classical detector params.")
    p.add_argument("--dataset", type=str, default=str(DEFAULT_DATASET), help="YOLO dataset root.")
    p.add_argument("--split", type=str, default="val", choices=["train", "val"], help="Split.")
    p.add_argument("--base-config", type=str, default=str(DEFAULT_BASE_CONFIG), help="Base config JSON.")
    p.add_argument("--outdir", type=str, default=str(DEFAULT_OUTDIR), help="Output directory.")
    p.add_argument("--iou", type=float, default=0.3, help="IoU threshold for matching.")

    p.add_argument(
        "--no-hough",
        action="store_true",
        help="Disable Hough circle/lines during tuning (much faster for large grids).",
    )

    p.add_argument(
        "--det-thresholds",
        type=float,
        nargs="+",
        default=[0.05, 0.1, 0.15, 0.2, 0.25],
        help="Grid for det_threshold.",
    )
    p.add_argument(
        "--min-color-ratios",
        type=float,
        nargs="+",
        default=[0.01, 0.02, 0.03, 0.05, 0.08],
        help="Grid for min_color_ratio.",
    )
    p.add_argument(
        "--canny-pairs",
        type=int,
        nargs="+",
        default=[40, 120, 60, 140, 80, 160, 100, 200],
        help="Flattened list of (low,high) pairs, e.g. 40 120 60 140.",
    )
    p.add_argument("--max-trials", type=int, default=200, help="Cap number of evaluated configs.")
    return p.parse_args()


def _coerce_tuple3(value):
    if isinstance(value, tuple) and len(value) == 3:
        return tuple(int(x) for x in value)
    if isinstance(value, list) and len(value) == 3:
        return (int(value[0]), int(value[1]), int(value[2]))
    return value


def _load_base_config(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("base config must be an object")

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

    return raw


def yolo_line_to_xyxy(line: str, w: int, h: int):
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
    return [x1, y1, x2, y2]


def read_yolo_labels(path: Path, w: int, h: int) -> list[list[int]]:
    if not path.exists():
        return []
    out: list[list[int]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        bb = yolo_line_to_xyxy(raw, w, h)
        if bb is not None:
            out.append(bb)
    return out


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
    order = sorted(range(len(preds)), key=lambda i: scores[i], reverse=True)
    used = [False] * len(gts)

    tp = 0
    fp = 0
    for idx in order:
        p = preds[idx]
        best_iou = 0.0
        best_j = -1
        for j, gt in enumerate(gts):
            if used[j]:
                continue
            v = iou_xyxy(p, gt)
            if v > best_iou:
                best_iou = v
                best_j = j
        if best_j >= 0 and best_iou >= iou_thr:
            used[best_j] = True
            tp += 1
        else:
            fp += 1

    fn = int(sum(1 for u in used if not u))
    return tp, fp, fn


@dataclass
class TrialResult:
    det_threshold: float
    min_color_ratio: float
    canny_low: int
    canny_high: int
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float


def eval_config(dataset: Path, split: str, params: ClassicalDetectorParams, iou_thr: float) -> tuple[int, int, int, float, float, float]:
    img_dir = dataset / "images" / split
    lbl_dir = dataset / "labels" / split

    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    total_tp = total_fp = total_fn = 0
    for img_path in sorted(img_dir.iterdir()):
        if img_path.suffix.lower() not in exts:
            continue

        bgr = cv2.imread(str(img_path))
        if bgr is None:
            continue

        h, w = bgr.shape[:2]
        gts = read_yolo_labels(lbl_dir / f"{img_path.stem}.txt", w, h)

        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        det = detect_classical(rgb, params, return_debug=False)
        preds = det["bboxes"]
        scores = det["scores"]

        tp, fp, fn = match_greedy(preds, scores, gts, float(iou_thr))
        total_tp += tp
        total_fp += fp
        total_fn += fn

    precision = float(total_tp / (total_tp + total_fp)) if (total_tp + total_fp) > 0 else 0.0
    recall = float(total_tp / (total_tp + total_fn)) if (total_tp + total_fn) > 0 else 0.0
    f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return total_tp, total_fp, total_fn, precision, recall, f1


def main() -> None:
    args = parse_args()

    if len(args.canny_pairs) % 2 != 0:
        raise SystemExit("--canny-pairs must be even length: low high low high ...")

    canny_pairs = [(int(args.canny_pairs[i]), int(args.canny_pairs[i + 1])) for i in range(0, len(args.canny_pairs), 2)]

    dataset = Path(args.dataset)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    base = _load_base_config(Path(args.base_config))

    # Extract det_threshold from base, and build DetectorConfig from the rest.
    base_det_threshold = float(base.pop("det_threshold", 0.25))
    _ = base_det_threshold  # kept for backwards compatibility / readability

    trials = list(
        itertools.product(
            [float(x) for x in args.det_thresholds],
            [float(x) for x in args.min_color_ratios],
            canny_pairs,
        )
    )

    if args.max_trials > 0:
        trials = trials[: int(args.max_trials)]

    results: list[TrialResult] = []

    for idx, (det_thr, min_col, (c_low, c_high)) in enumerate(trials, start=1):
        cfg_dict = dict(base)
        cfg_dict["min_color_ratio"] = float(min_col)
        cfg_dict["canny_low"] = int(c_low)
        cfg_dict["canny_high"] = int(c_high)

        if args.no_hough:
            cfg_dict["use_hough_circle"] = False
            cfg_dict["use_hough_lines"] = False

        proposal = DetectorConfig(**cfg_dict)
        params = ClassicalDetectorParams(proposal=proposal, det_threshold=float(det_thr))

        tp, fp, fn, precision, recall, f1 = eval_config(dataset, args.split, params, float(args.iou))

        results.append(
            TrialResult(
                det_threshold=float(det_thr),
                min_color_ratio=float(min_col),
                canny_low=int(c_low),
                canny_high=int(c_high),
                tp=int(tp),
                fp=int(fp),
                fn=int(fn),
                precision=float(precision),
                recall=float(recall),
                f1=float(f1),
            )
        )

        if idx % 25 == 0:
            print(f"Evaluated {idx}/{len(trials)} trials...")

    # Sort by F1 then recall then precision, descending.
    results_sorted = sorted(results, key=lambda r: (r.f1, r.recall, r.precision), reverse=True)

    # Save all results.
    (outdir / "grid_results.json").write_text(
        json.dumps([asdict(r) for r in results_sorted], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    top5 = results_sorted[:5]
    print("Top-5 trials:")
    for r in top5:
        print(f"  f1={r.f1:.3f} p={r.precision:.3f} r={r.recall:.3f} tp={r.tp} fp={r.fp} fn={r.fn} | det={r.det_threshold} min_color={r.min_color_ratio} canny=({r.canny_low},{r.canny_high})")

    best = results_sorted[0] if results_sorted else None
    if best is None:
        raise SystemExit("No trials evaluated")

    # Write best config JSON compatible with existing loader.
    best_cfg = dict(base)
    best_cfg["min_color_ratio"] = best.min_color_ratio
    best_cfg["canny_low"] = best.canny_low
    best_cfg["canny_high"] = best.canny_high
    best_cfg["det_threshold"] = best.det_threshold

    if args.no_hough:
        best_cfg["use_hough_circle"] = False
        best_cfg["use_hough_lines"] = False

    (outdir / "best_config.json").write_text(json.dumps(best_cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (outdir / "best_summary.json").write_text(json.dumps(asdict(best), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Saved: {outdir / 'grid_results.json'}")
    print(f"Saved: {outdir / 'best_config.json'}")


if __name__ == "__main__":
    main()
