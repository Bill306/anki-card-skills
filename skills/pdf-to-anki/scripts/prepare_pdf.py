#!/usr/bin/env python3
"""Extract page-anchored text and render review images. No model or network calls."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import pymupdf


def select_pages(value, total):
    if value == "all":
        return list(range(1, total + 1))
    result = set()
    for part in value.split(","):
        parts = part.strip().split("-")
        if len(parts) == 1:
            start = end = int(parts[0])
        elif len(parts) == 2:
            start, end = map(int, parts)
        else:
            raise ValueError("Pages must be 'all' or e.g. 1-3,5")
        if start < 1 or end < start or end > total:
            raise ValueError(f"Page range outside 1..{total}: {part}")
        result.update(range(start, end + 1))
    if not result:
        raise ValueError("No pages selected")
    return sorted(result)


def prepare(pdf_path, output, page_selection="all", dpi=110):
    pdf_path, output = Path(pdf_path).resolve(), Path(output).resolve()
    if not 50 <= dpi <= 240:
        raise ValueError("Use DPI between 50 and 240")
    if output.exists():
        raise ValueError(f"Output exists; choose a new directory: {output}")
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    with pymupdf.open(pdf_path) as doc:
        if not doc.is_pdf or doc.needs_pass:
            raise ValueError("Input must be an accessible, unencrypted PDF")
        selected = select_pages(page_selection, len(doc))
        source_id = "pdf-" + digest[:16]
        output.mkdir(parents=True)
        (output / "pages").mkdir()
        pages = []
        for number in selected:
            page = doc[number - 1]
            text = page.get_text("text", sort=True)
            count = len("".join(text.split()))
            images = len(page.get_images())
            paths = len(page.get_drawings())
            flags = []
            if count < 40:
                flags.append("sparse_text_check_scan_or_diagram")
            if text.count("\ufffd") > max(2, len(text) * 0.01):
                flags.append("text_encoding_needs_visual_review")
            if images or paths:
                flags.append("contains_images_or_vectors_check_visuals")
            # Bound raster size for unusually large pages while keeping all pages.
            scale = min(dpi / 72, math.sqrt(12_000_000 / max(1, page.rect.width * page.rect.height)))
            name = f"pages/{source_id}-p{number:04d}.png"
            page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False).save(output / name)
            pages.append({"pdf_page": number, "page_label": page.get_label(),
                          "text": text, "text_chars": count, "image_count": images,
                          "vector_path_count": paths, "flags": flags, "render_path": name})
        result = {"schema_version": 1, "id": source_id, "title": pdf_path.stem,
                  "filename": pdf_path.name, "sha256": digest, "page_count": len(doc),
                  "selected_pages": selected, "pages": pages,
                  "notice": "Extraction is not OCR and does not verify visual reading order. Inspect rendered pages."}
    (output / "source.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [f"# {result['title']}", f"Source ID: {source_id}", f"SHA256: {digest}"]
    for page in pages:
        md += [f"\n## PDF p.{page['pdf_page']} (label: {page['page_label']})",
               "Flags: " + (", ".join(page["flags"]) or "none; visual review still needed"), page["text"]]
    (output / "source.md").write_text("\n\n".join(md), encoding="utf-8")
    return {"source_id": source_id, "page_count": result["page_count"],
            "selected_pages": selected, "flagged_pages": [p["pdf_page"] for p in pages if p["flags"]],
            "source_manifest": str(output / "source.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--pages", default="all")
    parser.add_argument("--dpi", default=110, type=int)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.pdf, args.out, args.pages, args.dpi), ensure_ascii=False, indent=2))
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(2, f"Error: {exc}\n")
