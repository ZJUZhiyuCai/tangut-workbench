"""Portable data operations. No network calls, implicit downloads, or AI inference."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator

TABLES = ("sources", "entries", "senses", "documents", "passages", "gaps", "hypotheses")
UNICODE_FILE = "vendor/unicode/TangutSources-17.0.0.txt"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def unicode_records(path: Path) -> list[dict]:
    """Only include characters actually present in the pinned official source file."""
    grouped: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        codepoint, prop, value = line.split("\t")
        record = grouped.setdefault(codepoint, {
            "id": codepoint.replace("+", ""), "codepoint": codepoint,
            "character": chr(int(codepoint[2:], 16)), "source_id": "unicode17",
        })
        key = {"kTGT_MergedSrc": "merged_sources", "kTGT_RSUnicode": "radical_strokes"}[prop]
        if key in record:
            raise ValueError(f"Duplicate Unicode property: {codepoint} {prop}")
        record[key] = value
    return sorted(grouped.values(), key=lambda row: int(row["codepoint"][2:], 16))


def load(root: Path) -> dict:
    result = {table: read_json(root / "data" / f"{table}.json") for table in TABLES}
    result["project"] = read_json(root / "data/project.json")
    result["characters"] = [json.loads(line) for line in
                            (root / "data/characters.jsonl").read_text(encoding="utf-8").splitlines()]
    return result


def validate(root: Path) -> list[str]:
    """Validate shape, references, evidence status, coordinates, and vendored provenance."""
    errors: list[str] = []
    try:
        data = load(root)
        schema = read_json(root / "schemas/dataset.schema.json")
        Draft202012Validator.check_schema(schema)
        for error in Draft202012Validator(schema).iter_errors(data):
            errors.append(f"{'/'.join(map(str, error.absolute_path))}: {error.message}")
        if errors:
            return errors
        for table in (*TABLES, "characters"):
            ids = [row["id"] for row in data[table]]
            for ident, count in Counter(ids).items():
                if count > 1:
                    errors.append(f"{table}: duplicate ID {ident}")
        indexes = {table: {row["id"]: row for row in data[table]}
                   for table in (*TABLES, "characters")}

        def ref(table, ident, context):
            if ident not in indexes[table]:
                errors.append(f"{context}: unknown {table} reference {ident}")
                return None
            return indexes[table][ident]

        for record in data["characters"]:
            ref("sources", record["source_id"], record["id"])
        expected = unicode_records(root / UNICODE_FILE)
        if data["characters"] != expected:
            errors.append("characters: inventory differs from the pinned Unicode source; run import-unicode")
        for entry in data["entries"]:
            characters = [ref("characters", c, entry["id"]) for c in entry["character_ids"]]
            if all(characters) and entry["headword"] != "".join(c["character"] for c in characters):
                errors.append(f"{entry['id']}: headword does not match character_ids")
        for table in ("senses", "documents", "passages", "gaps", "hypotheses"):
            for row in data[table]:
                for ev in row["evidence"]:
                    source = ref("sources", ev["source_id"], row["id"])
                    if source and ev["kind"] == "dictionary_scan" and source["kind"] != "dictionary":
                        errors.append(f"{row['id']}: dictionary_scan requires a dictionary source")
                if "document_id" in row:
                    ref("documents", row["document_id"], row["id"])
        for sense in data["senses"]:
            ref("entries", sense["entry_id"], sense["id"])
            if sense["status"] == "source_checked" and not any(
                ev["kind"] == "dictionary_scan" and ev["inspection"] == "direct"
                for ev in sense["evidence"]
            ):
                errors.append(f"{sense['id']}: source_checked needs direct dictionary-page evidence")
            for review in sense["independent_reviews"]:
                if not review["reviewer"] or not review["record_url"]:
                    errors.append(f"{sense['id']}: independent review needs a named, linked record")
        for row in data["hypotheses"]:
            for ident in row["related_character_ids"]:
                ref("characters", ident, row["id"])
            for ident in row["related_sense_ids"]:
                ref("senses", ident, row["id"])
            for ident in row["gap_ids"]:
                ref("gaps", ident, row["id"])
        for row in data["passages"]:
            width, height = row["image_dimensions"]
            left, top, right, bottom = row["box"]
            if not (0 <= left < right <= width and 0 <= top < bottom <= height):
                errors.append(f"{row['id']}: box outside declared image dimensions")
            for ch in row["transcription"]:
                ref("characters", f"U{ord(ch):X}", row["id"])
            if row["translation_status"] == "untranslated" and row["translation_zh"] is not None:
                errors.append(f"{row['id']}: untranslated passage cannot contain a translation")
            if row["novelty"] == "new_translation" and row["translation_status"] != "translated":
                errors.append(f"{row['id']}: new translation requires a translated passage")
            if row["novelty"] == "new_translation" and row["unit_type"] != "passage":
                errors.append(f"{row['id']}: alignment windows cannot count as new translated passages")
            if row["translation_status"] == "translated" and not row["translation_zh"]:
                errors.append(f"{row['id']}: translated passage needs a non-empty translation")
        for record in read_json(root / "vendor/manifest.json"):
            asset_path = (root / record["path"]).resolve()
            if not asset_path.is_relative_to(root.resolve()):
                errors.append("vendor: asset path escapes repository")
                continue
            if not asset_path.is_file() or hashlib.sha256(asset_path.read_bytes()).hexdigest() != record["sha256"]:
                errors.append(f"vendor: SHA256 mismatch for {record['path']}")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"Cannot validate dataset: {exc}")
    return errors


def stats(data: dict) -> dict:
    return {
        "unicode_characters": len(data["characters"]),
        "lexical_entries": len(data["entries"]),
        "senses_source_checked": sum(s["status"] == "source_checked" for s in data["senses"]),
        "senses_source_reported": sum(s["status"] == "source_reported" for s in data["senses"]),
        "senses_proposed": sum(s["status"] == "proposed" for s in data["senses"]),
        "senses_with_independent_review": sum(bool(s["independent_reviews"]) for s in data["senses"]),
        "documents": len(data["documents"]),
        "alignment_windows": sum(p["unit_type"] == "alignment_window" for p in data["passages"]),
        "open_hypotheses": sum(h["status"] == "proposed" for h in data["hypotheses"]),
        "unread_regions": sum(g["status"] == "unread" for g in data["gaps"]),
        "new_translated_passages": sum(p["unit_type"] == "passage" and p["novelty"] == "new_translation" and
                                       p["translation_status"] == "translated"
                                       for p in data["passages"]),
    }


def search(data: dict, query: str, limit: int = 50) -> list[dict]:
    query = query.strip().casefold()
    if not query:
        return []
    # Li's 2008 source identifier is not silently treated as every Li edition's ID.
    if re.fullmatch(r"l\d{1,4}", query):
        query = f"l2008-{int(query[1:]):04d}"
    if re.fullmatch(r"(?:u\+|u)?[0-9a-f]{5}", query):
        query = f"u+{query.removeprefix('u+').removeprefix('u')}"
    senses = {e["id"]: [s for s in data["senses"] if s["entry_id"] == e["id"]]
              for e in data["entries"]}
    by_char: dict[str, list] = {}
    headwords: dict[str, list] = {}
    for entry in data["entries"]:
        for ident in entry["character_ids"]:
            by_char.setdefault(ident, []).extend(senses[entry["id"]])
            headwords.setdefault(ident, []).append(entry["headword"])
    result = []
    for character in data["characters"]:
        linked = by_char.get(character["id"], [])
        haystack = " ".join([character["character"], character["codepoint"],
                             character["merged_sources"],
                             *headwords.get(character["id"], []),
                             *[s["gloss_zh"] + " " + s["gloss_en"] for s in linked]]).casefold()
        if query in haystack:
            result.append({**character, "senses": linked})
            if len(result) >= limit:
                break
    return result
