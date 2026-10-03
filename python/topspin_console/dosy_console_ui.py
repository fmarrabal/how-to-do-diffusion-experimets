# -*- coding: utf-8 -*-
"""Native TopSpin dialogs. Jython 2.7 / CPython 3 standard library only."""
from __future__ import print_function, unicode_literals
import datetime
import io
import json
import math
import os
import re
import uuid
import _dosy_ramp_engine as ramp
import _dosy_calibration as calibration

TBO_PROFILE = {}
TBO_MODEL_SOURCE_SHA256 = ''
try:
    text_type = unicode
except NameError:
    text_type = str

def ask(api, title, labels, defaults, header=''):
    result = api.INPUT_DIALOG(title, header, labels, [text_type(v) for v in defaults],
                              [''] * len(labels), ['1'] * len(labels))
    if result is None:
        return None
    return [text_type(v).strip() for v in result]

def current_dataset(api):
    data = api.CURDATA()
    if not data or len(data) != 4:
        raise ValueError('Abra un dataset [nombre, EXPNO, PROCNO, directorio].')
    name = text_type(data[0])
    if name in ('.', '..') or any(c in name for c in ('/', '\\', '\x00')):
        raise ValueError('Nombre de dataset no admitido.')
    folder = os.path.realpath(os.path.join(text_type(data[3]), name))
    if not os.path.isdir(folder):
        raise ValueError('Dataset no encontrado: ' + folder)
    return list(data), folder

def positive(value, label):
    number = float(value)
    if math.isnan(number) or math.isinf(number) or number <= 0:
        raise ValueError(label + ': debe ser positivo y finito.')
    return number

def parse_expnos(text):
    result = []
    for term in text.split(','):
        term = term.strip()
        if re.match(r'^\d+-\d+$', term):
            lo, hi = [int(v) for v in term.split('-')]
            if hi < lo or hi-lo > 10000:
                raise ValueError('Rango EXPNO invalido.')
            result.extend(range(lo, hi+1))
        elif re.match(r'^\d+$', term):
            result.append(int(term))
        else:
            raise ValueError('EXPNO: use 10-32 o 10,12,14. Sin decimales.')
    if not result or min(result) <= 0 or len(result) > 10000 or len(set(result)) != len(result):
        raise ValueError('EXPNO positivos, sin duplicados; maximo 10000.')
    return result

def report_base():
    return os.path.join(os.path.expanduser('~'), 'DiffAtOnce_DOSY')

def new_report_dir(base, kind):
    base = os.path.abspath(os.path.expanduser(base))
    if not os.path.isdir(base):
        os.makedirs(base)
    stamp = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    target = os.path.join(base, kind + '_' + stamp + '_' + uuid.uuid4().hex[:8])
    os.mkdir(target)
    return target

def write_text(path, text):
    if not isinstance(text, text_type):
        text = text.decode('utf-8')
    with io.open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)

def write_json(path, value):
    write_text(path, json.dumps(value, ensure_ascii=True, indent=2))

def csv_text(rows, keys):
    def quote(value):
        if value is None:
            return ''
        if isinstance(value, (list, dict)):
            value = json.dumps(value, ensure_ascii=True, sort_keys=True)
        text = text_type(value)
        return '"' + text.replace('"', '""') + '"'
    return '\n'.join([','.join(quote(k) for k in keys)] +
                     [','.join(quote(row.get(k)) for k in keys) for row in rows]) + '\n'

def ramp_flow(api):
    current, folder = current_dataset(api)
    program = text_type(api.GETPAR('PULPROG')).strip().strip('<>')
    values = ask(api, 'DOSY: configurar rampas',
        ['EXPNO plantilla', 'PROCNO plantilla', 'Primer EXPNO destino',
         'Salto EXPNO entre rampas', 'GPZ inicial (%)', 'GPZ final (%)',
         'Paso GPZ (%)', 'Indice GPZ', 'DS en cada destino (vacio: heredar)',
         'Programa de pulsos esperado'],
        [current[1], current[2], '100', '100', '8', '96', '4', '6', '16', program],
        'Copias de parametros de una plantilla 1D. P30 y RG se conservan.')
    if values is None:
        return
    times = ask(api, 'DOSY: tiempos de difusion',
        ['Parametro del tiempo (p. ej. D20)', 'Valores en ms, separados por coma',
         'Numero de repeticiones si deja los tiempos vacios', 'Carpeta de informes'],
        ['D20', '50,100,150', '3', report_base()],
        'Verifique el parametro en su secuencia. stebpgp1s1d: D20 = Delta grande; delta pequena = 2*P30.')
    if times is None:
        return
    delays = [positive(v.strip(), 'Delta')/1000.0 for v in times[1].split(',')] if times[1] else None
    cfg = {'template_expno': int(values[0]), 'template_procno': int(values[1]),
           'start_expno': int(values[2]), 'experiment_stride': int(values[3]),
           'gradient_start_percent': values[4], 'gradient_stop_percent': values[5],
           'gradient_step_percent': values[6], 'gradient_index': int(values[7]),
           'dummy_scans': int(values[8]) if values[8] else None,
           'expected_pulse_program': values[9], 'expected_dataset_name': text_type(current[0]),
           'delay_parameter': times[0] if delays is not None else None,
           'delay_values_s': delays, 'ramp_count': len(delays) if delays is not None else int(times[2]),
           'delay_mapping_confirmed': delays is not None, 'example_only': False}
    plan = ramp.build_plan(cfg)
    plan['generator'] = 'DiffAtOnce native TopSpin DOSY assistant 2.0'
    summary = ('Dataset: %s\nPlantilla: %s/%s\n%d rampas x %d puntos = %d experimentos\n'
               'GPZ%d: %s a %s %%\nTiempos D (s): %s\nP30, RG y forma: heredados\n\n') % (
               current[0], cfg['template_expno'], cfg['template_procno'], cfg['ramp_count'],
               plan['points_per_ramp'], plan['experiment_count'], cfg['gradient_index'],
               values[4], values[5], str(delays))
    table = csv_text(plan['rows'], ['ramp','point','expno','gradient_percent','delay_s','dummy_scans'])
    api.VIEWTEXT('Plan DOSY', 'Revise destinos, tiempos y limites del equipo', summary + table)
    choice = api.SELECT('Preparar DOSY', summary +
        'Crear confirma el mapeo del tiempo en la secuencia. Los destinos deben estar libres.',
        ['Crear experimentos', 'Exportar plan solamente', 'Cancelar'])
    if choice not in (0, 1):
        return
    output = new_report_dir(times[3], 'rampas')
    write_json(os.path.join(output,'plan.json'), plan)
    write_text(os.path.join(output,'plan.csv'), table)
    if choice == 0:
        try:
            created = ramp.prepare(api, plan)
        except Exception as error:
            write_json(os.path.join(output,'preparacion.json'), {'status':'failed','error':str(error)})
            raise
        write_json(os.path.join(output,'preparacion.json'), {'status':'prepared','created':created,'acquisition_started':False})
    api.MSG(('Experimentos preparados. ' if choice == 0 else 'Plan exportado. ') +
            'No se ha iniciado adquisicion.\n' + output)

def calibration_summary(result):
    return json.dumps({key:result.get(key) for key in
        ('bruker_gradient_proposal','fit','calibration_profile','temperature','warnings')}, ensure_ascii=True, indent=2)

def known_sequence_gradient(result):
    """Conditional physical G from the exact saved TBO pulse/shape model.

    Never use the nominal installed constant. Different pulse/shape bytes do
    not inherit this sequence-specific model just because names are similar.
    """
    profile = result['calibration_profile']
    scope = profile['scope']
    if (scope.get('PULPROG') != 'stebpgp1s1d' or scope.get('NUC1') != '1H' or
            scope.get('GPNAM6') != 'SMSQ10.100' or not TBO_MODEL_SOURCE_SHA256):
        return None
    for filename in ('pulseprogram','gpnam6'):
        hashes = set(source['sha256'] for source in TBO_PROFILE.get('sources',[])
                     if source['path'].replace('\\','/').split('/')[-1] == filename)
        if len(hashes) != 1 or profile.get('saved_file_hashes',{}).get(filename) not in hashes:
            return None
    delta = 2.0 * positive(scope['P30'],'P30') * 1e-6
    effective_time = float(scope['D20']) - .32525 * delta - float(scope['D16']) / 2.0
    if effective_time <= 0:
        raise ValueError('Tiempo efectivo de la secuencia no positivo.')
    gamma = 267.52218744e6
    shape_squared = float(TBO_PROFILE['shape_squared'])
    b100 = positive(profile['b_at_100_percent_s_m2'],'b100')
    coefficient_per_G2 = (gamma*delta)**2 * shape_squared * effective_time
    g = math.sqrt(b100/coefficient_per_G2)
    return {'G_max_T_m':g,'G_max_G_cm':g*100.0,'G_max_G_mm':g*10.0,
            'G_relative_SE_regression_only':result['fit']['relative_slope_uncertainty_1sigma']/2.0,
            'model':'b100 = (gamma*Gmax*delta)^2 * shape_squared * (D20-0.32525*delta-D16/2)',
            'delta_s':delta,'effective_time_s':effective_time,'gamma_rad_s_T':gamma,
            'shape_squared':shape_squared,'source':'documented local sequence model; python/sequence_model.json',
            'model_source_sha256':TBO_MODEL_SOURCE_SHA256,
            'identity_check':'saved pulseprogram and gpnam6 SHA-256 equal the documented model identity',
            'status':'derived proposal; spectral/reference review required; not applied to Bruker',
            'uncertainty_scope':'regression only; excludes Dref, temperature and pulse-model uncertainty'}

def escape_html(value):
    return text_type(value).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

def fit_svg(result, residual=False):
    rows, fit = result['rows'], result['fit']
    x = [r['x_gradient_fraction_squared'] for r in rows]
    y = [r['residual_log'] if residual else r['log_relative_intensity'] for r in rows]
    lo, hi = min(y+[0.0]), max(y+[0.0])
    if not residual:
        model = [fit['intercept_log_I_over_Imax']+fit['slope']*v for v in x]
        lo, hi = min(y+model+[0.0]), max(y+model+[0.0])
    span = max(hi-lo, 1e-6)
    lo, hi = lo-.12*span, hi+.12*span
    xmax = max(max(x)*1.04, .01)
    sx = lambda v: 90+v/xmax*880
    sy = lambda v: 310-(v-lo)/(hi-lo)*240
    title = 'Residuos del ajuste' if residual else 'Atenuacion e intercepto libre'
    svg = '<svg viewBox="0 0 1040 390" role="img" aria-label="'+title+'"><text x="90" y="32" font-size="23">'+title+'</text>'
    svg += '<path d="M90 70V310H970" fill="none" stroke="#122e40"/>'
    for j in range(5):
        xx, yy = xmax*j/4, lo+(hi-lo)*j/4
        svg += '<text x="%.2f" y="338" text-anchor="middle">%.3g</text>' % (sx(xx),xx)
        svg += '<text x="80" y="%.2f" text-anchor="end">%.3g</text>' % (sy(yy)+5,yy)
    if residual:
        svg += '<path d="M90 %.3fH970" stroke="#b56525" stroke-dasharray="5 5"/>' % sy(0)
    else:
        pairs = sorted(zip(x,model))
        svg += '<polyline points="'+ ' '.join('%.3f,%.3f'%(sx(a),sy(b)) for a,b in pairs)+'" fill="none" stroke="#b56525" stroke-width="3"/>'
    for xx,yy in zip(x,y):
        svg += '<circle cx="%.3f" cy="%.3f" r="4" fill="#087e98"/>'%(sx(xx),sy(yy))
    ylabel = 'Residuo logaritmico' if residual else 'ln(I / Imax)'
    return svg + '<text x="510" y="377" text-anchor="middle">(GPZ / 100)^2</text><text transform="translate(23 210) rotate(-90)" text-anchor="middle">'+ylabel+'</text></svg>'

def make_report(result):
    # The JSON retains all precision and diagnostics; charts are a display of those values.
    rows = result['rows']
    body = '<!doctype html><meta charset="utf-8"><title>Calibracion DOSY</title>'
    body += '<style>body{font:17px system-ui;background:#f5f2ea;color:#122e40;max-width:1100px;margin:40px auto}svg{background:white;width:100%;margin:12px 0}pre{white-space:pre-wrap}table{border-collapse:collapse;font-size:14px}td,th{border:1px solid #bcc;padding:8px}</style>'
    body += '<h1>Calibracion DOSY del patron</h1><p>Integral firmada en una region ppm fija. Ajuste con intercepto libre. La escala empirica se limita a las condiciones registradas.</p>'
    body += fit_svg(result) + fit_svg(result,True)
    body += '<pre>' + escape_html(calibration_summary(result)) + '</pre>'
    keys = ['expno','gradient_percent','integral','predicted_integral','residual_log']
    body += '<table><tr>' + ''.join('<th>'+escape_html(k)+'</th>' for k in keys) + '</tr>'
    for row in rows:
        body += '<tr>' + ''.join('<td>'+escape_html(row.get(k,''))+'</td>' for k in keys) + '</tr>'
    return body + '</table>'

def open_report(path):
    try:
        from java.awt import Desktop
        from java.io import File
        Desktop.getDesktop().browse(File(path).toURI())
    except ImportError:
        import webbrowser
        webbrowser.open('file://' + os.path.abspath(path).replace('\\','/'))

def calibration_flow(api):
    current, folder = current_dataset(api)
    selection = ask(api, 'Calibracion DOSY: serie del patron',
        ['EXPNO (p. ej. 10-32 o 100,102,104)', 'PROCNO', 'Limite ppm inferior',
         'Limite ppm superior', 'Carpeta de informes'],
        ['', current[2], '', '', report_base()],
        'Use la region del patron de ESTA muestra. Espectros procesados 1D con fase, linea base y escala comparables.')
    if selection is None:
        return
    references = ask(api, 'Calibracion DOSY: referencia y temperatura',
        ['Patron, disolvente y fuente del D de referencia',
         'D de referencia a esa T (en 10^-9 m2/s)', 'Temperatura de referencia (K)',
         'Maxima variacion TE de la serie (K)', 'Maxima diferencia de cada TE frente a T referencia (K)'],
        ['', '', '', '0.5', '0.5'],
        'D de referencia obligatorio. 1.902 para HDO/D2O corresponde a 298.15 K; no se impone a otra temperatura.')
    if references is None:
        return
    result = calibration.analyze_series(folder, parse_expnos(selection[0]), int(selection[1]),
        float(selection[2]), float(selection[3]), positive(references[1],'D referencia'),
        positive(references[2],'T referencia'), references[0],
        max_temperature_span_K=positive(references[3],'Variacion TE'),
        max_reference_temperature_difference_K=positive(references[4],'Diferencia T'))
    result['bruker_gradient_proposal'] = known_sequence_gradient(result)
    output = new_report_dir(selection[4], 'calibracion')
    write_json(os.path.join(output,'calibracion.json'),result)
    keys = sorted(set(k for row in result['rows'] for k in row))
    write_text(os.path.join(output,'atenuacion_residuos.csv'),csv_text(result['rows'],keys))
    report = os.path.join(output,'informe.html')
    write_text(report,make_report(result))
    api.VIEWTEXT('Calibracion DOSY', 'Resultado y diagnosticos',
        calibration_summary(result) + '\n\nGuardado en: ' + output +
        '\nLa escala b/GPZ^2 es experimental. No cambia la constante global de Bruker. No se incluye una calibracion experimental de ejemplo aplicable a su equipo.')
    proposal = result['bruker_gradient_proposal']
    buttons = ['Abrir informe','Abrir gradpar','Cerrar'] if proposal else ['Abrir informe','Cerrar']
    message = output
    if proposal:
        message += '\n\nG propuesta: %.9g G/cm = %.9g G/mm' % (proposal['G_max_G_cm'],proposal['G_max_G_mm'])
    choice = api.SELECT('Resultado DOSY', message, buttons)
    if choice == 0:
        open_report(report)
    elif proposal and choice == 1:
        api.XCMD('gradpar',wait=api.WAIT_TILL_DONE)
        api.MSG('G propuesta: %.9g G/cm = %.9g G/mm.\nRevise el ajuste y la referencia antes de introducirla. Guardado por sonda: setpre > File > Write.' % (proposal['G_max_G_cm'],proposal['G_max_G_mm']))

def gradient_flow(api):
    values = ask(api,'Calibracion Bruker: constante de gradiente',
        ['G anterior usada al calcular D medido', 'Unidad G (G/cm o G/mm)',
         'D medido con esa G (10^-9 m2/s)', 'D referencia (10^-9 m2/s)',
         'T referencia (K)', 'Patron, disolvente y fuente', 'Carpeta de informes'],
        ['', 'G/cm', '', '', '', '', report_base()],
        'Introduzca valores del mismo analisis. No se carga el gradiente nominal de la instalacion.')
    if values is None:
        return
    if values[1] not in ('G/cm','G/mm'):
        raise ValueError('Unidad G admitida: G/cm o G/mm, sin conversion implicita.')
    gold, dm, dr = [positive(values[n], 'Dato de calibracion') for n in (0,2,3)]
    temp = positive(values[4], 'T referencia')
    if not values[5]:
        raise ValueError('Indique patron, disolvente y fuente.')
    gnew = calibration.gradient_correction(gold,dm,dr,values[1])['new_gradient_constant']
    result = {'G_old':gold,'G_new':gnew,'G_unit':values[1], 'D_measured_1e9':dm,
              'D_reference_1e9':dr,'temperature_K':temp,'reference':values[5],
              'formula':'G_new = G_old * sqrt(D_measured / D_reference)',
              'instrument_calibration_modified':False}
    output = new_report_dir(values[6], 'constante_gradiente')
    write_json(os.path.join(output,'constante_propuesta.json'),result)
    text = 'G nueva = %.9g %s\n\n%s\n\nGuardado: %s\nEl valor calculado debe revisarse en el editor de la sonda.' % (gnew,values[1],result['formula'],output)
    if api.SELECT('Constante calculada',text,['Abrir gradpar','Cerrar']) == 0:
        api.XCMD('gradpar',wait=api.WAIT_TILL_DONE)
        api.MSG('Valor calculado: %.9g %s\nPara guardar en la sonda: setpre > File > Write.\nNo se han editado archivos globales desde este asistente.\nSi cambia la constante, regenere difflist con xau dosy restore sobre una copia de analisis.' % (gnew,values[1]))

def tbo_flow(api):
    keys = ['id','pulse_program','gradient_shape','shape_squared','equation','scope','status']
    text = json.dumps({key:TBO_PROFILE.get(key) for key in keys},ensure_ascii=True,indent=2)
    api.VIEWTEXT('Modelo de secuencia documentado / Documented sequence model','sequence_model.json',text +
        '\n\nNo es una calibracion de su sonda. No contiene datos experimentales ni Dref predefinida.\nNot a probe calibration. No experimental data or default Dref is included.')

def main(api):
    try:
        action = api.SELECT('DiffAtOnce DOSY','Rampas y calibracion desde TopSpin',
            ['Preparar rampas','Calibrar con serie 1D','Constante Bruker desde D medido','Ver modelo de secuencia','Salir'])
        if action == 0:
            ramp_flow(api)
        elif action == 1:
            calibration_flow(api)
        elif action == 2:
            gradient_flow(api)
        elif action == 3:
            tbo_flow(api)
    except Exception as error:
        api.MSG('DOSY: ' + str(error))
