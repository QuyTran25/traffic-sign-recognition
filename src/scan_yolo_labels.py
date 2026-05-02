from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LABEL_DIR = ROOT / "labels"


def main() -> None:
    if not LABEL_DIR.exists():
        print(f"Label directory not found: {LABEL_DIR}")
        return

    found = False
    for path in sorted(LABEL_DIR.glob("*.txt")):
        if path.name in {"classes.txt", ".gitkeep"}:
            continue

        bad = []
        for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw.strip()
            if not line:
                continue
            parts = line.split(" ")
            if len(parts) != 5:
                bad.append((i, raw))

        if bad:
            found = True
            print(path.name)
            for i, raw in bad:
                print(f"  line {i}: {raw!r}")

    if not found:
        print("No malformed YOLO lines found.")


if __name__ == "__main__":
    main()