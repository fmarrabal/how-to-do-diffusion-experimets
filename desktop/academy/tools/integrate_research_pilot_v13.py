from pathlib import Path
BASE=Path(__file__).resolve().parents[1]


def main():
 p=BASE/'web/research-studio.js';s=p.read_text(encoding='utf-8')
 changes=[
  ("let submissions=[],reviews=[],draft=", "let pilotController=null,pilotState=null,formCounter=0;const usedFormSeeds=new Set();\n   let submissions=[],reviews=[],draft="),
  ("function collect(){container.querySelectorAll", "function collect(){if(pilotController)pilotState=pilotController.snapshot();container.querySelectorAll"),
  ("prediction,predictionsByStage:clone(predictionsByStage)};", "prediction,predictionsByStage:clone(predictionsByStage),pilotState:pilotController?.snapshot()||pilotState};"),
  ("prediction:b.prediction||'',predictionsByStage:safePredictions};", "prediction:b.prediction||'',predictionsByStage:safePredictions,pilotState:b.pilotState||null};"),
  ("predictionsByStage=old.predictionsByStage;", "predictionsByStage=old.predictionsByStage;pilotState=old.pilotState;"),
  ("predictionsByStage=loaded.predictionsByStage;save();", "predictionsByStage=loaded.predictionsByStage;pilotState=loaded.pilotState;save();"),
  ("function render(){if(!alive)return;", "function render(){if(!alive)return;if(pilotController){pilotState=pilotController.snapshot();pilotController.destroy();pilotController=null;}"),
  ("${context()}</div>`;}", "${context()}</div>`;if(active==='competencies'&&root.AcademyResearchPilot){const place=container.querySelector('[data-research-pilot]');pilotController=root.AcademyResearchPilot.mount(place,lang,{initialState:pilotState,onChange:next=>{pilotState=next;save();},onLearningAttempt:attempt=>{learning=L.recordAttempt(learning,attempt);save();}});}}"),
  ("function action(name){collect();error=false;", "function action(name){collect();error=false;if(['hint','ask','native-tutor'].includes(name)&&pilotState?.derived?.activeQuestionCount>0)throw Error(t('Termina la fase piloto sin ayuda antes de solicitar pistas.','Complete the unaided pilot stage before requesting hints.'));"),
  ("diagnosticResult=null;hintLevel=0;form=L.makeDiagnostic({seed:(caseState.seed+Math.floor(now()/1000))>>>0,phase,count:7});", "diagnosticResult=null;hintLevel=0;let formSeed=((caseState.seed+now())^Math.imul(++formCounter,2654435761))>>>0;while(usedFormSeeds.has(formSeed))formSeed=(formSeed+1)>>>0;usedFormSeeds.add(formSeed);form=L.makeDiagnostic({seed:formSeed,phase,count:7});"),
  ("<p class=\"rs-scope\">${t('El piloto docente requiere participantes", "<div data-research-pilot></div><p class=\"rs-scope\">${t('El piloto docente requiere participantes"),
  ("publicCases:library?.cases?.length||0,spatialCalculated:", "publicCases:library?.cases?.length||0,pilot:pilotController?.snapshot().derived||pilotState?.derived||null,spatialCalculated:"),
  ("destroy(){collect();save();alive=false;worker?.terminate();", "destroy(){collect();save();alive=false;pilotController?.destroy();pilotController=null;worker?.terminate();"),
 ]
 for old,new in changes:
  if new in s:continue
  if s.count(old)!=1:raise ValueError('Pilot integration anchor '+old[:80]+' count '+str(s.count(old)))
  s=s.replace(old,new,1)
 p.write_text(s,encoding='utf-8')
 p=BASE/'web/index.html';s=p.read_text(encoding='utf-8');s=s.replace('  <script src="learning-path.js" defer></script>', '  <script src="learning-path.js" defer></script>\n  <script src="research-pilot-panel.js" defer></script>',1);p.write_text(s,encoding='utf-8')
 p=BASE/'web/academy.js';s=p.read_text(encoding='utf-8');s=s.replace('function render(){researchController?.destroy();', "function render(){document.body.classList.toggle('research-layout',view==='research');researchController?.destroy();",1);p.write_text(s,encoding='utf-8')
 p=BASE/'web/research-studio.css';s=p.read_text(encoding='utf-8');s+='\n/* The research pathway has its own stage navigation. */\n.research-layout .layout{grid-template-columns:1fr}.research-layout #sidebar,.research-layout #menu-toggle{display:none}.rs-main{scroll-margin-top:110px}.embedded .rs-main{scroll-margin-top:16px}\n';p.write_text(s,encoding='utf-8')
 print('Voluntary teaching pilot integrated, unaided-stage assistance guard active')


if __name__=='__main__':main()
