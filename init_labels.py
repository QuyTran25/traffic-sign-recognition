from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMAGE_DIR = ROOT / "image"
LABEL_DIR = ROOT / "labels"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def main() -> None:
    LABEL_DIR.mkdir(parents=True, exist_ok=True)

    created = 0
    for image_path in sorted(IMAGE_DIR.iterdir()):
        if image_path.suffix.lower() not in IMAGE_EXTS:
            continue

        label_path = LABEL_DIR / f"{image_path.stem}.txt"
        if not label_path.exists():
            label_path.write_text("", encoding="utf-8")
            created += 1

    print(f"Created {created} label template files in {LABEL_DIR}")


if __name__ == "__main__":
    main()
