"""Integrate the shared research studio without changing legacy scientific engines."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[3]
ACADEMY = ROOT / "desktop/academy"


def replace(text, old, new):
    if new in text:
        return text
    if text.count(old) != 1:
        raise ValueError("Unexpected source shape: " + old[:80])
    return text.replace(old, new, 1)


def main():
    web = ACADEMY / "web"
    path = web / "index.html"
    text = path.read_text(encoding="utf-8")
    text = replace(text, '  <link rel="stylesheet" href="doctoral-hub.css">', '  <link rel="stylesheet" href="research-studio.css">\n  <link rel="stylesheet" href="doctoral-hub.css">')
    text = replace(text, '  <script src="academy.js" defer></script>', '\n'.join('  <script src="' + name + '" defer></script>' for name in ['research-journey.js', 'learning-path.js', 'spatial-encoding.js', 'research-studio.js', 'academy.js']))
    text = text.replace('diffatonce-academy-1.2.0-win-x64', 'diffatonce-academy-1.3.0-win-x64')
    path.write_text(text, encoding="utf-8")
    path = web / "academy.js"
    text = path.read_text(encoding="utf-8")
    text = replace(text, "view=query.get('view')||'lesson'", "view=query.get('view')||'research'")
    text = replace(text, 'doctoralController=null,doctoralCases=null;', 'doctoralController=null,doctoralCases=null,researchController=null;')
    text = replace(text, "tabs=[['doctoral'", "tabs=[['research','Investigación','Research'],['doctoral'")
    text = replace(text, "if(view==='doctoral')view='lesson';", "if(['doctoral','research'].includes(view))view='lesson';")
    text = replace(text, "text('evidence',view==='doctoral'", "if(view==='research'){$('chapter').textContent=l('Investigación continua · 1.3','Continuous research · 1.3');$('title').textContent=l('De la pregunta a una conclusión defendible','From question to a defensible conclusion');$('objective').textContent=l('La misma muestra, decisiones conectadas y evidencias para revisión.','The same sample, connected decisions and evidence for review.');}text('evidence',view==='doctoral'")
    anchor = ' function doctoralView(){'
    addition = " function researchView(){researchController=window.AcademyResearchStudio.mount($('view'),language,{embedded,onView:id=>{const u=new URL(location.href);u.searchParams.set('research',id);history.replaceState(null,'',u);}});const wanted=new URL(location.href).searchParams.get('research');if(wanted)researchController.setView(wanted);}"
    text = replace(text, anchor, addition + anchor)
    text = replace(text, "language=lang;if(view==='doctoral'", "language=lang;if(view==='research'&&researchController){navigation();header();researchController.setLanguage(lang);const u=new URL(location.href);u.searchParams.set('lang',lang);history.replaceState(null,'',u);return;}if(view==='doctoral'")
    text = replace(text, 'function render(){doctoralController?.destroy();doctoralController=null;', 'function render(){researchController?.destroy();researchController=null;doctoralController?.destroy();doctoralController=null;')
    text = replace(text, "['derivations','doctoral'].includes(view)", "['derivations','doctoral','research'].includes(view)")
    text = replace(text, '({doctoral:doctoralView,lesson,', '({research:researchView,doctoral:doctoralView,lesson,')
    text = replace(text, 'snapshot:()=>({ready:!!course&&!mathPending,doctoral:', "selectResearchView:id=>{if(view!=='research'){view='research';render();}researchController.setView(id);},researchEvidence:()=>researchController?.exportEvidence()||null,receiveResearchTutor:answer=>researchController?.receiveTutor(answer),snapshot:()=>({ready:!!course&&!mathPending,research:researchController?.snapshot()||null,doctoral:")
    text = text.replace('diffatonce-academy-1.2.0-win-x64', 'diffatonce-academy-1.3.0-win-x64')
    path.write_text(text, encoding="utf-8")
    for name in ['research-library.json', 'research-tutor-knowledge.json']:
        shutil.copy2(ACADEMY / 'content' / name, web / 'content' / name)
    for source in (ACADEMY / 'content/research-data').rglob('*'):
        if source.is_file():
            target = web / 'content/research-data' / source.relative_to(ACADEMY / 'content/research-data')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    print('Research 1.3 browser integration and licensed public data prepared')


if __name__ == '__main__':
    main()
