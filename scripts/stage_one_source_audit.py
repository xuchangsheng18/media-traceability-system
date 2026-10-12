"""Deterministic, read-only OOXML/content audit. No layout/approval claims."""
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
W = "{" + NS["w"] + "}"


def sha(value):
    return hashlib.sha256(value).hexdigest()


def compact(value):
    # Markdown escape and whitespace differences only; do not strip punctuation/numbers.
    return re.sub(r"[\s\\]", "", value)


def wtext(node):
    return "".join(t.text or "" for t in node.findall(".//w:t", NS))


def audit():
    inventory = json.loads((ROOT / "docs/00-project/source-inventory.json").read_text(encoding="utf-8"))
    cards = json.loads((ROOT / "tasks/source-task-cards.json").read_text(encoding="utf-8"))
    documents, task_checks = [], []
    for source in inventory:
        path = ROOT / source["path"]
        converted = "docs/_converted/" + {"original": "original", "revision": "revision", "guide": "guide"}[source["kind"]] + "/" + path.stem + ".md"
        target = (ROOT / converted).read_text(encoding="utf-8")
        target_text = compact(target)
        record = {"source": source["path"], "source_sha256": sha(path.read_bytes()),
                  "converted": converted, "converted_sha256": sha((ROOT / converted).read_bytes()),
                  "visual_layout_verified": False, "headings": [], "media": [], "gaps": []}
        assert record["source_sha256"] == source["sha256"], source["path"]
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if path.suffix == ".docx":
                document = ET.fromstring(archive.read("word/document.xml"))
                styles = ET.fromstring(archive.read("word/styles.xml"))
                style_names = {s.get(W + "styleId"): s.find("w:name", NS).get(W + "val")
                               for s in styles.findall("w:style", NS) if s.find("w:name", NS) is not None}
                paras = document.findall(".//w:p", NS)
                pnums = {id(p): i + 1 for i, p in enumerate(paras)}
                rows = []
                for index, paragraph in enumerate(paras, 1):
                    text = wtext(paragraph)
                    if not text.strip():
                        continue
                    prop = paragraph.find("w:pPr/w:pStyle", NS)
                    style = style_names.get(prop.get(W + "val"), "") if prop is not None else ""
                    classification = "GENERATED_TOC" if style.lower().startswith("toc ") else "BODY_TEXT"
                    matched = compact(text) in target_text
                    item = {"locator": f"word/document.xml#paragraph-{index}", "text_sha256": sha(text.encode()),
                            "style": style, "classification": classification, "present_in_markdown": matched}
                    if classification == "GENERATED_TOC" or not matched:
                        item["text"] = text
                    if not matched and classification != "GENERATED_TOC":
                        record["gaps"].append(item)
                    if style.lower().startswith("heading") or style.startswith("标题"):
                        record["headings"].append({"locator": item["locator"], "text": text, "style": style})
                    rows.append(item)
                # Some source files use custom styles: exact Markdown heading matches identify their paragraphs.
                known = {h["locator"] for h in record["headings"]}
                for match in re.finditer(r"^#{1,6} ([^\n]+)$", target, re.M):
                    heading = match.group(1).strip()
                    candidates = [(i, p) for i, p in enumerate(paras, 1) if compact(wtext(p)) == compact(heading)]
                    for index, paragraph in candidates:
                        locator = f"word/document.xml#paragraph-{index}"
                        entry = next((r for r in rows if r["locator"] == locator), None)
                        if locator not in known and entry and entry["classification"] != "GENERATED_TOC":
                            record["headings"].append({"locator": locator, "text": wtext(paragraph),
                                                       "style": entry["style"], "identified_by": "exact_converted_heading"})
                            known.add(locator)
                            break
                table_records = []
                for index, table in enumerate(document.findall(".//w:tbl", NS), 1):
                    cells = []
                    for row_number, row in enumerate(table.findall("w:tr", NS), 1):
                        for col_number, cell in enumerate(row.findall("w:tc", NS), 1):
                            text = wtext(cell)
                            cells.append({"row": row_number, "column": col_number, "text_sha256": sha(text.encode()),
                                          "paragraph_numbers": [pnums[id(p)] for p in cell.findall(".//w:p", NS)],
                                          "present_in_markdown": not text.strip() or compact(text) in target_text})
                    table_records.append({"locator": f"word/document.xml#table-{index}",
                                          "row_count": len(table.findall("w:tr", NS)), "cells": cells})
                link_fields = []
                for number, paragraph in enumerate(paras, 1):
                    instruction = "".join(p.text or "" for p in paragraph.findall(".//w:instrText", NS)).strip()
                    if "HYPERLINK" in instruction.upper():
                        targets = re.findall(r'HYPERLINK\s+"([^"]+)"', instruction, re.I)
                        link_fields.append({"locator": f"word/document.xml#paragraph-{number}",
                                            "instruction": instruction, "targets": targets,
                                            "targets_present_in_markdown": all(compact(t) in target_text for t in targets)})
                links = []
                rels_name = "word/_rels/document.xml.rels"
                if rels_name in names:
                    for relation in ET.fromstring(archive.read(rels_name)):
                        if relation.get("Type", "").endswith("/hyperlink"):
                            links.append(relation.get("Target"))
                comment_rows = []
                if "word/comments.xml" in names:
                    for comment in ET.fromstring(archive.read("word/comments.xml")).findall("w:comment", NS):
                        text = wtext(comment)
                        comment_rows.append({"id": comment.get(W + "id"), "locator": "word/comments.xml#comment-" + comment.get(W + "id"), "text": text,
                                             "present_in_markdown": not text.strip() or compact(text) in target_text})
                auxiliary = []
                for name in names:
                    if re.match(r"word/(header\d+|footer\d+|footnotes|endnotes)\.xml$", name):
                        xml = ET.fromstring(archive.read(name))
                        auxiliary.append({"part": name, "text_paragraphs": [wtext(p) for p in xml.findall(".//w:p", NS) if wtext(p).strip()],
                                          "field_instructions": [p.text or "" for p in xml.findall(".//w:instrText", NS)]})
                record.update(kind="WORD", paragraphs_total=len(paras), paragraphs_nonempty=len(rows),
                              paragraphs=rows, tables=table_records, hyperlink_field_instructions=link_fields,
                              hyperlink_relationship_targets=links, comments=comment_rows, auxiliary_parts=auxiliary,
                              omml_equations=len(document.findall(".//m:oMath", NS)),
                              merged_cell_markers=len(document.findall(".//w:gridSpan", NS)) + len(document.findall(".//w:vMerge", NS)))
                if "项目任务书_技术修订版V1.3" in path.name:
                    current = None
                    for child in document.find("w:body", NS):
                        if child.tag == W + "p":
                            found = re.match(r"^(T\d{3})\s+(.+)$", wtext(child))
                            if found:
                                current = (found.group(1), found.group(2), pnums[id(child)])
                        elif child.tag == W + "tbl" and current:
                            pairs = [[wtext(c) for c in row.findall("w:tc", NS)] for row in child.findall("w:tr", NS)]
                            if len(pairs) == 10 and all(len(p) == 2 for p in pairs) and pairs[0][0] == "责任角色":
                                task_id, title, number = current
                                values = dict(pairs)
                                task_checks.append({"task_id": task_id, "source": source["path"],
                                                    "locator": f"word/document.xml#paragraph-{number}",
                                                    "fields_checked": len(values), "name_matches": cards[task_id]["name"] == title,
                                                    "fields_match": cards[task_id]["fields"] == values,
                                                    "source_fields_sha256": sha(json.dumps(values, ensure_ascii=False, sort_keys=True).encode())})
            else:
                slides = []
                slide_paths = sorted((n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)), key=lambda n: int(re.search(r"slide(\d+)", n).group(1)))
                for index, name in enumerate(slide_paths, 1):
                    xml = ET.fromstring(archive.read(name))
                    page = re.search(rf"^## 第{index}页\n(.*?)(?=^## 第\d+页\n|\Z)", target, re.M | re.S)
                    page_text = compact(page.group(1)) if page else ""
                    shapes = []
                    for shape in xml.findall(".//p:sp", NS):
                        prop = shape.find("p:nvSpPr/p:cNvPr", NS)
                        texts = ["".join(t.text or "" for t in p.findall(".//a:t", NS)) for p in shape.findall(".//a:p", NS)]
                        transform = shape.find("p:spPr/a:xfrm", NS)
                        geometry = {node.tag.rsplit("}", 1)[-1]: dict(node.attrib) for node in transform} if transform is not None else {}
                        shapes.append({"shape_id": prop.get("id") if prop is not None else None,
                                       "name": prop.get("name") if prop is not None else None, "geometry_emu": geometry,
                                       "paragraphs": texts, "text_present_in_markdown": all(not t.strip() or compact(t) in page_text for t in texts)})
                    notes_path = f"ppt/notesSlides/notesSlide{index}.xml"
                    notes = [t.text or "" for t in ET.fromstring(archive.read(notes_path)).findall(".//a:t", NS)] if notes_path in names else []
                    slides.append({"slide": index, "locator": name, "shapes": shapes, "notes_text": notes,
                                   "all_xml_text_present_in_markdown": all(not (t.text or "").strip() or compact(t.text) in page_text for t in xml.findall(".//a:t", NS))})
                    record["headings"].append({"locator": name, "text": f"第{index}页界面原型", "style": "slide"})
                record.update(kind="POWERPOINT", slides=slides, slide_count=len(slides))
            for name in names:
                if re.match(r"(word|ppt)/media/", name):
                    digest = sha(archive.read(name))
                    matches = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "docs/assets/source").rglob("*") if p.is_file() and sha(p.read_bytes()) == digest)
                    record["media"].append({"zip_part": name, "sha256": digest, "exact_repository_copies": matches})
        documents.append(record)
    word = [d for d in documents if d["kind"] == "WORD"]
    ppt = [d for d in documents if d["kind"] == "POWERPOINT"]
    return {"revision": "stage-one-content-audit-20261012", "status": "CONTENT_STRUCTURALLY_AUDITED_NOT_APPROVED",
            "method": "normalized_text_presence_with_exact_source_locators_not_order_or_visual_equivalence",
            "documents": documents, "task_source_field_checks": task_checks,
            "task_cards_sha256": sha((ROOT / "tasks/source-task-cards.json").read_bytes()),
            "summary": {"source_files": len(documents), "word_files": len(word), "word_paragraphs": sum(d["paragraphs_total"] for d in word),
                        "word_tables": sum(len(d["tables"]) for d in word), "ppt_slides": sum(d["slide_count"] for d in ppt),
                        "generated_TOC_paragraphs_omitted_from_markdown": sum(1 for d in word for p in d["paragraphs"] if p["classification"] == "GENERATED_TOC" and not p["present_in_markdown"]),
                        "unexplained_body_text_gaps": sum(len(d["gaps"]) for d in word),
                        "task_cards_checked": len(task_checks), "task_fields_checked": sum(t["fields_checked"] for t in task_checks)},
            "formal_frozen": False, "visual_layout_verified": False}


if __name__ == "__main__":
    result = audit()
    output = ROOT / "docs/00-project/stage-one/source-content-audit.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result["summary"], ensure_ascii=False))
