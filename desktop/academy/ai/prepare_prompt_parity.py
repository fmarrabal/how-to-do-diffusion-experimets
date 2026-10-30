import json
from pathlib import Path
from transformers import AutoTokenizer
import academy_pipeline_v2 as pipeline

here=Path(__file__).resolve().parent
folder=here/"PromptParity/fixtures"
folder.mkdir(parents=True,exist_ok=True)
tokenizer=AutoTokenizer.from_pretrained(here/"base-1.7b",local_files_only=True)
rows=[json.loads(line) for line in (here/"work-v2/test.jsonl").read_text(encoding="utf-8").splitlines()]
for index,row in enumerate(rows):
    source=folder/f"input-{index:02}.json"
    expected=folder/f"expected-{index:02}.txt"
    if source.exists() or expected.exists():raise RuntimeError("Parity fixture exists; preserve it.")
    source.write_text(json.dumps(row["input"],ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    expected.write_bytes(pipeline.chat_prompt(tokenizer,row["input"]).encode("utf-8"))
print(json.dumps(dict(fixtures=len(rows),scope="serialization only, no inference")))
