"""Regression controls for source-container drift versus changed teaching content.

Fixtures are tiny generated OOXML archives, not copies of the user's deck.
"""
from pathlib import Path
import hashlib
import io
import json
import tempfile
import unittest
import zipfile

from manual_source_reaudit import compare_source

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"

def presentation(text, comment=b""):
    output=io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("ppt/presentation.xml",f'<p:presentation xmlns:p="{P}" xmlns:r="{R}"><p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst></p:presentation>')
        z.writestr("ppt/_rels/presentation.xml.rels",f'<Relationships xmlns="{REL}"><Relationship Id="rId1" Type="{R}/slide" Target="slides/slide1.xml"/></Relationships>')
        z.writestr("ppt/slides/slide1.xml",f'<p:sld xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree><a:t>{text}</a:t></p:spTree></p:cSld></p:sld>')
        z.comment=comment
    return output.getvalue()

class SourceComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="academy-source-fixture-")
        self.folder=Path(self.temp.name)
        self.original=presentation("Frozen teaching snapshot")
        self.snapshot={"input":{"path":"synthetic-original.pptx","bytes":len(self.original),"sha256":hashlib.sha256(self.original).hexdigest()},
            "slides":[{"slide":1,"part":"ppt/slides/slide1.xml","textNodes":["Frozen teaching snapshot"],"descriptions":[],"speakerNotes":[],"hidden":False,"images":[],"videoRelationships":[]}]}
    def tearDown(self): self.temp.cleanup()
    def compare(self, data):
        p=self.folder/"fixture.pptx";p.write_bytes(data)
        report=compare_source(p,self.snapshot)
        self.assertEqual(p.read_bytes(),data,"Read-only comparison must retain input bytes")
        return report
    def test_exact_container_retains_both_identities(self):
        report=self.compare(self.original)
        self.assertTrue(report["packageByteIdentity"])
        self.assertTrue(report["allTeachingContentChecksPassed"])
    def test_container_only_change_is_explicit_not_original_identity(self):
        report=self.compare(presentation("Frozen teaching snapshot",comment=b"synthetic packaging change"))
        self.assertFalse(report["packageByteIdentity"])
        self.assertTrue(report["allTeachingContentChecksPassed"])
        self.assertTrue(all(report["slides"][0]["checks"].values()))
    def test_changed_teaching_text_is_rejected(self):
        report=self.compare(presentation("Different unreviewed teaching"))
        self.assertFalse(report["packageByteIdentity"])
        self.assertFalse(report["allTeachingContentChecksPassed"])
        self.assertFalse(report["slides"][0]["checks"]["textNodes"])
    def test_changed_hidden_status_is_rejected(self):
        self.snapshot["slides"][0]["hidden"]=True
        report=self.compare(self.original)
        self.assertFalse(report["allTeachingContentChecksPassed"])
        self.assertFalse(report["slides"][0]["checks"]["hidden"])

if __name__ == "__main__":unittest.main()
