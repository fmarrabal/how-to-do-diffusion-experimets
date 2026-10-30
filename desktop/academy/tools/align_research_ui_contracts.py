"""Bounded source integration of the reviewed research engines' UI contracts."""
from pathlib import Path

P = Path(__file__).resolve().parents[1] / 'web/research-studio.js'


def main():
    text = P.read_text(encoding='utf-8')
    changes = [
        ("<pre class=\"rs-pre\">${esc(JSON.stringify(p,null,2))}</pre>", "${plot([{name:t('Nutación con signo','Signed nutation'),data:(p.pulseCurve||[]).map(v=>({x:v.pulseUs,y:v.signedIntegral}))}],'p / µs','S / S₀')}<div class=\"rs-metrics\">${metric(t('Primer nulo / µs','First null / µs'),fmt(p.firstNullUs,5))}${metric(t('Máximo precedente / µs','Preceding maximum / µs'),fmt(p.precedingMaximumUs,5))}</div>${plot([{name:t('Patrón','Standard'),data:(p.referenceCurve||[]).map(v=>({x:v.bNominal*1e-9,y:v.signal}))}],'b nominal / 10⁹ s m⁻²','S / S₀')}"),
        ("Object.entries({objective:t(", "Object.entries({objective:t("),
        ("fields:clone(draft),evidenceReferences:[caseState.id+':'+caseState.stage],now:now(),parentSubmission:submissions.at(-1)||undefined", "fields:{question:draft.objective,prediction:prediction,processing:[draft.physics,draft.experimentalDesign,draft.processing,draft.uncertainty].join('\\n\\n'),controls:draft.controls,conclusion:draft.conclusion},evidenceReferences:[{id:caseState.id+':'+caseState.stage,label:t('Estado reproducible del caso','Reproducible case snapshot'),sha256:caseSha256,kind:'case-snapshot'}],now:now(),parentSubmission:submissions.filter(s=>s.caseId===caseState.id&&s.caseSha256===caseSha256).at(-1)||undefined"),
        ("const scores=Object.fromEntries(rubricNames.map(id=>[id,num('score-'+id)])),comments=value('review-comment'),questions=[value('review-question')];", "const scores=Object.fromEntries(rubricNames.map(id=>[id,num('score-'+id)])),comments=Object.fromEntries(rubricNames.map(id=>[id,value('review-comment-'+id)])),questions=[value('review-question')].filter(q=>q.trim());"),
        ("evidenceReferences:submission.evidenceReferences||[],questions,reviewer:", "evidenceReferences:Object.fromEntries(rubricNames.map(id=>[id,submission.evidenceReferences.map(r=>r.id)])),questions,reviewer:"),
        ("${rubricNames.map(id=>number('score-'+id,id,2,'0–4','min=\"0\" max=\"4\" step=\"1\"')).join('')}</div><label>${t('Comentario con referencias a evidencias','Feedback with evidence references')}<textarea data-field=\"review-comment\"></textarea></label>", "${rubricNames.map(id=>`<div>${number('score-'+id,id,2,'0–4','min=\"0\" max=\"4\" step=\"1\"')}<label>${t('Comentario y evidencia para este criterio','Feedback and evidence for this criterion')}<textarea data-field=\"review-comment-${id}\" maxlength=\"4000\"></textarea></label></div>`).join('')}</div>"),
        ("const parsed=P.parseCSV(raw,'attenuation'),rows=parsed.rows||parsed.data||parsed;", "const parsed=P.parseCSV(raw,'attenuation'),rows=parsed.rows||parsed.data||(parsed.bs?parsed.bs.map((b,i)=>({b_s_m2:b,signal:parsed.signals?.[i]??parsed.signal?.[i]??parsed.intensities?.[i]})):parsed);"),
        ("const a=caseState.analysis;return card", "const a=caseState.analysis;return card"),
    ]
    for old, new in changes:
        if old == new:
            continue
        if new in text:
            continue
        if text.count(old) != 1 and not (old.startswith("<pre class=") and text.count(old)==2):
            raise ValueError('Unexpected UI anchor: ' + old[:90])
        text = text.replace(old,new,1)
    P.write_text(text,encoding='utf-8')
    print('Research UI aligned with typed learning and case contracts')


if __name__=='__main__':
    main()
