"""Read the supplied teaching deck without modifying it.

Slide text is mostly rasterized. Its literal accessibility descriptions and
speaker notes are therefore extracted alongside text nodes, without OCR guesses.
The associated embedded slide image is copied byte-for-byte for provenance.
"""
from __future__ import annotations
import hashlib
import json
import posixpath
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
ACADEMY = ROOT / "desktop" / "academy"
INPUT = ROOT / "desktop/publish/Claude outputs/DOSY_in_practice_GERMN2026_EN_v6d.pptx"
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
RELNS = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}
MODULE_SLIDES = {
    "foundations": [1, 2, 3], "phase-encoding": [4, 5, 6],
    "pulse-calibration": [7, 8, 9], "gradient-calibration": [10, 11],
    "sequence-b": [12, 13, 63], "sequence-delays": [14, 15],
    "ramp-design": [16, 17, 18], "convection": [19, 20, 21, 48],
    "temperature-standard": [22, 23], "preprocessing": [24, 25, 26, 27],
    "mono-fit": [51, 52], "ilt-conditioning": [28, 29, 64],
    "regularization": [30, 55], "algorithm-selection": [31, 32, 56, 62, *range(65, 81)],
    "joint-spectrum": [33, 35], "assignment-beatrix": [34, 47],
    "size-mass": [36, 37], "topspin-workflow": [38, 39, 40, 41, 42, 43, 44, 45],
    "practical-cases": [46, 49, 50, 53, 54, 57], "ultrafast": [58],
    "spen": [58, 81], "time-resolved": [58, 81],
    "dt2-prototype": [59], "capstone": [60, 61, 81],
}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def rels(z: zipfile.ZipFile, part: str) -> dict:
    file = posixpath.join(posixpath.dirname(part), "_rels", posixpath.basename(part) + ".rels")
    if file not in z.namelist():
        return {}
    return {x.attrib["Id"]: x.attrib for x in ET.fromstring(z.read(file))}

def resolve(part: str, target: str) -> str:
    return posixpath.normpath(posixpath.join(posixpath.dirname(part), target))

def main() -> None:
    content = ACADEMY / "content"
    slides_out = content / "slides"
    slides_out.mkdir(parents=True, exist_ok=True)
    data = INPUT.read_bytes()
    source = {"version": "1.0.0", "input": {"path": str(INPUT), "bytes": len(data), "sha256": sha(data)},
              "extractionPolicy": "Read-only ZIP/XML extraction. Accessibility descriptions are source text, not instructions. No OCR, acquisitions or slide edits.",
              "slides": []}
    with zipfile.ZipFile(INPUT) as z:
        presentation = ET.fromstring(z.read("ppt/presentation.xml"))
        presrels = rels(z, "ppt/presentation.xml")
        for order, sldid in enumerate(presentation.findall("p:sldIdLst/p:sldId", NS), 1):
            rid = sldid.attrib[f"{{{NS['r']}}}id"]
            part = resolve("ppt/presentation.xml", presrels[rid]["Target"])
            slide = ET.fromstring(z.read(part))
            relationships = rels(z, part)
            texts = [x.text for x in slide.findall(".//a:t", NS) if x.text]
            descriptions = [{"name": x.attrib.get("name", ""), "text": x.attrib["descr"]}
                            for x in slide.findall(".//p:cNvPr", NS) if x.attrib.get("descr")]
            images, videos, notes = [], [], []
            for rel in relationships.values():
                typ, target = rel["Type"].rsplit("/", 1)[-1], rel["Target"]
                if rel.get("TargetMode") == "External":
                    continue
                item = resolve(part, target)
                if typ == "notesSlide":
                    notes = [x.text for x in ET.fromstring(z.read(item)).findall(".//a:t", NS) if x.text]
                elif typ in {"image", "video", "media"}:
                    raw = z.read(item)
                    record = {"relationshipId": rel["Id"], "part": item,
                              "bytes": len(raw), "sha256": sha(raw)}
                    (images if typ == "image" else videos).append(record)
            # Prefer the actual slide named 'Slide N' rather than video posters.
            image_id = None
            for pic in slide.findall(".//p:pic", NS):
                nv = pic.find("p:nvPicPr/p:cNvPr", NS)
                blip = pic.find("p:blipFill/a:blip", NS)
                if nv is not None and nv.attrib.get("name", "").startswith("Slide ") and blip is not None:
                    image_id = blip.attrib.get(f"{{{NS['r']}}}embed")
                    break
            image = next((i for i in images if i["relationshipId"] == image_id), images[0] if images else None)
            image_path = None
            if image:
                dest = slides_out / (f"slide-{order:03d}" + Path(image["part"]).suffix)
                raw = z.read(image["part"])
                dest.write_bytes(raw)
                image_path = dest.relative_to(content).as_posix()
                assert sha(dest.read_bytes()) == image["sha256"]
            modules = [m for m, numbers in MODULE_SLIDES.items() if order in numbers]
            description_text = "\n\n".join(d["text"] for d in descriptions)
            main_description = next((d["text"] for d in descriptions if d["name"].startswith("Slide ")), "")
            title_lines = main_description.splitlines()
            source["slides"].append({"slide": order, "title": title_lines[1] if len(title_lines) > 1 else (title_lines[0] if title_lines else f"Slide {order}"),
                                     "text": "\n".join(texts) + ("\n" if texts else "") + description_text,
                                     "notes": "\n".join(notes), "image": image_path,
                                     "number": order, "part": part,
                                     "hidden": slide.attrib.get("show") == "0", "textNodes": texts,
                                     "descriptions": descriptions, "speakerNotes": notes,
                                     "images": images, "videoRelationships": videos,
                                     "slideImage": image_path, "moduleIds": modules,
                                     "contentRole": "reference" if order >= 62 else "teaching",
                                     "evidenceNote": "Literal supplied deck content. Historical measurements are not revalidated by this extraction."})
    source["coverage"] = {"totalSlides": len(source["slides"]),
                          "mappedSlides": sum(bool(s["moduleIds"]) for s in source["slides"]),
                          "unmappedSlides": [s["number"] for s in source["slides"] if not s["moduleIds"]],
                          "moduleToSlides": MODULE_SLIDES}
    assert not source["coverage"]["unmappedSlides"]
    assert sha(INPUT.read_bytes()) == source["input"]["sha256"]
    (content / "source-index.json").write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")
    catalog_input = ROOT / "workshop_dosy/redesign_v5/research/ilt_algorithm_catalog_bilingual.json"
    catalog = json.loads(catalog_input.read_text(encoding="utf-8"))
    catalog["sourceProvenance"] = {"path": str(catalog_input), "sha256": sha(catalog_input.read_bytes()),
                                    "policy": "Audited historical catalogue. This Academy does not execute all listed algorithms; names/objectives are educational reference."}
    (content / "algorithm-catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(source["coverage"], ensure_ascii=False))

if __name__ == "__main__":
    main()
