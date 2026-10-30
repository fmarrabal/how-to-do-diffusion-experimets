"""Read-only comparison of the current supplied PPTX with the frozen extraction.

Never rewrites the PPTX, extracted slides, source-index or course. The additive
report distinguishes package byte identity from observed teaching-content
identity. An appended empty ZIP footer can be tested without changing input.
"""
import hashlib
import io
import json
import posixpath
import struct
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[1]
INDEX=BASE/"content/source-index.json"
NS={"a":"http://schemas.openxmlformats.org/drawingml/2006/main",
    "p":"http://schemas.openxmlformats.org/presentationml/2006/main",
    "r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
def sha(data):return hashlib.sha256(data).hexdigest()
def resolve(part,target):return posixpath.normpath(posixpath.join(posixpath.dirname(part),target))
def rels(z,part):
    name=posixpath.join(posixpath.dirname(part),"_rels",posixpath.basename(part)+".rels")
    return {} if name not in z.namelist() else {r.attrib["Id"]:r.attrib for r in ET.fromstring(z.read(name))}

def main():
    snapshot=json.loads(INDEX.read_text(encoding="utf-8"));path=Path(snapshot["input"]["path"])
    data=path.read_bytes();rows=[];checks=[];archive=[]
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        pr=rels(z,"ppt/presentation.xml")
        parts=[resolve("ppt/presentation.xml",pr[n.attrib[f"{{{NS['r']}}}id"]]["Target"])
               for n in ET.fromstring(z.read("ppt/presentation.xml")).findall("p:sldIdLst/p:sldId",NS)]
        checks.append({"name":"slide-count", "passed":len(parts)==len(snapshot["slides"]),"current":len(parts),"snapshot":len(snapshot["slides"])})
        for old,part in zip(snapshot["slides"],parts):
            slide=ET.fromstring(z.read(part));rr=rels(z,part)
            texts=[n.text for n in slide.findall(".//a:t",NS) if n.text]
            descriptions=[{"name":n.attrib.get("name",""),"text":n.attrib["descr"]} for n in slide.findall(".//p:cNvPr",NS) if n.attrib.get("descr")]
            notes=[];media=[]
            for r in rr.values():
                if r.get("TargetMode")=="External":continue
                kind=r["Type"].rsplit("/",1)[-1];item=resolve(part,r["Target"])
                if kind=="notesSlide":notes=[n.text for n in ET.fromstring(z.read(item)).findall(".//a:t",NS) if n.text]
                if kind in {"image","video","media"}:media.append({"relationshipId":r["Id"],"part":item,"bytes":len(z.read(item)),"sha256":sha(z.read(item))})
            byid={r["relationshipId"]:r for r in media}
            comparison={"orderAndPart":old["part"]==part,"textNodes":old["textNodes"]==texts,
                        "accessibilityDescriptions":old["descriptions"]==descriptions,"speakerNotes":old["speakerNotes"]==notes,
                        "hidden":old["hidden"]==(slide.attrib.get("show")=="0"),
                        "imageAndVideoRelationships":all(byid.get(r["relationshipId"])==r for r in old["images"]+old["videoRelationships"]) and len(media)==len(old["images"]+old["videoRelationships"])}
            if old.get("image"):
                image_id=None
                for pic in slide.findall(".//p:pic",NS):
                    nv=pic.find("p:nvPicPr/p:cNvPr",NS);blip=pic.find("p:blipFill/a:blip",NS)
                    if nv is not None and nv.attrib.get("name","").startswith("Slide ") and blip is not None:
                        image_id=blip.attrib.get(f"{{{NS['r']}}}embed");break
                selected=byid.get(image_id) or next((r for r in media if r in old["images"]),None)
                local=BASE/"content"/old["image"]
                comparison["extractedSlideImageBytes"]=selected is not None and sha(local.read_bytes())==selected["sha256"]
            rows.append({"slide":old["slide"],"part":part,"checks":comparison,"passed":all(comparison.values())})
        archive=[{"part":i.filename,"bytes":i.file_size,"crc32":f"{i.CRC:08x}","sha256":sha(z.read(i.filename))} for i in z.infolist()]
    # Read-only investigation: compare the prefix at the exact previous length.
    oldlen=snapshot["input"]["bytes"]
    prefix=data[:oldlen]
    prefix_match=sha(prefix)==snapshot["input"]["sha256"]
    footer=data[oldlen:]
    footer_analysis={"bytesAdded":len(data)-oldlen,"exactSnapshotPrefixMatch":prefix_match,
                     "trailingBytesHex":footer.hex() if len(footer)<=128 else None,
                     "zipEndOfCentralDirectorySignature":footer.startswith(b"PK\x05\x06")}
    if footer.startswith(b"PK\x05\x06") and len(footer)>=22:
        values=struct.unpack("<4s4H2LH",footer[:22]);footer_analysis["record"]={"disk":values[1],"centralDirectoryDisk":values[2],"entriesOnDisk":values[3],"totalEntries":values[4],"centralDirectoryBytes":values[5],"centralDirectoryOffset":values[6],"commentBytes":values[7]}
    report={"date":"2026-10-05","policy":"Read-only input and frozen artifacts. Only this additive report is written.",
            "snapshotInput":snapshot["input"],"currentInput":{"path":str(path),"bytes":len(data),"sha256":sha(data)},
            "sourceIndexSha256":sha(INDEX.read_bytes()),"courseSha256":sha((BASE/"content/course.json").read_bytes()),
            "packageByteIdentity":sha(data)==snapshot["input"]["sha256"],"prefixInvestigation":footer_analysis,
            "checks":checks,"slides":rows,"allTeachingContentChecksPassed":all(r["passed"] for r in rows) and all(c["passed"] for c in checks),
            "currentArchiveEntries":archive,
            "limits":"Without byte-for-byte package identity, do not state that the current PPTX container is unchanged. All recorded slide ordering, extracted image bytes, text/accessibility descriptions, speaker notes, hidden flags and image/video relationships are compared against the frozen extraction. Unrecorded package properties are not compared to a historical archive unless the exact prefix is recovered."}
    output=BASE/"docs/source-input-reaudit.json";output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:report[k] for k in ["snapshotInput","currentInput","packageByteIdentity","prefixInvestigation","allTeachingContentChecksPassed"]},indent=2))
    print("Slides compared:",len(rows),"failed:",[r["slide"] for r in rows if not r["passed"]])
if __name__=="__main__":main()
