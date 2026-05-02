import argparse
from pathlib import Path

import cv2
from ultralytics import YOLO

from cv_region_proposal import propose_regions


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WEIGHTS = ROOT / "output" / "yolov8" / "traffic_sign_detector" / "weights" / "best.pt"
DEFAULT_IMAGE_DIR = ROOT / "image"
DEFAULT_OUTPUT = ROOT / "output" / "cv_yolo_preview"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CV proposals + YOLOv8 detector.")
    parser.add_argument("--weights", type=str, default=str(DEFAULT_WEIGHTS), help="Path to trained weights.")
    parser.add_argument("--image-dir", type=str, default=str(DEFAULT_IMAGE_DIR), help="Directory of images.")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT), help="Output directory.")
    parser.add_argument("--conf", type=float, default=0.25, help="YOLO confidence threshold.")
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image size.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    image_dir = Path(args.image_dir)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    model = YOLO(args.weights)

    for image_path in sorted(image_dir.iterdir()):
        if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            continue

        image = cv2.imread(str(image_path))
        if image is None:
            continue

        proposals = propose_regions(image)
        detections = []

        for box in proposals:
            crop = image[box.y1:box.y2, box.x1:box.x2]
            if crop.size == 0:
                continue
            results = model.predict(crop, conf=args.conf, imgsz=args.imgsz, verbose=False)
            for r in results:
                for xyxy, conf in zip(r.boxes.xyxy.cpu().numpy(), r.boxes.conf.cpu().numpy()):
                    x1, y1, x2, y2 = xyxy.astype(int)
                    detections.append((
                        box.x1 + x1,
                        box.y1 + y1,
                        box.x1 + x2,
                        box.y1 + y2,
                        float(conf),
                    ))

        canvas = image.copy()
        for x1, y1, x2, y2, conf in detections:
            cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                canvas,
                f"traffic_sign {conf:.2f}",
                (x1, max(15, y1 - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
                cv2.LINE_AA,
            )

        out_path = output_dir / image_path.name
        cv2.imwrite(str(out_path), canvas)

    print(f"Saved previews to {output_dir}")


if __name__ == "__main__":
    main()
