"""Additive git check using an actual empty ignore file, never Windows NUL."""
import hashlib
import json
import subprocess
from pathlib import Path

here=Path(__file__).resolve().parent
repo=here.parents[2]/"desktop/training/work/llama.cpp"
ignore=here/"git-empty-ignore.txt"
if not ignore.exists():ignore.write_bytes(b"")
status=subprocess.run(["git","-c",f"core.excludesFile={ignore}","-C",str(repo),"status","--porcelain","--untracked-files=no"],capture_output=True,text=True,check=False)
blob=subprocess.run(["git","-C",str(repo),"show","HEAD:convert_hf_to_gguf.py"],capture_output=True,check=False)
actual=(repo/"convert_hf_to_gguf.py").read_bytes()
def sha(data):return hashlib.sha256(data).hexdigest()
normalized=actual.replace(b"\r\n",b"\n")
report=dict(environment_report_sha256=sha((here/"environment_report.json").read_bytes()),tracked_changes=dict(returncode=status.returncode,stdout=status.stdout,stderr=status.stderr),converter_matches_source_commit=blob.returncode==0 and blob.stdout==actual,converter_matches_source_after_crlf_normalization=blob.returncode==0 and blob.stdout==normalized,converter_working_sha256=sha(actual),converter_normalized_lf_sha256=sha(normalized),converter_git_blob_sha256=sha(blob.stdout) if blob.returncode==0 else None,scope="Additive CRLF-versus-LF provenance check. Actual converter hash remains authoritative. Earlier reports, base weights and completed training/evaluation reports remain intact.")
target=here/"environment_git_provenance_normalized.json"
if target.exists():raise RuntimeError("Preserve completed additive provenance check.")
target.write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report))
