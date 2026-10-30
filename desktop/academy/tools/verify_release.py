"""Verify frozen course/model/docs and the actual published WPF folder."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def load(path):
    return json.loads(path.read_text('utf-8-sig'))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--ui-qa', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Preserve completed release evidence.')
    checks = []
    def check(name, passed, detail=None):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})
    manifest = {k.lower(): v for k, v in load(ROOT / 'ai/release/manifest.json').items()}
    course = load(ROOT / 'content/course.json')
    check('frozen_bilingual_course', sha(ROOT / 'content/course.json') == manifest['coursesha256'] and len(course['modules']) == 24,
          {'modules': 24, 'examples': sum(len(m['examples']) for m in course['modules']), 'questions': sum(len(m['questions']) for m in course['modules'])})
    check('tutor_release_gate', manifest['finetuned'] and manifest['qualitypassed'] and manifest['nativeevaluationpassed']
          and manifest['nativeevaluationpending'] is False and manifest['experimentalvalidation'] is False, manifest['answermode'])
    check('tutor_source_identity', sha(ROOT / 'src/DiffAtOnce.Academy.Tutor/TutorService.cs') == manifest['tutorsourcesha256'])
    native = load(ROOT / 'ai/release/native_evaluation_report.json')
    check('actual_native_hybrid_cpu', native['passed'] and all(c['passed'] for c in native['checks'])
          and sha(ROOT / 'ai/release/native_evaluation_report.json') == manifest['nativeevaluationreportsha256'], {'checks': len(native['checks']), 'scope': native['scope']})
    evaluation = load(ROOT / 'ai/release/evaluation_report.json')
    tuned = evaluation['engines']['fine_tuned'] if 'fine_tuned' in evaluation['engines'] else evaluation['engines']['finetuned']
    check('reserved_free_generation', evaluation['quality_passed'] and tuned['passed'] == tuned['total'],
          {'passed': tuned['passed'], 'total': tuned['total'], 'scope': 'Developer-authored held-out HF fixtures; not independent scientific/student validation.'})
    numeric = load(ROOT / 'tests/DiffAtOnce.Academy.Tests/bin/Release/net8.0/teaching-simulations-qa.json')
    check('native_numeric_models', all(c['passed'] for c in numeric['checks'])
          and numeric['source_sha256'] == sha(ROOT / 'src/DiffAtOnce.Academy.Core/TeachingSimulations.cs'), {'checks': len(numeric['checks'])})
    for name, report_path in [('final_wpf_and_llm', ROOT / 'qa/ui-release-final/ui-self-test.json'), ('published_wpf', args.ui_qa)]:
        gui = load(report_path)
        check(name, all(c['passed'] for c in gui['checks']) and gui['courseSha256'] == manifest['coursesha256'],
              {'checks': len(gui['checks']), 'report_sha256': sha(report_path), 'scope': 'Observed actions in the application; no instrument validation.'})
    lab = load(ROOT / 'qa/lab-embedding-verification.json')
    check('original_motion_lab_preserved', lab['passed'], {'files': len(lab['checks'])})
    structure = load(ROOT / 'docs/manual-verification.json')
    visual = load(ROOT / 'docs/manual-visual-review.json')
    check('pdf_structure', structure['failed'] == 0 and all(c['passed'] for c in structure['checks']), {'checks': len(structure['checks'])})
    check('pdf_visual_review_current', visual.get('tutorStatus') in {'verified', 'verified-hybrid-package'} and not visual.get('currentBuildNeedsFinalVisualReview')
          and not visual.get('supersededByRebuild') and all(m['result'] == 'passed' and m['sha256'] == sha(ROOT / 'docs' / m['file']) for m in visual['manuals']), visual['manuals'])
    critical = ['DiffAtOnce.Academy.exe', 'DiffAtOnce.Academy.dll', 'DiffAtOnce.Academy.Tutor.dll',
                'Content/course.json', 'Models/Beatrix/model.gguf', 'Models/Beatrix/manifest.json', 'Docs/MANUAL_ES.pdf', 'Docs/MANUAL_EN.pdf']
    files = [{'path': name, 'bytes': (args.package / name).stat().st_size, 'sha256': sha(args.package / name)} for name in critical]
    for name, original in [('Content/course.json', ROOT / 'content/course.json'), ('Models/Beatrix/manifest.json', ROOT / 'ai/release/manifest.json'),
                           ('Docs/MANUAL_ES.pdf', ROOT / 'docs/MANUAL_ES.pdf'), ('Docs/MANUAL_EN.pdf', ROOT / 'docs/MANUAL_EN.pdf')]:
        check('published_identity_' + name, sha(args.package / name) == sha(original))
    check('published_model_identity', next(f['sha256'] for f in files if f['path'].endswith('model.gguf')) == manifest['sha256'])
    source_audits = {p.name: load(p) for p in (ROOT / 'content').glob('*recheck*.json')}
    source_audits.update({p.name: load(p) for p in (ROOT / 'content').glob('*drift*.json')})
    source_reaudit_path = ROOT / 'docs/source-input-reaudit.json'
    if source_reaudit_path.exists():
        recheck = load(source_reaudit_path)
        source_audits[source_reaudit_path.name] = recheck
        check('current_source_teaching_content', len(recheck['slides']) == 81 and all(s['passed'] for s in recheck['slides'])
              and recheck['courseSha256'] == manifest['coursesha256']
              and sha(Path(recheck['currentInput']['path'])) == recheck['currentInput']['sha256'],
              {'slides': len(recheck['slides']), 'packageByteIdentity': recheck['packageByteIdentity'],
               'scope': 'Teaching content matches the frozen extraction; current ZIP container identity is recorded separately.'})
    result = {'application': 'DiffAtOnce Academy 1.0.0', 'platform': 'WPF Windows x64', 'passed': all(c['passed'] for c in checks),
              'checks': checks, 'critical_files': files, 'source_container_rechecks': source_audits,
              'experimental_validation': False, 'limitations': 'Synthetic education and software QA; no spectrometer operation, experimental validation or measured student-learning effectiveness. Tutor generated output and literal course text are distinct.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'passed': result['passed'], 'checks': len(checks), 'failed': [c['name'] for c in checks if not c['passed']], 'report': str(args.output)}))
    return 0 if result['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
