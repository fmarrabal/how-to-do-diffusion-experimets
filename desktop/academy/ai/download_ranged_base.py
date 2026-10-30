"""Bounded ranged retrieval after a full public model request stalled.
Public pinned artifact only; TLS verification stays enabled; every range and
final SHA-256 are checked. Four workers, at most two attempts per range.
"""
import concurrent.futures
import hashlib
import json
import os
import time
from pathlib import Path

dest=Path(__file__).resolve().parent/'base-1.7b'
model='Qwen/Qwen3-1.7B';revision='70d244cc86ccca08cf5af4e1e306ecf908b1ad5e'
os.environ.update(HF_HOME=str(dest.parent/'hub-cache'),HF_HUB_DISABLE_TELEMETRY='1',HF_HUB_DISABLE_XET='1')
import requests
from huggingface_hub import HfApi
info=HfApi(token=False).model_info(model,revision=revision,files_metadata=True)
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
for sibling in info.siblings:
 if not sibling.rfilename.endswith('.safetensors'):continue
 name=sibling.rfilename
 if Path(name).name!=name:raise RuntimeError('Unexpected nested weight name')
 size=sibling.lfs.size;expected=sibling.lfs.sha256;target=dest/name
 if target.exists() and target.stat().st_size==size and sha(target)==expected:
  print(json.dumps(dict(file=name,status='already_verified')),flush=True);continue
 blocks=dest/(name+'.verified-ranges');blocks.mkdir(exist_ok=True);width=16*1024*1024;count=(size+width-1)//width;started=time.time()
 def get(i):
  start=i*width;end=min(size-1,start+width-1);part=blocks/f'{i:04d}.block'
  if part.exists() and part.stat().st_size==end-start+1:return i
  for attempt in range(2):
   try:
    url=f'https://huggingface.co/{model}/resolve/{revision}/{name}?academy_range={i}'
    with requests.get(url,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'},stream=True,timeout=(10,45)) as r:
     if r.status_code!=206 or r.headers.get('Content-Range')!=f'bytes {start}-{end}/{size}':raise RuntimeError(f'Invalid ranged response: {r.status_code}')
     with part.open('wb') as out:
      for chunk in r.iter_content(1024*1024):out.write(chunk)
    if part.stat().st_size!=end-start+1:raise RuntimeError('Short ranged response')
    return i
   except (requests.RequestException,RuntimeError):
    if attempt:raise
    time.sleep(1)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  done=0
  for future in concurrent.futures.as_completed([pool.submit(get,i) for i in range(count)]):
   future.result();done+=1
   if done%10==0 or done==count:print(json.dumps(dict(file=name,ranges=done,total=count,seconds=round(time.time()-started))),flush=True)
 assembled=dest/(name+'.assembled')
 with assembled.open('wb') as out:
  for i in range(count):
   with (blocks/f'{i:04d}.block').open('rb') as f:
    for chunk in iter(lambda:f.read(1024*1024),b''):out.write(chunk)
 if sha(assembled)!=expected:raise RuntimeError('Full pinned model SHA-256 mismatch')
 assembled.replace(target)
 print(json.dumps(dict(file=name,status='verified',sha256=expected,seconds=round(time.time()-started))),flush=True)
report=dict(model=model,revision=revision,license='Apache-2.0',official_model_card='https://huggingface.co/'+model,files={f.name:dict(bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(dest.iterdir()) if f.is_file() and f.name!='base-provenance.json'},private_data_transmitted=False,transfer='Checked bounded range retrieval after a stalled full request',weights_matched_upstream_sha256=True)
(dest/'base-provenance.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(status='complete',revision=revision)),flush=True)
