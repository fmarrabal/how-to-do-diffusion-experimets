"""Prepare a public copy of the supplied bilingual workshop archive.

Standard library only. Originals are read-only. Presentation rendering, media,
charts and slide geometry remain byte-for-byte unchanged. Only textual local
paths in speaker notes are replaced. This is not a PowerPoint re-export.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
LOCAL = re.compile(r"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/])(?!/)[^\s<>\"'|;,\)\]]+")
SERIAL = re.compile(r"\bZ\d{6}_\d{4}\b")
EXCLUDE = {
    "MANIFEST_SHA256.json", "DOSY_Consola_Bruker_v2.zip",
    "DOSY_Consola_Bruker_v3.zip", "Generador_rampas_DOSY_TopSpin.zip",
    "Fuentes/casos/prepare_case_assets.py",
    "Fuentes/casos/HDO_integral_offline/replay_integral_calibration.py",
    "Fuentes/simulaciones/v5/make_parameter_visuals.py",
    "Fuentes/simulaciones/v5/ilt_visuals.py",
    "Fuentes/simulaciones/v6/problem_simulations.py",
    "Fuentes/simulaciones/v6/convection_toy_model.py",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sanitize(text):
    def replace(match):
        path = match.group(0).replace("\\", "/")
        if "/Bruker/TopSpin3.8.0/" in path:
            return "<TopSpin>/" + path.split("/TopSpin3.8.0/", 1)[1]
        name = path.rstrip("/").rsplit("/", 1)[-1]
        return "[local-source: " + name + "]"
    return SERIAL.sub("[probe serial omitted]", LOCAL.sub(replace, text))


def sanitize_json(value):
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            public_key = sanitize(key)
            if public_key in result:
                public_key += " [source-id: " + sha(key.encode("utf-8"))[:12] + "]"
            if public_key in result:
                raise ValueError("Ambiguous public provenance key")
            result[public_key] = sanitize_json(item)
        assert len(result) == len(value)
        return result
    if isinstance(value, list):
        return [sanitize_json(item) for item in value]
    return sanitize(value) if isinstance(value, str) else value


def public_deck(data):
    """Rewrite note text only; all other OPC entries must be identical."""
    changed = []
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as src, zipfile.ZipFile(out, "w") as dst:
        for info in src.infolist():
            content = src.read(info.filename)
            if info.filename.startswith("ppt/notesSlides/") and info.filename.endswith(".xml"):
                original = content
                # Operate inside a:t text nodes without rewriting namespaces or
                # relationships. XML escapes are respected by ElementTree checks.
                text = content.decode("utf-8")
                text = re.sub(
                    r"(<a:t(?:\s[^>]*)?>)(.*?)(</a:t>)",
                    lambda m: m[1] + sanitize(m[2]).replace("<TopSpin>", "&lt;TopSpin&gt;") + m[3],
                    text, flags=re.S,
                )
                content = text.encode("utf-8")
                ET.fromstring(content)
                if content != original:
                    changed.append(info.filename)
            dst.writestr(info, content)
    result = out.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as src, zipfile.ZipFile(io.BytesIO(result)) as dst:
        assert src.namelist() == dst.namelist()
        assert dst.testzip() is None
        for name in src.namelist():
            if name not in changed:
                assert src.read(name) == dst.read(name), name
        assert not any(LOCAL.search(dst.read(name).decode("utf-8")) for name in changed)
    return result, changed


def resolve(part, target):
    return target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(posixpath.dirname(part), target))


def relationships(archive, part):
    directory, filename = posixpath.split(part)
    name = posixpath.join(directory, "_rels", filename + ".rels")
    if name not in archive.namelist():
        return {}
    return {rel.get("Id"): rel for rel in ET.fromstring(archive.read(name))}


def paragraphs(element):
    return ["".join(node.text or "" for node in paragraph.findall(".//a:t", NS))
            for paragraph in element.findall(".//a:p", NS)]


def markdown_text(text):
    # Show literal placeholders such as <TopSpin> rather than interpreting
    # them as HTML. This affects only the Markdown transcript, not the deck.
    return text.replace("<", "&lt;").replace(">", "&gt;")


def export_content(data, language, story, output):
    """Expose every slide, its tables/charts, media, and full notes in Markdown."""
    translated = language == "es"
    title = "Contenido completo de las presentaciones" if translated else "Complete presentation content"
    lines = ["# " + title, "", "[English](../en/presentation-content.md) · [Español](../es/presentation-content.md)", "",
             ("45 diapositivas: 25 principales y 20 apéndices ocultos. Texto y notas extraídos de la edición pública del PPTX. El PowerPoint conserva los gráficos editables y vídeos."
              if translated else "45 slides: 25 main slides and 20 hidden appendices. Text and notes are extracted from the public PPTX. PowerPoint retains editable charts and videos."), ""]
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        part = "ppt/presentation.xml"
        rels = relationships(archive, part)
        slide_ids = ET.fromstring(archive.read(part)).findall("p:sldIdLst/p:sldId", NS)
        assert len(slide_ids) == 45
        image_files = {}
        for number, sid in enumerate(slide_ids, 1):
            slide_part = resolve(part, rels[sid.get("{" + NS["r"] + "}id")].get("Target"))
            slide = ET.fromstring(archive.read(slide_part))
            sr = relationships(archive, slide_part)
            hidden = slide.get("show", "1") == "0"
            assert hidden == (number > 25)
            heading = story["slides"][number - 1]["title_" + language]
            lines += ["## %02d. %s" % (number, heading), "",
                      ("Apéndice oculto" if translated else "Hidden appendix") if hidden else
                      ("Diapositiva principal" if translated else "Main slide"), ""]
            lines += ["### " + ("Texto de la diapositiva" if translated else "Slide text"), ""]
            for text in paragraphs(slide):
                if text.strip():
                    lines += [markdown_text(text).replace("\n", "  \n"), ""]
            # Cached chart values remain explicit even when the chart is a
            # native editable object rather than drawing text.
            for rel in sr.values():
                rel_type = rel.get("Type", "")
                target = resolve(slide_part, rel.get("Target"))
                if rel_type.endswith("/chart"):
                    chart = ET.fromstring(archive.read(target))
                    c = {"c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}
                    lines += ["### " + ("Valores del gráfico" if translated else "Chart values"), ""]
                    for series in chart.findall(".//c:ser", c):
                        for block in list(series):
                            values = [v.text or "" for v in block.findall(".//c:v", c)]
                            if values:
                                lines += ["- " + block.tag.rsplit("}", 1)[-1] + ": " + ", ".join(values)]
                    lines += [""]
                if rel_type.endswith("/image") or rel_type.endswith("/video"):
                    content = archive.read(target)
                    extension = PurePosixPath(target).suffix.lower()
                    asset = sha(content)[:20] + extension
                    if asset not in image_files:
                        dest = output / "presentations/assets" / asset
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(content)
                        image_files[asset] = True
                    url = "../../presentations/assets/" + asset
                    if extension in (".png", ".jpg", ".jpeg", ".gif"):
                        lines += ["![%s %d](%s)" % ("Figura" if translated else "Figure", number, url), ""]
                    else:
                        lines += ["[%s %d](%s)" % ("Vídeo o recurso" if translated else "Video or asset", number, url), ""]
            note_rel = next((rel for rel in sr.values() if rel.get("Type", "").endswith("/notesSlide")), None)
            assert note_rel is not None
            note = ET.fromstring(archive.read(resolve(slide_part, note_rel.get("Target"))))
            notes = []
            for shape in note.findall(".//p:sp", NS):
                placeholder = shape.find(".//p:ph", NS)
                if placeholder is not None and placeholder.get("type") == "body":
                    notes.extend(paragraphs(shape))
            assert any(text.strip() for text in notes)
            lines += ["### " + ("Notas completas del ponente" if translated else "Full speaker notes"), ""]
            for text in notes:
                if text.strip():
                    lines += [markdown_text(text).rstrip(), ""]
    return "\n".join(lines).rstrip() + "\n"


def mapped_name(name):
    if name.startswith("Presentaciones/"):
        lang = "es" if "_ES_" in name else "en"
        return "presentations/%s/workshop-%s.pptx" % (lang, lang)
    if name.startswith("PDF/"):
        lang = "es" if "_ES_" in name else "en"
        return "presentations/%s/workshop-%s.pdf" % (lang, lang)
    if name.startswith("media/"):
        return "presentations/" + name
    if name.startswith("Fuentes/"):
        return "materials/" + name[len("Fuentes/"):]
    return "materials/presenter/" + name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--replace-generated", action="store_true", help="After review, replace only the known archive-derived files in --out")
    args = parser.parse_args()
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source = args.archive.read_bytes()
    records = []
    notes_changes = {}
    with zipfile.ZipFile(io.BytesIO(source)) as archive:
        # This file list is the reviewed v8 teaching release, not a recursive
        # export of the research workspace.
        assert len(archive.namelist()) == 75
        for name in archive.namelist():
            if name in EXCLUDE:
                continue
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("Unsafe archive path")
            content = archive.read(name)
            original_sha = sha(content)
            suffix = path.suffix.lower()
            if suffix == ".pptx":
                content, changed = public_deck(content)
                notes_changes[mapped_name(name)] = changed
            elif suffix == ".json":
                public = sanitize_json(json.loads(content.decode("utf-8-sig")))
                content = (json.dumps(public, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            elif suffix in (".txt", ".csv", ".html"):
                text = sanitize(content.decode("utf-8-sig")).replace("\r\n", "\n").replace("\r", "\n")
                if suffix == ".txt":
                    text = "\n".join(line.rstrip() for line in text.split("\n"))
                content = text.encode("utf-8")
            dest = output / mapped_name(name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists() and dest.read_bytes() != content and not args.replace_generated:
                raise ValueError("Destination differs; preserve or review it before rebuilding: " + mapped_name(name))
            dest.write_bytes(content)
            records.append({"file": mapped_name(name), "source_member": name,
                            "source_sha256": original_sha, "public_sha256": sha(content),
                            "bytes": len(content), "changed": sha(content) != original_sha})
    story = json.loads((output / "materials/story.json").read_text(encoding="utf-8"))
    for language in ("en", "es"):
        data = (output / ("presentations/%s/workshop-%s.pptx" % (language, language))).read_bytes()
        text = export_content(data, language, story, output)
        dest = output / "docs" / language / "presentation-content.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(text.encode("utf-8"))
    manifest = {"schema_version": 1, "source_release": "bilingual workshop v8",
                "source_archive_sha256": sha(source), "slides_each": 45,
                "main_each": 25, "hidden_each": 20, "embedded_videos_each": 7,
                "changes": "Local paths in notes/text and probe serial in metadata omitted. Public text line endings are normalized LF. Slide/media/chart bytes remain unchanged. Original PDF and raster labels remain unchanged.",
                "slides_unchanged": True, "source_files_modified": False,
                "note_parts_modified": notes_changes,
                "excluded": sorted(EXCLUDE), "files": records}
    dest = output / "provenance/presentation-manifest.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"files": len(records), "slides_each": 45, "originals_modified": False,
                      "notes_parts_changed": {name: len(parts) for name, parts in notes_changes.items()}}))


if __name__ == "__main__":
    main()
