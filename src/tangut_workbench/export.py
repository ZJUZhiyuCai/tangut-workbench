"""Reproducible exports; the public app and CLDF reuse the same curated records."""

import shutil
from pathlib import Path

from .core import load, stats, write_json


def build_site(root: Path, destination: Path):
    data = load(root)
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(root / "web", destination, dirs_exist_ok=True)
    shutil.copytree(root / "licenses", destination / "licenses", dirs_exist_ok=True)
    shutil.copy2(root / "NOTICE.md", destination / "NOTICE.md")
    write_json(destination / "dataset.json", {**data, "stats": stats(data)})
    write_json(destination / "data/stats.json", stats(data))
    (destination / ".nojekyll").touch()


def export_cldf(root: Path, destination: Path):
    """Conservative export: only page-checked senses, with their original status attached."""
    from pycldf import Dictionary
    from pycldf.sources import Source

    data = load(root)
    destination.mkdir(parents=True, exist_ok=True)
    dataset = Dictionary.in_dir(destination)
    dataset.add_component("LanguageTable")
    dataset.add_columns("SenseTable", {
        "name": "Source", "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#source",
        "datatype": "string", "separator": ";",
    }, "Evidence_Status", "Independent_Review_Count")
    dataset.add_foreign_key("SenseTable", "Entry_ID", "EntryTable", "ID")
    dataset.add_foreign_key("EntryTable", "Language_ID", "LanguageTable", "ID")
    dataset.properties["dc:title"] = "Tangut Workbench — page-checked lexical senses"
    dataset.properties["dc:license"] = "https://creativecommons.org/licenses/by/4.0/"
    dataset.properties["dc:description"] = (
        "Only source_checked senses are exported. This means checked against a dictionary page; "
        "it does not mean independently reviewed, newly deciphered, or verified in Inv.5875. "
        "Hypotheses, reported senses and Unicode-only records are excluded."
    )
    selected = [s for s in data["senses"] if s["status"] == "source_checked"]
    needed = {ev["source_id"] for sense in selected for ev in sense["evidence"]}
    for source in data["sources"]:
        if source["id"] in needed:
            dataset.add_sources(Source("misc", source["id"], title=source["title"],
                                       author=source["author"], year=source["year"],
                                       url=source["url"]))
    used_entries = {sense["entry_id"] for sense in selected}
    dataset.write(
        LanguageTable=[{"ID": "txg", "Name": "Tangut", "ISO639P3code": "txg"}],
        EntryTable=[{"ID": e["id"], "Language_ID": "txg", "Headword": e["headword"],
                     "Part_Of_Speech": e["part_of_speech"]}
                    for e in data["entries"] if e["id"] in used_entries],
        SenseTable=[{"ID": s["id"], "Entry_ID": s["entry_id"],
                     "Description": s["gloss_zh"],
                     "Source": [f"{ev['source_id']}[{ev['locator']}]" for ev in s["evidence"]],
                     "Evidence_Status": s["status"],
                     "Independent_Review_Count": len(s["independent_reviews"])} for s in selected],
    )
    if not dataset.validate():
        raise ValueError("Export failed CLDF validation")
    shutil.copy2(root / "licenses/CC-BY-4.0.txt", destination / "LICENSE")
    return dataset.filename
