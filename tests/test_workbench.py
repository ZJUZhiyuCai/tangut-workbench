import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tangut_workbench.core import load, read_json, search, stats, unicode_records, validate, write_json
from tangut_workbench.export import build_site, export_cldf

ROOT = Path(__file__).resolve().parents[1]


class ReadOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load(ROOT)

    def test_production_dataset_validates(self):
        self.assertEqual(validate(ROOT), [])

    def test_inventory_covers_unicode_17_extension(self):
        records = unicode_records(ROOT / "vendor/unicode/TangutSources-17.0.0.txt")
        self.assertEqual(len(records), 6175)
        self.assertEqual(records[-1]["codepoint"], "U+18D1E")
        self.assertEqual(self.data["characters"], records)

    def test_lookup_glyph_gloss_codepoint_and_li_number(self):
        for query in ("𗞈", "葡萄", "grape", "U+17788", "u17788", "17788", "L4267", "l2008-4267"):
            with self.subTest(query=query):
                self.assertEqual(search(self.data, query)[0]["id"], "U17788")

    def test_lookup_unknown_and_blank(self):
        self.assertEqual(search(self.data, "没有的词义"), [])
        self.assertEqual(search(self.data, " "), [])

    def test_unicode_only_character_has_no_invented_senses(self):
        row = search(self.data, "U+18D1E")[0]
        self.assertEqual(row["senses"], [])

    def test_progress_separates_inventory_from_research(self):
        counts = stats(self.data)
        self.assertEqual(counts["unicode_characters"], 6175)
        self.assertEqual(counts["lexical_entries"], 5)
        self.assertEqual(counts["senses_source_checked"], 2)
        self.assertEqual(counts["senses_source_reported"], 3)
        self.assertEqual(counts["senses_with_independent_review"], 0)
        self.assertEqual(counts["new_translated_passages"], 0)
        self.assertEqual(counts["alignment_windows"], 6)

    def test_hypotheses_have_not_changed_baseline(self):
        self.assertTrue(all(not h["accepted"] and not h["manuscript_text_changed"]
                            for h in self.data["hypotheses"]))

    def test_font_gap_is_explicit(self):
        coverage = read_json(ROOT / "web/font-coverage.json")
        ids = {c["id"] for c in self.data["characters"]}
        missing = set(coverage["missing_character_ids"])
        self.assertEqual(len(missing), 30)
        self.assertTrue(missing <= ids)
        self.assertEqual(coverage["covered_characters"] + len(missing), len(ids))

    def test_public_data_contains_no_local_paths(self):
        serialized = json.dumps(self.data, ensure_ascii=False)
        for private_marker in ("/Users/", "file://", "127.0.0.1", "localhost", "access_token="):
            self.assertNotIn(private_marker, serialized)

    def test_multi_character_headword_lookup(self):
        data = json.loads(json.dumps(self.data))
        data["entries"].append({"id": "test-compound", "headword": "𗞈𗞤",
                                "character_ids": ["U17788", "U177A4"], "part_of_speech": "test"})
        self.assertEqual(len(search(data, "𗞈𗞤")), 2)

    def test_site_export_preserves_status_and_license_notices(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            build_site(ROOT, output)
            exported = read_json(output / "dataset.json")
            self.assertEqual(exported["stats"], stats(self.data))
            self.assertEqual(exported["hypotheses"], self.data["hypotheses"])
            for asset in ("index.html", "app.js", "style.css", "NOTICE.md", "font-coverage.json",
                          "licenses/Unicode-3.0.txt", "licenses/OFL-NotoSerifTangut.txt"):
                self.assertTrue((output / asset).is_file(), asset)

    def test_cldf_export_is_valid_and_excludes_reported_and_proposed(self):
        from pycldf import Dataset

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            filename = export_cldf(ROOT, output)
            dataset = Dataset.from_metadata(output / filename)
            self.assertTrue(dataset.validate())
            senses = list(dataset["SenseTable"])
            self.assertEqual(len(senses), 2)
            self.assertTrue(all(s["Evidence_Status"] == "source_checked" for s in senses))
            self.assertTrue(all(s["Source"] and "li2012[" in s["Source"][0] for s in senses))
            self.assertTrue(all(int(s["Independent_Review_Count"]) == 0 for s in senses))
            self.assertEqual(len(list(dataset["EntryTable"])), 2)
            self.assertTrue((output / "sources.bib").is_file())
            self.assertTrue((output / "LICENSE").is_file())


class InvalidDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for directory in ("data", "schemas", "vendor", "licenses", "web"):
            shutil.copytree(ROOT / directory, self.root / directory)

    def tearDown(self):
        self.tmp.cleanup()

    def mutate(self, table, operation):
        path = self.root / "data" / f"{table}.json"
        rows = read_json(path)
        operation(rows)
        write_json(path, rows)

    def assert_rejected(self, fragment):
        self.assertIn(fragment, "\n".join(validate(self.root)))

    def test_duplicate_ids_rejected(self):
        self.mutate("entries", lambda rows: rows.append(rows[0]))
        self.assert_rejected("duplicate ID")

    def test_unknown_source_rejected(self):
        self.mutate("senses", lambda rows: rows[0]["evidence"][0].update(source_id="absent"))
        self.assert_rejected("unknown sources reference")

    def test_unknown_entry_rejected(self):
        self.mutate("senses", lambda rows: rows[0].update(entry_id="absent"))
        self.assert_rejected("unknown entries reference")

    def test_wrong_glyph_mapping_rejected(self):
        self.mutate("entries", lambda rows: rows[0].update(headword="𗞤"))
        self.assert_rejected("headword does not match")

    def test_reported_evidence_cannot_be_promoted_without_page_check(self):
        self.mutate("senses", lambda rows: rows[2].update(status="source_checked"))
        self.assert_rejected("needs direct dictionary-page evidence")

    def test_dictionary_evidence_cannot_point_to_catalogue(self):
        self.mutate("senses", lambda rows: rows[0]["evidence"][0].update(source_id="catalogue2024"))
        self.assert_rejected("requires a dictionary source")

    def test_missing_locator_rejected(self):
        self.mutate("senses", lambda rows: rows[0]["evidence"][0].update(locator=""))
        self.assert_rejected("locator")

    def test_box_outside_image_rejected(self):
        self.mutate("passages", lambda rows: rows[0].update(box=[1, 1, 9999, 100]))
        self.assert_rejected("box outside declared image dimensions")

    def test_inverted_box_rejected(self):
        self.mutate("passages", lambda rows: rows[0].update(box=[100, 100, 10, 10]))
        self.assert_rejected("box outside declared image dimensions")

    def test_untranslated_record_cannot_hide_translation(self):
        self.mutate("passages", lambda rows: rows[0].update(translation_zh="虚构译文"))
        self.assert_rejected("untranslated passage cannot contain a translation")

    def test_alignment_cannot_inflate_new_translation_count(self):
        self.mutate("passages", lambda rows: rows[0].update(
            novelty="new_translation", translation_status="translated", translation_zh="字义"))
        self.assert_rejected("alignment windows cannot count")

    def test_untranslated_cannot_be_new_translation(self):
        self.mutate("passages", lambda rows: rows[0].update(novelty="new_translation"))
        self.assert_rejected("new translation requires a translated passage")

    def test_candidate_cannot_be_silently_accepted(self):
        self.mutate("hypotheses", lambda rows: rows[0].update(accepted=True))
        self.assert_rejected("accepted")

    def test_independent_review_requires_named_linked_record(self):
        self.mutate("senses", lambda rows: rows[0].update(
            independent_reviews=[{"reviewer": "", "record_url": "", "date": "2026-10-12"}]))
        self.assert_rejected("independent_reviews")

    def test_vendor_hash_mismatch_rejected(self):
        path = self.root / "vendor/unicode/TangutSources-17.0.0.txt"
        path.write_bytes(path.read_bytes() + b"\n# modified\n")
        self.assert_rejected("SHA256 mismatch")

    def test_accidental_unicode_edit_rejected(self):
        path = self.root / "data/characters.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
        self.assert_rejected("inventory differs")


if __name__ == "__main__":
    unittest.main()
