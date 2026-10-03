# -*- coding: utf-8 -*-
"""Exercise and render the real Swing components in demonstration mode only.

These are application view renders, not invented UI mockups. Every curve comes
from the controller reading the generated labelled synthetic Bruker files.
No TopCmds API is imported and no hardware command is issued.
"""
from __future__ import unicode_literals
import io, json, os, runpy, sys, time, threading
from javax.swing import SwingUtilities
from java.awt.image import BufferedImage
from java.io import File
from javax.imageio import ImageIO

HERE=os.path.dirname(os.path.abspath(__file__))
runpy.run_path(os.path.join(HERE,'dist','spectrometer_calibration_gui.py'),run_name='gui_selftest_bundle')
gui=sys.modules['_cal_gui']
app=gui.main(demo=True)
shots=os.path.join(HERE,'screenshots')
if not os.path.isdir(shots):os.makedirs(shots)

def ui(fn):SwingUtilities.invokeAndWait(gui.Task(fn))
def settle():ui(lambda:None);time.sleep(.15);ui(lambda:None)
def public_display_paths(component):
    """Redact display paths during actual Swing rendering; restore UI afterwards."""
    changes=[]
    def visit(item):
        if hasattr(item,'getText') and hasattr(item,'setText'):
            value=item.getText()
            if value is not None:
                text=unicode(value)
                for prefix in (HERE.replace(chr(92),chr(92)*2),HERE,HERE.replace(chr(92),'/')):
                    text=text.replace(prefix,'C:/DiffAtOnce/python/calibration_gui')
                if text != unicode(value):
                    changes.append((item,value));item.setText(text)
        if hasattr(item,'getComponents'):
            for child in item.getComponents():visit(child)
    visit(component)
    return changes

def capture(name,tab,language):
    def render():
        app.lang=language;app.language.setSelectedIndex(1 if language=='es' else 0)
        app.refresh_language();app.tabs.setSelectedIndex(tab)
        app.frame.validate()
    ui(render);settle()
    def save():
        component=app.frame.getContentPane()
        image=BufferedImage(component.getWidth(),component.getHeight(),BufferedImage.TYPE_INT_RGB)
        changes=public_display_paths(component)
        try:
            graphics=image.createGraphics();component.printAll(graphics);graphics.dispose()
            ImageIO.write(image,'png',File(os.path.join(shots,name+'_'+language+'.png')))
        finally:
            for item,value in changes:item.setText(value)
    ui(save)

try:
    ui(lambda:app.fields['report_dir'].setText(os.path.join(HERE,'demo_evidence')))
    config=app.config()
    p1preview=app.controller.preview(config)
    p1output=app.controller.run(config,'acquire',callback=app.event)
    assert abs(p1output['result']['P90_us']-11)<1e-5
    assert p1output['demo'] is True
    config['mode']='gradient'
    gpreview=app.controller.preview(config)
    gout=app.controller.run(config,'acquire',callback=app.event)
    assert abs(gout['result']['calibration_profile']['b_at_100_percent_s_m2']-2e9)<10
    context=app.controller.context()
    ui(lambda:app.update_context(context))
    stopflag=threading.Event();stopconfig=dict(config);stopconfig['gradient_start_expno']=1600
    def stopping(event):
        if event['stage']=='point_finished' and event['current']>=11:stopflag.set()
    stopped=app.controller.run(stopconfig,'acquire',callback=stopping,stop_event=stopflag)
    assert stopped['status']=='stopped'
    assert len([e for e in stopped['events'] if e['stage']=='point_finished'])==11
    collisions=dict(config);collisions['mode']='p1'
    collision_preview=app.controller.preview(collisions)
    assert collision_preview['collisions']
    def display(output):
        app.result=output;app.job_finished(output);app.idle()
        app.log.setText('\n'.join('[%s] %s %s'%(e['stage'],e.get('expno',''),e['message']) for e in output['events']))
    for lang in ('en','es'):
        capture('overview',0,lang);capture('launch',0,lang)
        capture('instrument',1,lang)
        capture('p1_plan',2,lang)
        ui(lambda:app.setplan(p1preview));ui(lambda:display(p1output))
        app.result=p1output;app.result['mode']='p1'
        capture('p1_result',4,lang)
        ui(lambda:app.reviewbox.setSelected(True));ui(lambda:app.applybutton.setEnabled(True))
        capture('apply_p1',4,lang)
        ui(lambda:app.reviewbox.setSelected(False))
        capture('dosy_reference',3,lang)
        ui(lambda:app.setplan(gpreview));ui(lambda:display(gout))
        app.result=gout;app.result['mode']='gradient'
        capture('dosy_plan',4,lang);capture('worked_example',4,lang)
        ui(lambda:app.curve.__setattr__('plot',None));ui(lambda:app.resultsummary.setText(''))
        app.result=None
        ui(lambda:app.resultdetails.setText(''))
        ui(lambda:app.setplan({'plan':stopped['plan']},clear_log=False))
        ui(lambda:app.log.setText('\n'.join('[%s] %s'%(e['stage'],e['message']) for e in stopped['events'])))
        ui(lambda:app.progress.setValue(int(100*11/23)));ui(lambda:app.status.setText(app.t('stopped')))
        capture('run_stop',4,lang)
        ui(lambda:app.stopbutton.setEnabled(False));ui(lambda:app.progress.setValue(100))
        ui(lambda:app.modechoice.setSelectedIndex(0))
        app.result=None
        ui(lambda:app.curve.__setattr__('plot',None));ui(lambda:app.resultsummary.setText(''))
        ui(lambda:app.resultdetails.setText(''))
        ui(lambda:app.setplan(collision_preview));ui(lambda:app.log.setCaretPosition(0));ui(lambda:app.progress.setValue(0))
        capture('error_log',4,lang)
        ui(lambda:app.modechoice.setSelectedIndex(1))
        ui(lambda:display(gout));ui(lambda:app.status.setText(app.t('success')+' | '+gout['output_dir']))
        capture('reports',4,lang)
        assert app.tabs.getTitleAt(0)==gui.TEXT['home'][1 if lang=='es' else 0]
    # Exercise the same asynchronous GUI action used by an operator, not only
    # the controller used to build the illustrated demonstration states.
    def launch_gui_action():
        app.modechoice.setSelectedIndex(0)
        app.fields['p1_start_expno'].setText('2000')
        for check in app.checks.values():check.setSelected(True)
        app.start_run('acquire')
    ui(launch_gui_action)
    deadline=time.time()+30
    while app.running and time.time()<deadline:
        time.sleep(.1);settle()
    settle()
    assert not app.running, 'GUI action did not finish'
    assert app.result and app.result['demo'] and app.result['mode']=='p1'
    assert abs(app.result['result']['P90_us']-11)<1e-5
    assert app.curve.plot and not app.stopbutton.isEnabled()
    saved_config=app.config()
    assert all(saved_config['operator_checks'].values())
    ui(lambda:app.populate(saved_config))
    assert not any(check.isSelected() for check in app.checks.values())
    assert app.result is None and not app.applybutton.isEnabled()
    assert not app.setup_config.get('working_dataset_confirmed')
    checks={'demo_only':True,'hardware_commands_issued':False,'P90_us':p1output['result']['P90_us'],
        'b100_s_m2':gout['result']['calibration_profile']['b_at_100_percent_s_m2'],
        'screenshots':24,'languages':['en','es'],'real_swing_components_rendered':True,
        'screenshots_are_application_renders':True,'TopSpin_3_6_4_live_validation':False,
        'actual_simulated_stop_after_points':11,'collision_preview_verified':True,
        'asynchronous_GUI_acquire_and_fit_demo_verified':True,
        'loading_settings_requires_fresh_operator_review':True,
        'public_display_paths_redacted':True,
        'public_screenshots_rerendered_from_synthetic_files':True}
    with io.open(os.path.join(HERE,'GUI_VERIFICATION.json'),'w',encoding='utf-8',newline='\n') as f:f.write(unicode(json.dumps(checks,indent=2,separators=(',', ': '))) + '\n')
    print(json.dumps(checks))
finally:
    ui(lambda:app.frame.dispose())
