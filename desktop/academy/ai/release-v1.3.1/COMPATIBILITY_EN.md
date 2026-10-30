# Beatrix 1.3.1 compatibility record

This release reuses the exact existing Qwen3-1.7B Q8_0 weights from Academy 1.3. No fine-tuning, optimizer steps, quantization or model-file edits were performed for this compatibility review. The source workspace uses one NTFS hardlink to the original GGUF, not a separate disk copy.

`TrainingCourseSha256` and `OriginalSupplementalSha256` preserve the original content provenance. `CourseSha256` and `SupplementalContentSha256` identify the corrected runtime content. Original training and evaluation reports remain unchanged and are labelled by `OriginalTrainingQualification`, `OriginalQualificationMetadata` and the exact original manifest copy.

`native_evaluation_report.json` records actual local C# runtime evaluation against the corrected course and mathematics. It includes model generation, source/citation guards, cancellation, original-course regression, fresh English/Spanish symbolic temperature-factor queries, and literal documentary delivery of all mathematical chapters in both languages. Literal documentary delivery is not LLM generation or model learning.

Recording a passing run does not automatically approve a release. The pre-approval state kept native, compatibility and supplemental gates false/pending until root review. Original `QualityPassed` and `ResearchQualityPassed` describe the frozen trained-model provenance only. No instrument, experimental or educational-effectiveness validation is claimed.

The source changes following that run are evaluated separately in `compatibility_guard_evaluation.json` and reviewed in `compatibility_guard_review.json`. Explicitly synthetic gradient-scaling answers with unsupported measurement claims or the observed reversal of gradient versus b scaling are rejected into labelled reviewed guidance. Raw rejected generation is retained in evaluation diagnostics and is not shown as an accepted model answer. Combined temperature/flow questions use the complete reviewed temperature and convection modules without invoking the model.

The scoped post-change run contains 82 behavior checks, including replay of 14 original and 4 earlier captured answers, four actual new generations and two actual documentary requests. Two generations are accepted; two are rejected into reviewed fallback. The preserved first post-change automatic-pass report contains a manually identified causal error and is not treated as semantic approval. Neither replay nor fallback is counted as successful new generation. Model weights and system instructions remain unchanged, and final release approval belongs to the parent review.


Root review accepts bounded hybrid teaching compatibility in `compatibility_approval.json`. Current flags refer to that composite scope. The original103 and later82 reports remain distinct; two rejected generations are documentary fallback, not successful generation. Final package WPF QA remains a separate distribution gate. Arbitrary generated prose is not certified.
