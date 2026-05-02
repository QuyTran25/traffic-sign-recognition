import argparse
from pathlib import Path

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data" / "detection.yaml"
DEFAULT_WEIGHTS = ROOT / "output" / "yolov8" / "traffic_sign_detector" / "weights" / "best.pt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate YOLOv8 detector.")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATA), help="Path to dataset yaml.")
    parser.add_argument("--weights", type=str, default=str(DEFAULT_WEIGHTS), help="Path to trained weights.")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = YOLO(args.weights)
    metrics = model.val(data=args.data, imgsz=args.imgsz)
    print(metrics)


if __name__ == "__main__":
    main()
