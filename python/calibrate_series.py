#!/usr/bin/env python3
"""Read-only offline wrapper for the same calibration core as TopSpin v2.

Input: independently acquired and processed, constant-timing 1D reference ramp.
Output: a new report folder. No instrument/API imports, acquisition or changes
to original spectra. Python >=3.8; standard library only.
"""
import argparse
import json
from pathlib import Path
import runpy
import sys

HERE = Path(__file__).resolve().parent


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset', type=Path, required=True, help='Directory containing EXPNO folders')
    p.add_argument('--expnos', required=True, help='Explicit range/list, e.g. 10-32 or 100,102,104,106')
    p.add_argument('--procno', type=int, default=1)
    p.add_argument('--ppm-low', type=float, required=True)
    p.add_argument('--ppm-high', type=float, required=True)
    p.add_argument('--dref', type=float, required=True, help='Reference D in 10^-9 m^2/s at the specified temperature')
    p.add_argument('--reference-temperature-k', type=float, required=True)
    p.add_argument('--reference-name', required=True)
    p.add_argument('--solvent', required=True)
    p.add_argument('--reference-source', required=True, help='DOI, URL or explicit documented laboratory source')
    p.add_argument('--max-temperature-span-k', type=float, default=0.5)
    p.add_argument('--max-reference-temperature-difference-k', type=float, default=0.5)
    p.add_argument('--confirm-sequence-mapping', action='store_true',
                   help='Confirm the saved sequence uses GPZ6, D20, P30, D16/GPNAM6 as expected; not automatic')
    p.add_argument('--out', type=Path, required=True, help='A new, non-existing folder outside the experimental dataset (required)')
    return p


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    if not args.confirm_sequence_mapping:
        p.error('Review the actual pulse program and add --confirm-sequence-mapping only after verifying the mapping')
    for name in ('reference_name', 'solvent', 'reference_source'):
        if not getattr(args, name).strip():
            p.error('--' + name.replace('_', '-') + ' must not be blank')
    if not args.dataset.is_dir():
        p.error('--dataset is not an existing directory')
    if args.out.exists():
        p.error('--out must not exist; original results are not overwritten')
    dataset = args.dataset.resolve()
    output = args.out.resolve()
    if dataset == output or dataset in output.parents:
        p.error('--out must be outside the experimental dataset to keep the input tree unchanged')
    bundle = HERE/'topspin_console'/'dist'/'dosy_workshop.py'
    if not bundle.is_file():
        p.error('Missing bundle: run python python/build_bundles.py first')
    # __main__ is deliberately NOT used: no TopCmds or hardware is loaded.
    runpy.run_path(str(bundle), run_name='_offline_calibration_bundle')
    ui = sys.modules['_dosy_console_ui']
    core = sys.modules['_dosy_calibration']
    reference = '%s / %s / %s' % (args.reference_name.strip(), args.solvent.strip(), args.reference_source.strip())
    try:
        result = core.analyze_series(str(dataset), ui.parse_expnos(args.expnos), args.procno,
                                    args.ppm_low, args.ppm_high, args.dref, args.reference_temperature_k,
                                    reference, args.max_temperature_span_k, args.max_reference_temperature_difference_k)
        result['sequence_mapping_confirmed_by_user'] = True
        result['bruker_gradient_proposal'] = ui.known_sequence_gradient(result)
        result['execution_mode'] = 'offline read-only; no instrument connection or automatic application'
        output.mkdir(parents=True, exist_ok=False)
        ui.write_json(str(output/'calibracion.json'), result)
        ui.write_text(str(output/'atenuacion_residuos.csv'), ui.csv_text(result['rows'],
            ['expno', 'procno', 'gradient_percent', 'x_gradient_fraction_squared', 'integral',
             'log_relative_intensity', 'predicted_integral', 'residual_log']))
        ui.write_text(str(output/'informe.html'), ui.make_report(result))
    except (ValueError, RuntimeError, OSError) as error:
        print('Calibration not completed: %s' % error, file=sys.stderr)
        return 1
    print(json.dumps({'output': str(output), 'points': result['fit']['n'],
                      'slope_abs': result['fit']['slope_abs'], 'R2': result['fit']['R2'],
                      'b_at_100_percent_s_m2': result['calibration_profile']['b_at_100_percent_s_m2'],
                      'status': 'candidate requiring spectral/reference/residual review; not applied to an instrument'}, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
