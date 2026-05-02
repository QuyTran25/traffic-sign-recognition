from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LABEL_DIR = ROOT / "labels"


def clean_file(label_path: Path) -> tuple[int, int]:
    kept = []
    removed = []

    for raw_line in label_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) != 5:
            removed.append(raw_line)
            continue

        kept.append(" ".join(parts))

    label_path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")

    if removed:
        bad_path = label_path.with_suffix(label_path.suffix + ".bad")
        bad_path.write_text("\n".join(removed) + "\n", encoding="utf-8")

    return len(kept), len(removed)


def main() -> None:
    if not LABEL_DIR.exists():
        print(f"Label directory not found: {LABEL_DIR}")
        return

    total_files = 0
    total_removed = 0

    for label_path in sorted(LABEL_DIR.glob("*.txt")):
        if label_path.name in {"classes.txt", ".gitkeep"}:
            continue

        _, removed = clean_file(label_path)
        if removed:
            total_removed += removed
        total_files += 1

    print(f"Checked {total_files} label files")
    print(f"Removed {total_removed} malformed lines")


if __name__ == "__main__":
    main()