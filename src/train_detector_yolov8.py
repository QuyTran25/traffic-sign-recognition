import argparse
from pathlib import Path

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data" / "detection.yaml"
DEFAULT_OUTPUT = ROOT / "output" / "yolov8"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train YOLOv8 detector on traffic sign dataset.")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATA), help="Path to dataset yaml.")
    parser.add_argument("--epochs", type=int, default=80, help="Number of epochs.")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size.")
    parser.add_argument("--batch", type=int, default=8, help="Batch size.")
    parser.add_argument("--weights", type=str, default="yolov8n.pt", help="Pretrained weights.")
    parser.add_argument("--project", type=str, default=str(DEFAULT_OUTPUT), help="Output folder.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = YOLO(args.weights)

    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=args.project,
        name="traffic_sign_detector",
        exist_ok=True,
    )


if __name__ == "__main__":
    main()
