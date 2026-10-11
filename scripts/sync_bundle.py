#!/usr/bin/env python3
"""Generate/check plugin skill copies from the canonical skills/ directory."""

import argparse
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    pairs = [
        (root / "skills", root / "plugin/skills"),
        (root / "rules", root / "plugin/rules"),
    ]
    differences = []
    for source, destination in pairs:
        for path in source.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            target = destination / path.relative_to(source)
            if not target.exists() or target.read_bytes() != path.read_bytes():
                differences.append(str(target.relative_to(root)))
                if not args.check:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, target)
    if args.check and differences:
        print("Generated bundle differs: " + ", ".join(differences))
        return 1
    print(
        f"Bundle {'checked' if args.check else 'synchronized'}; {len(differences)} differences."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
