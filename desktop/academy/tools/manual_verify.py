"""Render every manual page and record structural/text/bounds verification."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
import pdfplumber
from pypdf import PdfReader
from PIL import Image,ImageDraw

BASE = Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument("--render-dir",type=Path,default=BASE/"docs/qa/manual-pages")
parser.add_argument("--pdftoppm", default=os.environ.get("ACADEMY_PDFTOPPM") or shutil.which("pdftoppm") or "pdftoppm", help="Poppler pdftoppm executable; also accepts ACADEMY_PDFTOPPM or PATH")
args=parser.parse_args();POPLER=Path(args.pdftoppm)
args.render_dir.mkdir(parents=True,exist_ok=True)
report={"checks":[],"manuals":[],"evidenceBoundary":"Structural and text bounds checks plus complete Poppler rendering. Visual review of page PNGs is recorded separately; not hardware/student/LLM validation."}
def check(name,value):report["checks"].append({"name":name,"passed":bool(value)})
for lang in ("ES","EN"):
    path=BASE/f"docs/MANUAL_{lang}.pdf";reader=PdfReader(path);text="\n".join(p.extract_text() or "" for p in reader.pages)
    check(lang+" readable complete manual",len(reader.pages)>=12 and len(text)>12000)
    check(lang+" no replacement glyphs",not any(c in text for c in ("\ufffd","\u25a0")))
    check(lang+" required lessons",all(s in text for s in ("22", "11", "Beatrix", "SPEN", "ILT", "TTMS", "NO-GO")))
    check(lang+" title and provenance", "DiffAtOnce Academy" in text and "SHA-256" in text)
    bad=[]
    with pdfplumber.open(path) as pdf:
        for number,page in enumerate(pdf.pages,1):
            for w in page.extract_words():
                if w["x0"]<10 or w["x1"]>page.width-10 or w["top"]<8 or w["bottom"]>page.height-8:bad.append({"page":number,"word":w["text"],"rect":[w["x0"],w["top"],w["x1"],w["bottom"]]})
    check(lang+" text inside page",not bad)
    prefix=args.render_dir/f"MANUAL_{lang}"
    # These are this verifier's generated PNGs only, never original captures.
    for stale in args.render_dir.glob(f"MANUAL_{lang}-*.png"):
        if stale.parent.resolve()!=args.render_dir.resolve():raise ValueError("Render cleanup escaped its target directory")
        stale.unlink()
    subprocess.run([str(POPLER),"-r","90","-png",str(path),str(prefix)],check=True,capture_output=True)
    renders=sorted(args.render_dir.glob(f"MANUAL_{lang}-*.png"))
    check(lang+" all pages rendered",len(renders)==len(reader.pages))
    sheets=[]
    for start in range(0,len(renders),4):
        image=Image.new("RGB",(1240,1780),"#dce7e9");draw=ImageDraw.Draw(image)
        for j,p in enumerate(renders[start:start+4]):
            im=Image.open(p).convert("RGB");im.thumbnail((595,845))
            x=15+(j%2)*620;y=25+(j//2)*890;image.paste(im,(x,y));draw.text((x,y-17),p.name,fill="#15343e")
        out=args.render_dir/f"contact-{lang}-{start//4+1}.png";image.save(out);sheets.append(str(out))
    report["manuals"].append({"path":str(path),"pages":len(reader.pages),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"renderedPages":[str(p) for p in renders],"contactSheets":sheets,"boundsIssues":bad})
report["passed"]=sum(c["passed"] for c in report["checks"]);report["failed"]=sum(not c["passed"] for c in report["checks"])
(BASE/"docs/manual-verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"passed":report["passed"],"failed":report["failed"],"pages":[{"lang":l,"pages":m["pages"]} for l,m in zip(("ES","EN"),report["manuals"])]},indent=2))
if report["failed"]:raise SystemExit(1)
