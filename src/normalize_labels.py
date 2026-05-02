from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LABEL_DIR = ROOT / "labels"


def normalize_file(label_path: Path) -> bool:
    changed = False
    output_lines = []

    for raw_line in label_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) != 5:
            output_lines.append(line)
            continue

        if parts[0] != "0":
            parts[0] = "0"
            changed = True

        output_lines.append(" ".join(parts))

    label_path.write_text("\n".join(output_lines) + ("\n" if output_lines else ""), encoding="utf-8")
    return changed


def main() -> None:
    if not LABEL_DIR.exists():
        print(f"Label directory not found: {LABEL_DIR}")
        return

    updated = 0
    for label_path in sorted(LABEL_DIR.glob("*.txt")):
        if label_path.name in {"classes.txt", ".gitkeep"}:
            continue
        if normalize_file(label_path):
            updated += 1

    print(f"Normalized class IDs in {updated} label files")


if __name__ == "__main__":
    main()