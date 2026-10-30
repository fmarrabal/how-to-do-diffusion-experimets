"""Prepare unchanged, licensed public Bruker series for the research studio.

No private sample, calibration, article PDF or inferred reference D is included.
Paired acquisition numbers identify repository groups, not certified controls.
"""
from pathlib import Path
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "desktop/academy"
ARCHIVE = BASE / "research/doctoral-1.2/figshare-33075584-original.zip"
EXPECTED = "be65cb5cd54cffdac4ad3b6bca5d90fce175ba652d7127262513eef4e21f5dbc"
DOI = "10.26180/33075584.v1"
ATTRIBUTION = "Igor Silva, Alasdair McKay and Tanja Junkers. Comparison of Oligomer to Polymer Molar Mass Calibrations in Diffusion-Ordered Spectroscopy (DOSY) - Repository. Monash/Figshare. DOI " + DOI
LICENSE = {"name": "CC BY 4.0", "url": "https://creativecommons.org/licenses/by/4.0/"}
FILES = ["ser.ser", "acqus", "acqu2s", "pulseprogram", "difflist", "gradient_calib", "gpnam6", "pdata/1/procs", "pdata/1/dosy", "pdata/1/title"]
SELECT = [("IS_PMA1", "10"), ("IS_PMA1", "21"), ("IS_PMA6", "11"), ("IS_PMA6", "21"), ("IS_PMMA1", "12"), ("IS_PMMA1", "21"), ("IS_PMMA6", "12"), ("IS_PMMA6", "21")]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    assert sha(ARCHIVE.read_bytes()) == EXPECTED, "Public archive identity differs"
    cases = []
    with zipfile.ZipFile(ARCHIVE) as archive:
        for sample, experiment in SELECT:
            identity = "monash-" + sample.removeprefix("IS_").lower() + "-" + experiment
            origin = f"raw data/DOSY/{sample}/{experiment}"
            target = BASE / "content/research-data" / identity
            records = []
            for name in FILES:
                if origin + "/" + name not in archive.namelist():
                    if name == "pdata/1/dosy":
                        continue
                    raise ValueError("Required public original absent: " + origin + "/" + name)
                data = archive.read(origin + "/" + name)
                file = target / name
                file.parent.mkdir(parents=True, exist_ok=True)
                if file.exists():
                    assert file.read_bytes() == data, "Existing original must remain unchanged"
                else:
                    file.write_bytes(data)
                records.append({"path": name, "originalArchivePath": origin + "/" + name, "bytes": len(data), "sha256": sha(data), "url": "content/research-data/" + identity + "/" + name})
            acq = (target / "acqus").read_text(errors="replace")
            def scalar(name):
                match = re.search(r"^##\$" + re.escape(name) + r"=\s*(.+)$", acq, re.M)
                return match.group(1).strip() if match else None
            metadata = {key: scalar(key) for key in ["PULPROG", "TE", "NS", "RG", "SW_h", "SFO1", "GRPDLY", "TD"]}
            def array_parameter(name, index):
                match = re.search(r"^##\$" + re.escape(name) + r"=\s*\((\d+)\.\.(\d+)\)\s*\n(.*?)(?=^##|\Z)", acq, re.M | re.S)
                if not match:
                    return None
                values = []
                for line in match.group(3).splitlines():
                    if line.startswith('$$'):
                        continue
                    for token in line.split():
                        try:
                            values.append(float(token))
                        except ValueError:
                            return None
                offset = index - int(match.group(1))
                return values[offset] if 0 <= offset < len(values) else None
            metadata.update(d1Seconds=array_parameter('D', 1), d5Seconds=array_parameter('D', 5), d20Seconds=array_parameter('D', 20), p1Us=array_parameter('P', 1), p30Us=array_parameter('P', 30))
            metadata['parameterMeaning'] = 'Literal acquired TopSpin parameters; no universal identification with effective delta/Delta is inferred.'
            metadata["savedDOSYParametersAvailable"] = any(record["path"] == "pdata/1/dosy" for record in records)
            metadata["verifiedBRequiredBeforeDiffusionFit"] = not metadata["savedDOSYParametersAvailable"]
            provenance = {"schema": "academy-public-dataset/1", "sourceDOI": DOI, "sourceURL": "https://doi.org/" + DOI, "license": LICENSE, "attribution": ATTRIBUTION, "archiveSHA256": EXPECTED, "selection": "Unmodified public subset " + origin, "absoluteCalibrationValidated": False, "sampleGroup": sample, "experiment": experiment, "metadata": metadata, "files": records}
            (target / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
            cases.append({"id": identity, "title": {"es": sample.removeprefix("IS_") + " · adquisición " + experiment, "en": sample.removeprefix("IS_") + " · acquisition " + experiment}, "evidence": "experimental-public", "datasetBase": "content/research-data/" + identity, "group": sample, "experiment": experiment, "metadata": metadata, "sourceDOI": DOI, "license": LICENSE, "attribution": ATTRIBUTION, "objectives": {"es": "Inspecciona FID, fase, ventana y metadatos; compara la otra adquisición del mismo grupo. Justifica qué diferencias permiten una comparación y cuáles impiden inferir una causa.", "en": "Inspect FID, phase, integration and metadata; compare the other acquisition in the same group. Explain which differences permit comparison and which prevent a causal inference."}, "limitations": {"es": "La agrupación del repositorio no acredita un control de temperatura, convección ni réplicas idénticas. b y D son nominales/condicionales; no se proporciona una D verdadera ni masa absoluta.", "en": "Repository grouping does not establish a temperature/convection control or identical replicates. b and D are nominal/conditional; no true D or absolute molar mass is provided."}})
    catalogue = {"version": "1.3.0", "id": "academy-research-library", "sourceDOI": DOI, "license": LICENSE, "attribution": ATTRIBUTION, "cases": cases, "comparisonGroups": [{"id": sample, "caseIds": [case["id"] for case in cases if case["group"] == sample], "controlledVariable": None, "independentGroundTruthD": None} for sample in dict.fromkeys(sample for sample, _ in SELECT)]}
    (BASE / "content/research-library.json").write_text(json.dumps(catalogue, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"cases": len(cases), "originalFiles": sum(len(json.loads((BASE / case["datasetBase"] / "provenance.json").read_text())["files"]) for case in cases), "comparisonGroups": len(catalogue["comparisonGroups"]), "archiveUnchanged": sha(ARCHIVE.read_bytes()) == EXPECTED}))


if __name__ == "__main__":
    main()
