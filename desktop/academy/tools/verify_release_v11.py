"""Verify independently versioned Academy mathematics and downloadable WPF.

This report does not claim deployment, experiment validation or student outcomes.
The old 1.0 model/course/reports remain historical, immutable evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_text('utf-8-sig'))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--ui-qa', type=Path, required=True)
    parser.add_argument('--web-qa', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Preserve release evidence; choose a fresh report.')
    checks = []
    def check(name, passed, detail=None):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})
    release = ROOT / 'ai/release-v1.1'
    manifest = read(release / 'manifest.json')
    old = read(ROOT / 'ai/release/manifest.json')
    data = read(ROOT / 'content/derivations.json')
    bundle = read(ROOT / 'web/bundle-manifest.json')
    mathematical = read(ROOT / 'research/papers-20261005/scientific-review.json')
    check('reviewed_mathematics_identity', mathematical['contentSha256'] == sha(ROOT / 'content/derivations.json') and data['releaseStatus'] == 'reviewed' and mathematical['counts']['chapters'] == len(data['chapters']) == 20)
    check('independent_sequence_numerics', mathematical['numericalReview']['passed'] and all(c['passed'] for c in mathematical['numericalReview']['cases']), {'checks':mathematical['numericalReview']['checkCount'], 'scope':mathematical['numericalReview']['method']})
    expected_eq = {'sinnaeve-2012': {str(n) for n in range(1,66)}, 'kuchel-2012': {str(n) for n in range(1,39)} | {'A'+str(n) for n in range(1,9)}}
    mapped = {source['id']: {str(e['paperEquation']) for e in data['equationCoverage'] if e['sourceId'] == source['id']} for source in data['sources']}
    # Source IDs may include title-specific suffixes; source DOI fixes identity.
    for source in data['sources']:
        key = 'sinnaeve-2012' if source['doi'] == '10.1002/cmr.a.21223' else 'kuchel-2012'
        check('all_numbered_equations_' + key, mapped[source['id']] == expected_eq[key])
    check('model_weights_unchanged', manifest['Sha256'] == old['Sha256'] == sha(release / manifest['File']))
    check('frozen_course', manifest['CourseSha256'] == old['CourseSha256'] == sha(ROOT / 'content/course.json'))
    check('new_papers_documentary_only', manifest['SupplementalIncludedInTraining'] is False and manifest['SupplementalContentSha256'] == sha(ROOT / 'content/derivations.json') and manifest['SupplementalLLMApproved'] is False and manifest['SupplementalAnswerMode'] == 'reviewed-documentary-guide')
    check('native_tutor_gates', manifest['FineTuned'] and manifest['QualityPassed'] and manifest['NativeEvaluationPassed'] and manifest['NativeEvaluationPending'] is False and manifest['SupplementalNativeEvaluationPassed'] and manifest['SupplementalNativeEvaluationPending'] is False and manifest['ExperimentalValidation'] is False)
    native = read(release / 'native_evaluation_report.json')
    check('compiled_native_tutor_report', native['passed'] and sha(release / 'native_evaluation_report.json') == manifest['NativeEvaluationReportSha256'])
    check('new_response_semantics_reviewed', manifest['SupplementalSemanticEvaluationPending'] is False and bool(manifest['SupplementalSemanticEvaluationReportSha256']))
    for name, description in [('legacy_regression','unchanged course CPU generation'), ('supplemental_evaluation','reviewed paper documentary delivery; no LLM generation')]:
        detail = native[name]
        report = read(release / detail['file'])
        check(name, report['passed'] and all(c['passed'] for c in report['checks']) and sha(release / detail['file']) == detail['sha256'], {'checks':len(report['checks']), 'scope':description})
    semantic_record = native['supplemental_semantic_review']
    semantic_file = release / semantic_record['file']
    semantic = read(semantic_file)
    supplemental_record = native['supplemental_evaluation']
    supplemental = read(release / supplemental_record['file'])
    native_answer_ids = set(supplemental['delivery_case_ids'])
    semantic_answer_ids = {c['id'] for c in semantic['answers']}
    check('actual_semantic_report_identity', sha(semantic_file) == semantic_record['sha256'] == manifest['SupplementalSemanticEvaluationReportSha256']
          and semantic['native_report_sha256'] == supplemental_record['sha256']
          and semantic['corpus_sha256'] == manifest['SupplementalContentSha256']
          and semantic['model_sha256'] == manifest['Sha256'])
    check('delivered_guide_mode', supplemental['answer_mode'] == 'reviewed-documentary-guide' and supplemental['supplemental_llm_approved'] is False and supplemental['native_inference_performed'] is False and len(native_answer_ids) == 5)
    check('all_documentary_responses_reviewed', semantic['reviewed_guide_supported'] is True and semantic['critical_contradictions'] == []
          and semantic['experimental_validation'] is False and native_answer_ids == semantic_answer_ids
          and all(c['reviewed_guide_supported'] is True for c in semantic['answers']))
    for rejected in semantic['rejected_llm_reports']:
        failed_file = release / rejected['file']
        failed_review = release / rejected['semantic_review_file']
        check('rejected_generation_preserved_' + rejected['file'], rejected['passed'] is False and rejected['promotable'] is False
              and read(failed_file)['passed'] is False and sha(failed_file) == rejected['sha256']
              and sha(failed_review) == rejected['semantic_review_sha256'])
    for name, expected in manifest['TutorFilesSha256'].items():
        check('tutor_source_' + name, sha(ROOT / 'src/DiffAtOnce.Academy.Tutor' / name) == expected)
    check('complete_browser_without_llm', bundle['beatrix'] is False and bundle['derivationsSha256'] == sha(ROOT / 'content/derivations.json') and 'pending' not in bundle['releaseStatus'])
    web = read(args.web_qa)
    check('browser_qa', web['failed'] == 0 and web['derivationsReviewed'] is True, {'checks':web['passed'], 'report_sha256':sha(args.web_qa)})
    for name, relative in [('waveform_numeric','qa/papers-1.1/waveform-qa.json'), ('base_web_numeric','qa/web/numeric-qa.json')]:
        report = read(ROOT / relative)
        check(name, report.get('failed',0) == 0 and all(c['passed'] for c in report['checks']), {'checks':len(report['checks']), 'sha256':sha(ROOT / relative)})
    check('waveform_source_identity', read(ROOT/'qa/papers-1.1/waveform-qa.json')['sourceSha256'] == sha(ROOT/'web/waveform-lab.js'))
    native_calculators = read(ROOT/'qa/papers-1.1/native-calculators-final.json')
    check('native_calculators_and_source_identity', native_calculators['passed'] and all(c['passed'] for c in native_calculators['checks'])
          and native_calculators['source_sha256'] == sha(ROOT / native_calculators['source']), {'checks':len(native_calculators['checks'])})
    gui = read(args.ui_qa)
    check('packaged_wpf_and_local_beatrix', all(c['passed'] for c in gui['checks']) and gui['applicationVersion'] == '1.1.0' and gui['supplementalSha256'] == manifest['SupplementalContentSha256'], {'checks':len(gui['checks']), 'sha256':sha(args.ui_qa)})
    identities = {'Content/course.json':ROOT/'content/course.json', 'Content/derivations.json':ROOT/'content/derivations.json', 'Web/bundle-manifest.json':ROOT/'web/bundle-manifest.json', 'Web/content/derivations.json':ROOT/'web/content/derivations.json', 'Web/waveform-lab.js':ROOT/'web/waveform-lab.js', 'Models/Beatrix/manifest.json':release/'manifest.json', 'Models/Beatrix/model.gguf':release/'model.gguf'}
    files = []
    for name, original in identities.items():
        file = args.package / name
        check('packaged_identity_' + name, file.is_file() and sha(file) == sha(original))
        files.append({'path':name,'bytes':file.stat().st_size,'sha256':sha(file)})
    forbidden = [str(p.relative_to(args.package)) for p in args.package.rglob('*') if p.is_file() and ('-private.pdf' in p.name or '.private.pdf' in p.name or p.name in ['Sinnaeve-2012-private.pdf','Kuchel-2012-private.pdf'])]
    check('no_private_paper_copies_in_package', not forbidden, forbidden)
    result = {'application':'DiffAtOnce Academy 1.1.0', 'passed':all(c['passed'] for c in checks), 'checks':checks, 'critical_files':files, 'experimental_validation':False, 'deployment_verified':False, 'scope':'Packaged WPF/software and reviewed mathematical education QA. Paper chapters use a documentary guide without LLM generation. Original-course local Beatrix and its fine-tuning are preserved. Failed mathematical LLM trials are not relabelled successes. No student efficacy or spectrometer validation.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'checks':len(checks),'failed':[c['name'] for c in checks if not c['passed']]}))
    return 0 if result['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
