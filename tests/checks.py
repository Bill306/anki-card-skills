"""Exercise meaningful export/import invariants on the local synthetic PDF fixture."""
import copy
import importlib.metadata
import importlib.util
import json
import argparse
import shutil
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from uuid import uuid4

from anki.collection import Collection, ImportAnkiPackageRequest

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(tempfile.mkdtemp(prefix="anki-card-skill-checks-")).resolve() / "fixture"
shutil.copytree(ROOT / "examples/lumabox", HERE)
spec = importlib.util.spec_from_file_location("pdf_anki_export", ROOT / "skills/pdf-to-anki/scripts/export_anki.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main():
    data = json.loads((HERE / "cards.json").read_text())
    cases = []

    def rejects(name, mutate):
        bad = copy.deepcopy(data)
        mutate(bad)
        try:
            module.validate(bad, HERE)
        except ValueError:
            cases.append({"check": name, "status": "PASS"})
        else:
            raise AssertionError(f"Accepted invalid cards: {name}")

    rejects("out_of_range_source_page", lambda d: d["cards"][0]["source_refs"][0].update(pages=[5]))
    rejects("missing_source_evidence", lambda d: d["cards"][0]["source_refs"][0].pop("evidence"))
    rejects("duplicate_question", lambda d: d["cards"][1].update(question=d["cards"][0]["question"]))
    rejects("uncovered_included_concept", lambda d: d["cards"].pop(0))
    rejects("multiple_cloze_targets", lambda d: d["cards"][2].update(question="{{c1::丢失}} {{c2::保留}}"))
    rejects("media_path_escape", lambda d: d["cards"][0].update(back_media=["../pdf-to-anki/SKILL.md"]))
    try:
        module.export(HERE / "cards.json", HERE / "output")
    except ValueError:
        cases.append({"check": "preserve_existing_output", "status": "PASS"})
    else:
        raise AssertionError("Existing output was overwritten")
    d = copy.deepcopy(data)
    d["cards"][0]["question"] = "用途是什么？断电会怎样？"
    assert module.validate(d, HERE)[3][0]["code"] == "possible_multiple_recall_targets"
    cases.append({"check": "multiple_question_warning", "status": "PASS"})
    assert module.normalized("x < y?") != module.normalized("x > y?")
    assert module.normalized("V 的定义？") != module.normalized("v 的定义？")
    assert "&lt;" in module.rich("p < 0.05") and "&amp;" in module.rich("A & B")
    cases.append({"check": "math_operators_case_and_html_escaping_preserved", "status": "PASS"})

    manifest = json.loads((HERE / "prepared/source.json").read_text())
    scan = manifest["pages"][3]
    assert scan["text_chars"] == 0 and "sparse_text_check_scan_or_diagram" in scan["flags"]
    assert len(manifest["pages"]) == 4 and all((HERE / "prepared" / p["render_path"]).is_file() for p in manifest["pages"])
    cases.append({"check": "scan_page_flagged_and_all_pages_rendered", "status": "PASS"})

    updated = copy.deepcopy(data)
    updated["cards"][0]["answer"] = "快速、临时的数据存取；不承担长期保存。"
    run_id = uuid4().hex[:8]
    updated_path = HERE / f"cards-updated-{run_id}.json"
    updated_path.write_text(json.dumps(updated, ensure_ascii=False, indent=2))
    updated_output = HERE / f"output-updated-{run_id}"
    module.export(updated_path, updated_output)
    before = json.loads((HERE / "output/audit.json").read_text())
    after = json.loads((updated_output / "audit.json").read_text())
    assert before["card_guids"] == after["card_guids"]
    cases.append({"check": "stable_guids_after_answer_edit", "status": "PASS"})

    test_dir = HERE / f"backend-validation-{run_id}"
    test_dir.mkdir()
    collection = Collection(str(test_dir / "collection.anki2"))
    try:
        first = collection.import_anki_package(ImportAnkiPackageRequest(package_path=str(HERE / "output/deck.apkg")))
        assert collection.note_count() == collection.card_count() == 12
        assert len(first.log.new) == 12
        cases.append({"check": "actual_anki_backend_import_12_notes_12_cards", "status": "PASS"})

        cloze = next(collection.get_note(nid) for nid in collection.find_notes("") if collection.get_note(nid).fields[0] == "checksum-length")
        rendered = cloze.cards()[0]
        question, answer = rendered.question(), rendered.answer()
        class VisibleText(HTMLParser):
            def __init__(self):
                super().__init__(); self.parts = []
            def handle_data(self, value):
                self.parts.append(value)
        def visible(value):
            parser = VisibleText(); parser.feed(value.split("</style>")[-1]); return "".join(parser.parts)
        assert "16" not in visible(question) and "16" in visible(answer)
        basic = next(collection.get_note(nid) for nid in collection.find_notes("") if collection.get_note(nid).fields[0] == "cache-purpose")
        assert "快速、临时的数据存取" not in basic.cards()[0].question()
        assert "快速、临时的数据存取" in basic.cards()[0].answer()
        cases.append({"check": "basic_and_cloze_fronts_hide_answers", "status": "PASS"})

        media_files = list(Path(collection.media.dir()).glob("pdfanki_*.png"))
        assert len(media_files) == 1 and media_files[0].read_bytes() == (HERE / "prepared/pages" / (manifest["id"] + "-p0004.png")).read_bytes()
        cases.append({"check": "packaged_image_imported_byte_identical", "status": "PASS"})

        same = collection.import_anki_package(ImportAnkiPackageRequest(package_path=str(HERE / "output/deck.apkg")))
        assert collection.note_count() == collection.card_count() == 12 and len(same.log.new) == 0
        cases.append({"check": "reimport_does_not_duplicate", "status": "PASS"})
        update = ImportAnkiPackageRequest(package_path=str(updated_output / "deck.apkg"))
        update.options.update_notes = 1  # Explicit "always update" in this isolated collection only.
        collection.import_anki_package(update)
        assert collection.note_count() == collection.card_count() == 12
        changed = next(collection.get_note(nid) for nid in collection.find_notes("") if collection.get_note(nid).fields[0] == "cache-purpose")
        assert "不承担长期保存" in changed.fields[2]
        cases.append({"check": "answer_edit_updates_existing_note", "status": "PASS"})
    finally:
        collection.close()
    result = {"anki_backend_version": importlib.metadata.version("anki"), "checks": cases,
              "real_user_collection_accessed": False,
              "semantic_review": "Agent read all 4 PDF page images and reviewed all 12 cards; not an independent educational benchmark.",
              "scope_limit": "Synthetic fixture, Basic/Cloze only. One deliberately unavailable source fact remains blocked."}
    (HERE / "verification-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    if args.report:
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    main()
