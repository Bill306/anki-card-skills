#!/usr/bin/env python3
"""Validate source-backed card JSON and export APKG plus review artifacts, locally."""
import argparse
import base64
import csv
import hashlib
import html
import importlib.metadata
import json
import mimetypes
import re
import sqlite3
import tempfile
import unicodedata
import zipfile
from pathlib import Path

import genanki

ID = re.compile(r"^[A-Za-z0-9_.:-]{1,100}$")
CLOZE = re.compile(r"\{\{c1::([^{}]+?)\}\}")
CSS = """.card {font-family: -apple-system, Arial, sans-serif; font-size: 22px;
text-align: left; line-height: 1.6; padding: 18px; color: #20252b; background: #fff;}
.extra,.sources {font-size: 15px; margin-top: 20px; color: #5b6470;}
.cloze {font-weight: bold; color: #1568b1;} img {max-width:100%; max-height:65vh;}
.nightMode .card {background:#1e2227; color:#e7e9ec;}
.nightMode .extra,.nightMode .sources {color:#b7bec7;}"""


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, label, empty=False):
    require(isinstance(value, str), f"{label}: expected string")
    require(empty or bool(value.strip()), f"{label}: empty")
    require(not any(c in value for c in ("\x00", "\x1f", "\x1e")), f"{label}: reserved control character")
    return value


def entities(items, label):
    require(isinstance(items, list) and bool(items), f"{label}: expected nonempty list")
    result = {}
    for item in items:
        require(isinstance(item, dict), f"{label}: expected objects")
        identity = item.get("id")
        require(isinstance(identity, str) and bool(ID.fullmatch(identity)), f"{label}: invalid ID {identity!r}")
        require(identity not in result, f"{label}: duplicate ID {identity}")
        result[identity] = item
    return result


def check_refs(refs, sources, label, evidence=False):
    require(isinstance(refs, list) and bool(refs), f"{label}: missing source_refs")
    for ref in refs:
        require(isinstance(ref, dict), f"{label}: invalid source ref")
        source = sources.get(ref.get("source_id"))
        require(source is not None, f"{label}: unknown source_id")
        pages = ref.get("pages")
        require(isinstance(pages, list) and bool(pages), f"{label}: pages required")
        require(all(type(p) is int and 1 <= p <= source["page_count"] for p in pages), f"{label}: page outside PDF")
        require(len(set(pages)) == len(pages), f"{label}: duplicate page number")
        if "page_labels" in ref:
            require(isinstance(ref["page_labels"], list) and len(ref["page_labels"]) == len(pages)
                    and all(isinstance(x, str) for x in ref["page_labels"]), f"{label}: bad page_labels")
        if evidence:
            text(ref.get("evidence"), f"{label}.evidence")


def normalized(value):
    # Preserve case and mathematical operators: x<y and x>y are different facts.
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip().rstrip("?。.!！")


def validate(data, base):
    require(isinstance(data, dict) and type(data.get("schema_version")) is int
            and data["schema_version"] == 1, "Expected schema_version 1 object")
    deck = data.get("deck")
    require(isinstance(deck, dict), "deck object required")
    require(isinstance(deck.get("id"), str) and bool(ID.fullmatch(deck["id"])), "Invalid deck.id")
    text(deck.get("name"), "deck.name")
    require(not any(c in deck["name"] for c in "\n\r\t"), "Invalid deck.name")
    sources = entities(data.get("sources"), "sources")
    for source in sources.values():
        text(source.get("title"), "source.title")
        require(type(source.get("page_count")) is int and source["page_count"] > 0, "source.page_count must be positive integer")
        require(isinstance(source.get("sha256"), str) and bool(re.fullmatch(r"[0-9a-f]{64}", source["sha256"])), "source.sha256 must be real lowercase PDF digest")
    concepts = entities(data.get("concepts"), "concepts")
    for concept in concepts.values():
        text(concept.get("title"), "concept.title")
        require(concept.get("disposition") in ("included", "excluded", "blocked"), "Bad concept disposition")
        if concept["disposition"] != "included":
            text(concept.get("reason"), "concept.reason")
        check_refs(concept.get("source_refs"), sources, f"concept {concept['id']}")
    cards = entities(data.get("cards"), "cards")
    covered, seen, warnings, media = set(), {}, [], {}
    for card in cards.values():
        label = f"card {card['id']}"
        require(card.get("type") in ("basic", "cloze"), f"{label}: type must be basic or cloze")
        q = text(card.get("question"), f"{label}.question")
        a = text(card.get("answer"), f"{label}.answer", empty=card["type"] == "cloze")
        if card["type"] == "cloze":
            matches = list(CLOZE.finditer(q))
            require(len(matches) == 1 and bool(matches[0].group(1).split("::", 1)[0].strip()), f"{label}: use exactly one nonempty c1 cloze")
            require("{{" not in CLOZE.sub("", q) and "}}" not in CLOZE.sub("", q), f"{label}: malformed or additional cloze")
            require(not a.strip(), f"{label}: cloze answer goes inside question; use explanation for extra")
        else:
            require(not re.search(r"\{\{c\d+::", q + a), f"{label}: Basic cannot contain cloze markup")
        key = normalized(q)
        require(key not in seen, f"{label}: duplicate question with {seen.get(key)}")
        seen[key] = card["id"]
        if q.count("?") + q.count("？") > 1:
            warnings.append({"card_id": card["id"], "code": "possible_multiple_recall_targets"})
        if len(a) > 450:
            warnings.append({"card_id": card["id"], "code": "long_answer_check_atomicity"})
        text(card.get("explanation", ""), f"{label}.explanation", empty=True)
        check_refs(card.get("source_refs"), sources, label, evidence=True)
        linked = card.get("concept_ids")
        require(isinstance(linked, list) and bool(linked) and all(isinstance(x, str) for x in linked), f"{label}: concept_ids required")
        for concept_id in linked:
            require(concept_id in concepts and concepts[concept_id]["disposition"] == "included", f"{label}: unknown or non-included concept")
            covered.add(concept_id)
        tags = card.get("tags", [])
        require(isinstance(tags, list) and all(isinstance(t, str) and t and not re.search(r"\s|[\x00-\x1f]", t) for t in tags), f"{label}: invalid tags")
        for side in ("front_media", "back_media"):
            refs = card.get(side, [])
            require(isinstance(refs, list), f"{label}: {side} must be a list")
            for value in refs:
                require(isinstance(value, str) and not Path(value).is_absolute(), f"{label}: media must be relative path")
                path = (base / value).resolve()
                require(path.is_relative_to(base) and path.is_file(), f"{label}: missing media or outside card directory: {value}")
                ext = path.suffix.lower()
                require(ext in (".png", ".jpg", ".jpeg", ".webp", ".gif"), f"{label}: unsupported media")
                raw = path.read_bytes()
                require(len(raw) < 30_000_000, f"{label}: media exceeds 30MB")
                name = "pdfanki_" + hashlib.sha256(raw).hexdigest() + ext
                media[value] = {"name": name, "path": path}
    missing = {c["id"] for c in concepts.values() if c["disposition"] == "included"} - covered
    require(not missing, f"Included concepts missing cards: {sorted(missing)}")
    return sources, concepts, list(cards.values()), warnings, media


def rich(value):
    return html.escape(value).replace("\n", "<br>")


def source_text(card, sources):
    lines = []
    for ref in card["source_refs"]:
        line = sources[ref["source_id"]]["title"] + " — PDF p." + ", ".join(map(str, ref["pages"]))
        if ref.get("page_labels"):
            line += " (printed: " + ", ".join(ref["page_labels"]) + ")"
        lines.append(line)
    return "\n".join(lines)


def pictures(card, side, media, embedded=False):
    result = []
    for value in card.get(side, []):
        entry = media[value]
        if embedded:
            mime = mimetypes.guess_type(entry["name"])[0] or "image/png"
            src = "data:" + mime + ";base64," + base64.b64encode(entry["path"].read_bytes()).decode()
        else:
            src = entry["name"]
        result.append('<img alt="Source illustration" src="' + html.escape(src, quote=True) + '">')
    return "<br>".join(result)


def models():
    # Schema-specific, fixed IDs; never change fields while reusing these IDs.
    basic = genanki.Model(1872164501, "PDF2Anki Basic v1",
        fields=[{"name": x} for x in ("Id", "Front", "Back", "Extra", "Sources")],
        templates=[{"name": "Recall", "qfmt": "{{Front}}", "afmt": '{{FrontSide}}<hr id="answer">{{Back}}<div class="extra">{{Extra}}</div><div class="sources">{{Sources}}</div>'}],
        css=CSS, sort_field_index=1)
    cloze = genanki.Model(1872164502, "PDF2Anki Cloze v1",
        fields=[{"name": x} for x in ("Id", "Text", "Extra", "Sources")],
        templates=[{"name": "Recall", "qfmt": "{{cloze:Text}}", "afmt": '{{cloze:Text}}<div class="extra">{{Extra}}</div><div class="sources">{{Sources}}</div>'}],
        css=CSS, model_type=genanki.Model.CLOZE, sort_field_index=1)
    return {"basic": basic, "cloze": cloze}


def verify_package(path, expected_guids, expected_media):
    with zipfile.ZipFile(path) as z:
        require(z.testzip() is None, "ZIP integrity failed")
        require("collection.anki2" in z.namelist() and "media" in z.namelist(), "Invalid APKG members")
        mapping = json.loads(z.read("media"))
        require(set(mapping.values()) == set(expected_media), "Packaged media differs from expected")
        require(all(k in z.namelist() for k in mapping), "Media bytes missing")
        with tempfile.TemporaryDirectory(prefix="pdfanki-verify-") as temp:
            db_path = Path(temp) / "collection.anki2"
            db_path.write_bytes(z.read("collection.anki2"))
            with sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True) as db:
                require(db.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "SQLite integrity failed")
                guids = {row[0] for row in db.execute("select guid from notes")}
                note_count = db.execute("select count(*) from notes").fetchone()[0]
                card_count = db.execute("select count(*) from cards").fetchone()[0]
                require(guids == set(expected_guids) and note_count == len(expected_guids), "Note identity/count mismatch")
                require(card_count == note_count, "Expected exactly one card per note")
                require(db.execute("select count(*) from cards where type != 0 or queue != 0 or reps != 0").fetchone()[0] == 0, "Unexpected review history")
                require(db.execute("select count(*) from cards c left join notes n on c.nid=n.id where n.id is null").fetchone()[0] == 0, "Orphan cards")
    return {"notes": note_count, "cards": card_count, "media": len(mapping), "zip_integrity": "passed", "sqlite_integrity": "passed", "new_cards_only": True}


def export(input_path, output):
    input_path, output = Path(input_path).resolve(), Path(output).resolve()
    require(not output.exists(), f"Output exists; choose a new directory: {output}")
    data = json.loads(input_path.read_text(encoding="utf-8"))
    sources, concepts, cards, warnings, media = validate(data, input_path.parent)
    model_map = models()
    deck_id = (int(hashlib.sha256(("pdf-to-anki-v1:" + data["deck"]["id"]).encode()).hexdigest()[:8], 16) % (1 << 30)) + (1 << 30)
    deck = genanki.Deck(deck_id, data["deck"]["name"])
    rows, guids, previews = [], [], []
    review = ["# " + data["deck"]["name"], "核对卡片来源、单一考点、答案与覆盖；自动校验不代替语义复核。"]
    for card in cards:
        guid = genanki.guid_for("pdf-to-anki-v1", data["deck"]["id"], card["id"])
        guids.append(guid)
        front = rich(card["question"]) + pictures(card, "front_media", media)
        back = rich(card["answer"]) + pictures(card, "back_media", media)
        extra = rich(card.get("explanation", ""))
        refs = source_text(card, sources)
        fields = [rich(card["id"]), front, back, extra, rich(refs)]
        if card["type"] == "cloze":
            fields = [rich(card["id"]), front, extra + back, rich(refs)]
        tags = card.get("tags", [])
        deck.add_note(genanki.Note(model=model_map[card["type"]], fields=fields, tags=tags, guid=guid))
        rows.append([model_map[card["type"]].name, rich(card["id"]), front, back, extra, rich(refs), " ".join(tags)])
        evidence = "\n".join(ref["evidence"] for ref in card["source_refs"])
        review += [f"\n## {card['id']} · {card['type']}", card["question"], "答案：" + (card["answer"] or "见填空目标"),
                   "补充：" + card.get("explanation", ""), "来源：" + refs, "证据：" + evidence]
        front_preview = rich(card["question"]) + pictures(card, "front_media", media, True)
        previews.append('<article><small>' + rich(card["id"] + " · " + card["type"]) + '</small><h3>' + front_preview +
                        '</h3><details open><summary>答案 / 补充</summary><p>' + rich(card["answer"] or "答案在填空目标中") +
                        pictures(card, "back_media", media, True) + '</p><p>' + extra + '</p></details><p class="sources">' +
                        rich(refs) + '</p><details><summary>来源证据</summary>' + rich(evidence) + '</details></article>')
    review += ["\n# 知识点覆盖"]
    for concept in concepts.values():
        review.append(f"- {concept['id']} · {concept['title']} · {concept['disposition']}" + ("：" + concept["reason"] if concept.get("reason") else ""))
    output.mkdir(parents=True)
    # Copy media into temporary staging under unique basenames, not user originals.
    with tempfile.TemporaryDirectory(prefix="pdfanki-media-") as temp:
        staged = {}
        for entry in media.values():
            target = Path(temp) / entry["name"]
            if target.name not in staged:
                target.write_bytes(entry["path"].read_bytes())
                staged[target.name] = str(target)
        package = genanki.Package(deck)
        package.media_files = list(staged.values())
        package.write_to_file(str(output / "deck.apkg"))
    verification = verify_package(output / "deck.apkg", guids, [entry["name"] for entry in media.values()])
    with (output / "cards.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["NoteType", "Id", "Front", "Back", "Extra", "Sources", "Tags"])
        writer.writerows(rows)
    (output / "review.md").write_text("\n\n".join(review), encoding="utf-8")
    document = ('<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'">'
                '<title>' + html.escape(data["deck"]["name"]) + '</title><style>body{font-family:system-ui,sans-serif;max-width:860px;margin:32px auto;padding:0 20px;background:#f5f7fa;color:#20252b;line-height:1.6}article{background:white;border:1px solid #dfe4eb;border-radius:12px;padding:22px;margin:18px 0}h3{font-size:20px;font-weight:600}img{max-width:100%;max-height:650px}.sources,small{color:#67727e;font-size:14px}summary{cursor:pointer}</style><h1>' +
                rich(data["deck"]["name"]) + '</h1><p>' + str(len(cards)) + ' notes / ' + str(len(cards)) + ' cards · 审阅稿（填空答案可见）</p>' + "\n".join(previews) + '</html>')
    (output / "review.html").write_text(document, encoding="utf-8")
    blocked = [c for c in concepts.values() if c["disposition"] == "blocked"]
    audit = {"schema_version": 1, "deck": data["deck"], "sources": list(sources.values()),
             "status": "PARTIAL_SOURCE_COVERAGE" if blocked else "STRUCTURAL_CHECKS_PASSED",
             "semantic_review": "Requires Agent/source review; not established by this script.",
             "warnings": warnings, "blocked_concepts": blocked,
             "excluded_concepts": [c for c in concepts.values() if c["disposition"] == "excluded"],
             "included_concept_count": sum(c["disposition"] == "included" for c in concepts.values()),
             "card_guids": {c["id"]: g for c, g in zip(cards, guids)}, "verification": verification,
             "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
             "apkg_sha256": hashlib.sha256((output / "deck.apkg").read_bytes()).hexdigest(),
             "versions": {name: importlib.metadata.version(name) for name in ("genanki", "PyMuPDF")}}
    (output / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"output": str(output), "status": audit["status"], **verification, "warnings": warnings}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cards_json", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(export(args.cards_json, args.out), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Error: {exc}\n")
