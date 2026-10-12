"""Build deterministic public data archives; run from any working directory."""

import hashlib
import zipfile
from pathlib import Path

from tangut_workbench.core import load, read_json, stats, validate, write_json
from tangut_workbench.export import export_cldf

ROOT = Path(__file__).resolve().parents[1]


def archive(path, files, base, date):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for file in sorted(files):
            info = zipfile.ZipInfo(file.relative_to(base).as_posix(), (*date, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, file.read_bytes())


def main():
    errors = validate(ROOT)
    if errors:
        raise SystemExit("\n".join(errors))
    project = read_json(ROOT / "data/project.json")
    version = project["version"]
    date = tuple(map(int, project["updated"].split("-")))
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    files = [p for name in ("data", "schemas", "docs", "licenses", "vendor")
             for p in (ROOT / name).rglob("*") if p.is_file()]
    files += [ROOT / name for name in ("README.md", "NOTICE.md", "LICENSE", "CITATION.cff", "CHANGELOG.md")]
    archive(output / f"tangut-workbench-data-v{version}.zip", files, ROOT, date)
    cldf = ROOT / "build/release-cldf"
    export_cldf(ROOT, cldf)
    archive(output / f"tangut-workbench-cldf-v{version}.zip",
            [p for p in cldf.iterdir() if p.is_file()], cldf, date)
    write_json(output / "stats.json", stats(load(ROOT)))
    assets = [output / f"tangut-workbench-data-v{version}.zip",
              output / f"tangut-workbench-cldf-v{version}.zip", output / "stats.json"]
    (output / "SHA256SUMS").write_text("".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in assets
    ), encoding="utf-8")
    print((output / "SHA256SUMS").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
