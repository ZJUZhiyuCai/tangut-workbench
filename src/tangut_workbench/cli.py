import argparse
import json
from pathlib import Path

from .core import UNICODE_FILE, load, search, stats, unicode_records, validate
from .export import build_site, export_cldf


def main(argv=None):
    parser = argparse.ArgumentParser(description="Source-linked Tangut research tools")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="check schema, provenance, references and coordinates")
    sub.add_parser("stats", help="report separate inventory, lexical and translation counts")
    sub.add_parser("import-unicode", help="rebuild the character index from the pinned source")
    find = sub.add_parser("lookup", help="search glyph, U+code, L2008 number or gloss")
    find.add_argument("query")
    find.add_argument("--limit", type=int, default=20)
    for name in ("build", "export-cldf"):
        output = sub.add_parser(name)
        output.add_argument("--output", type=Path, default=Path("build") / name)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == "import-unicode":
        rows = unicode_records(root / UNICODE_FILE)
        (root / "data/characters.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
            encoding="utf-8",
        )
        print(f"Imported {len(rows)} Unicode records (no lexical meanings).")
        return 0
    errors = validate(root)
    if errors:
        print("\n".join(errors))
        return 1
    if args.command == "validate":
        print("Dataset validation passed. Linguistic claims still require source review.")
    elif args.command == "stats":
        print(json.dumps(stats(load(root)), ensure_ascii=False, indent=2))
    elif args.command == "lookup":
        if args.limit < 1:
            parser.error("--limit must be positive")
        print(json.dumps(search(load(root), args.query, args.limit), ensure_ascii=False, indent=2))
    elif args.command in ("build", "export-cldf"):
        destination = args.output.resolve()
        protected = [root / name for name in ("data", "web", "src", "vendor", "schemas", ".git")]
        if destination == root or any(destination.is_relative_to(p) or p.is_relative_to(destination)
                                      for p in protected):
            parser.error("output must not overlap source directories")
        if args.command == "build":
            build_site(root, destination)
        else:
            try:
                export_cldf(root, destination)
            except ModuleNotFoundError:
                parser.error('CLDF export requires: pip install -e ".[cldf]"')
        print(f"Wrote {destination}")
    return 0
