import argparse
import random
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
IMAGE_DIR = ROOT / "image"
LABEL_DIR = ROOT / "labels"
OUT_IMAGES_TRAIN = ROOT / "data" / "detection" / "images" / "train"
OUT_IMAGES_VAL = ROOT / "data" / "detection" / "images" / "val"
OUT_LABELS_TRAIN = ROOT / "data" / "detection" / "labels" / "train"
OUT_LABELS_VAL = ROOT / "data" / "detection" / "labels" / "val"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split detection dataset into train/val.")
    parser.add_argument("--val-ratio", type=float, default=0.2, help="Validation split ratio.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--copy", action="store_true", help="Copy files instead of symlink.")
    return parser.parse_args()


def ensure_dirs() -> None:
    OUT_IMAGES_TRAIN.mkdir(parents=True, exist_ok=True)
    OUT_IMAGES_VAL.mkdir(parents=True, exist_ok=True)
    OUT_LABELS_TRAIN.mkdir(parents=True, exist_ok=True)
    OUT_LABELS_VAL.mkdir(parents=True, exist_ok=True)


def list_pairs() -> list[tuple[Path, Path]]:
    pairs = []
    for image_path in sorted(IMAGE_DIR.iterdir()):
        if image_path.suffix.lower() not in IMAGE_EXTS:
            continue
        label_path = LABEL_DIR / f"{image_path.stem}.txt"
        if not label_path.exists():
            continue
        pairs.append((image_path, label_path))
    return pairs


def place_file(src: Path, dst: Path, copy_files: bool) -> None:
    if dst.exists():
        return
    if copy_files:
        shutil.copy2(src, dst)
    else:
        try:
            dst.symlink_to(src)
        except OSError:
            shutil.copy2(src, dst)


def main() -> None:
    args = parse_args()
    ensure_dirs()

    pairs = list_pairs()
    if not pairs:
        print("No image/label pairs found.")
        return

    random.seed(args.seed)
    random.shuffle(pairs)

    split_index = int(len(pairs) * (1 - args.val_ratio))
    train_pairs = pairs[:split_index]
    val_pairs = pairs[split_index:]

    for image_path, label_path in train_pairs:
        place_file(image_path, OUT_IMAGES_TRAIN / image_path.name, args.copy)
        place_file(label_path, OUT_LABELS_TRAIN / label_path.name, args.copy)

    for image_path, label_path in val_pairs:
        place_file(image_path, OUT_IMAGES_VAL / image_path.name, args.copy)
        place_file(label_path, OUT_LABELS_VAL / label_path.name, args.copy)

    print(f"Train pairs: {len(train_pairs)}")
    print(f"Val pairs: {len(val_pairs)}")
    print("Dataset ready at data/detection")


if __name__ == "__main__":
    main()
