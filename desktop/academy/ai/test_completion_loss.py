"""Compare Academy completion-only loss and gradients against the full HF loss."""
import json
from pathlib import Path
import torch
from transformers import Qwen3Config, Qwen3ForCausalLM
from academy_pipeline import masked_completion_loss

torch.manual_seed(261005)
model=Qwen3ForCausalLM(Qwen3Config(vocab_size=128,hidden_size=32,intermediate_size=64,num_hidden_layers=2,num_attention_heads=2,num_key_value_heads=2,head_dim=16,attention_dropout=0)).eval()
ids=torch.randint(0,128,(2,19));mask=torch.ones_like(ids);mask[1,15:]=0
labels=ids.clone();labels[0,:13]=-100;labels[1,:9]=-100;labels[1,15:]=-100
batch=dict(input_ids=ids,attention_mask=mask,labels=labels)
full=model(**batch).loss;full.backward();grad={n:p.grad.clone() for n,p in model.named_parameters() if p.grad is not None}
model.zero_grad();compact=masked_completion_loss(model,batch);compact.backward()
torch.testing.assert_close(full,compact,rtol=1e-6,atol=1e-7)
max_delta=0
for n,p in model.named_parameters():
    if n in grad:
        torch.testing.assert_close(p.grad,grad[n],rtol=2e-5,atol=1e-7)
        max_delta=max(max_delta,float((p.grad-grad[n]).abs().max()))
report=dict(passed=True,scope="Loss and all trainable gradients versus independent full HuggingFace causal loss, including prompt masking and ragged padding.",full_loss=float(full),completion_loss=float(compact),max_gradient_absolute_delta=max_delta,experimental_validation=False)
Path(__file__).with_name('completion-loss-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
