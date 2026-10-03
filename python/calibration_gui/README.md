# Spectrometer Calibration / Calibración del espectrómetro

Interfaz bilingüe ES/EN para preparar el instrumento, ajustar P1 del canal 1 y calibrar la escala DOSY mediante una señal de referencia. El archivo de distribución es `dist/spectrometer_calibration_gui.py`.

Bilingual ES/EN interface for instrument preparation, channel-1 P1 fitting and DOSY scale calibration from one reference signal. The distributable script is `dist/spectrometer_calibration_gui.py`.

## Español

### Inicio desde TopSpin

Desde la consola de comandos de TopSpin, con un dataset abierto:

```text
xpy C:/DiffAtOnce/python/calibration_gui/dist/spectrometer_calibration_gui.py
```

Si extraes el paquete en otro directorio, sustituye la ruta completa. Si tu instalación no admite esa forma de ruta en `xpy`, copia **solo el script autónomo** a `<TopSpin>/exp/stan/nmr/py/user` mediante el procedimiento habitual del laboratorio, conserva la versión anterior y ejecuta:

```text
xpy spectrometer_calibration_gui.py
```

Selecciona español o inglés en la propia ventana. El arranque no inicia adquisiciones. Primero utiliza **Leer dataset actual** para comprobar la comunicación GUI → `EXEC_PYSCRIPT` → CmdThread → `CURDATA`. Esta comprobación es distinta de ejecutar una adquisición o una calibración.

Al volver a ejecutar `xpy`, el lanzador trae al frente la ventana actual. Puede sustituir una versión anterior si está inactiva; conserva siempre una instancia con trabajo en curso y sus callbacks.

Requisitos: instalación TopSpin con su API `TopCmds`, Java/Jython y Swing; dataset con estructura directa `directorio/nombre/EXPNO/pdata/PROCNO`; plantillas revisadas; EXPNO de destino libres y un directorio de informes escribible. El script incluye el núcleo de cálculo y usa la biblioteca estándar. Un Python 3 externo sirve para pruebas del controlador, pero no sustituye al Jython integrado de TopSpin para la GUI o los comandos instrumentales.

El código está preparado para el flujo solicitado de TopSpin 3.6.4. **No se ha validado adquisición real en TopSpin 3.6.4.** La documentación instrumental consultada y el runtime Jython de prueba proceden de TopSpin 3.8.0; comprueba comandos, hardware y retorno de las operaciones en el sistema de destino.

### Demostración sin instrumento

Desde PowerShell:

```powershell
& 'C:\DiffAtOnce\python\calibration_gui\run_demo.ps1'
```

La única opción del lanzador es `-TopSpinRoot`. El valor por defecto es `C:\Bruker\TopSpin3.8.0`. Para usar el runtime de otra instalación:

```powershell
& 'C:\DiffAtOnce\python\calibration_gui\run_demo.ps1' -TopSpinRoot 'C:\Bruker\TopSpin3.6.4'
```

El lanzador localiza `jre/bin/java.exe` y el JAR `jython*.jar` de esa instalación y abre el bundle con `--demo`. No instala ni descarga dependencias. Si el runtime no existe, se detiene. La demostración crea archivos Bruker sintéticos en carpetas de sesión independientes y analiza esos archivos con el lector y los ajustes reales del programa; no conecta con `TopCmds`. Los datos ideales de demostración tienen P90 = 11 µs y b100 = 2 × 10⁹ s/m². Esos valores no son una calibración de tu instrumento.

### Secuencia de uso

1. **Equipo.** Comprueba dataset, muestra, sonda, canal y potencia. Crea primero una copia de preparación nueva; el EXPNO propuesto es **1050**, desde la plantilla P1 **1000**. `wraparam` copia parámetros, rechaza destinos existentes y verifica que no aparezcan `fid`, `ser` o espectros procesados. Se registran hashes del original y se restaura el dataset que estaba abierto.
2. **Preparación instrumental opcional.** Habilita por separado las capacidades presentes en tu equipo. Cada botón ejecuta una sola acción sobre la copia: LOCK (`lock -acqu`, con SOLVENT comprobado), ATMA (`atma`, requiere sonda ATM) o TOPSHIM (`topshim`, requiere configuración de sonda y lock revisado). La terminación de un comando no certifica lock estable, buena sintonía ni buena forma de línea. ATMA no calibra el pulso de 90°.
3. **Temperatura.** Habilita el controlador antes de consultar o cambiar la consigna. `teget` actualiza el TE guardado en la copia; `teset <K>` exige límites térmicos configurados por el operador. `GETPAR('TE')` es la consigna guardada y `GETPARSTAT('TE')` es un estado guardado; una lectura fresca del controlador tampoco demuestra por sí sola temperatura real de la muestra ni equilibrio. La revisión del equilibrio térmico y de D(T) sigue siendo una comprobación del operador.
4. **P1.** Usa una plantilla `zg` revisada, normalmente EXPNO 1000. Mantén constantes potencia RF, RG, NS, D1 y fase. Selecciona una señal aislada y un intervalo en ppm; incluye máximo positivo, primer nulo y señal negativa. El ajuste conserva el signo y usa `I(P1) = A·sin[π·P1/(2·P90)] + offset`, con búsqueda de P90 acotada. No rectifiques las integrales ni ajustes automáticamente la fase de cada espectro. En tu ejemplo, el primer nulo a P180 ≈ 22 µs conduce a P90 ≈ 11 µs, a esa potencia y canal; no es un valor universal.
5. **DOSY.** Usa la plantilla de difusión revisada, normalmente EXPNO 10, y configura GPZ6, región de integración, Dref en unidades de 10⁻⁹ m²/s, temperatura y fuente de Dref. Secuencia, forma de gradiente y tiempos se mantienen fijos durante la serie. P30, D20, D16, D5 y tiempos de doble eco estimulado proceden de la plantilla: comprueba su significado en el programa de pulsos. El ajuste de `ln(I/Imax)` frente a `(GPZ6/100)²` obtiene `b100 = |pendiente|/Dref` en s/m². La escala es específica del perfil experimental; cambiar Δ o la secuencia exige nueva calibración o un modelo verificado. Un b100 anterior opcional solo permite una comparación de escala, no reemplaza el ajuste empírico.
6. **Revisar y ejecutar.** Revisa plan, EXPNO y colisiones. **Preparar serie** crea solo los parámetros. **Adquirir y ajustar** adquiere y procesa cada punto mediante el flujo ZG/EFP después de las comprobaciones del operador. Puede utilizar la serie preparada por la misma instancia si sus parámetros no han cambiado. **Analizar serie** procesa el análisis de los espectros ya disponibles sin adquirir datos nuevos. **Parar tras punto** es cooperativo: termina el ZG/EFP en curso y no inicia el punto siguiente.
7. **Resultado.** Inspecciona espectros, integrales con signo, ajuste y residuos. Tras revisar un resultado P1, **Aplicar P1 a EXPNO nuevo** crea otra copia solo de parámetros; comprueba potencia RF y, cuando constan, núcleo y sonda, escribe P1 localmente y no adquiere. Los resultados DOSY se guardan como perfiles/propuestas para revisión; no modifican la calibración global del espectrómetro.

Los valores de EXPNO y las rampas mostradas son editables; no representan límites de hardware recomendados. Cada operación guarda un directorio nuevo con recibos, plan y resultados disponibles, incluidos JSON, CSV e informe DOSY HTML. Los destinos parciales se conservan para inspección. Las plantillas y los datos originales no se sobrescriben. La calibración compartida `calibracion/TBO_HDO_20260904.json` permanece separada y no debe reemplazarse por un gradiente nominal o por el resultado de la demostración.

Cargar ajustes restaura los valores editables, pero reinicia resultados y comprobaciones de muestra, hardware y revisión. Revisa de nuevo las condiciones de la sesión actual.

### Verificación y límites

Verificado el 3 de octubre de 2026: **51 pruebas simuladas** —18 del controlador y 33 de preparación instrumental— aprobadas en Jython 2.7.2. En CPython se aprueban las 41 pruebas portátiles y se omiten las 10 exclusivas de Java. Comprueban preservación de fuentes, colisiones, copias sin señales, signos, ajustes, parada entre puntos y rechazos por configuración o retornos no confirmados. Las pruebas Java inyectan `RuntimeException` para comprobar los recibos de fallo y la restauración del dataset; no conectan con el instrumento. `GUI_VERIFICATION.json` documenta el renderizado de componentes Swing y curvas sintéticas, también en ambos idiomas.

El lanzamiento nativo y la lectura de dataset de la GUI fuente previa a esta edición pública están **confirmados en TopSpin 3.8.0**. El bundle público reconstruido no se ha probado en un instrumento. El recibo `verification/native_pilot.json` registra que `EXEC_PYSCRIPT` recibe un callback mediante su argumento, lo ejecuta en `CmdThreadImpl` y lee `CURDATA`. Además, `verification/native_gui_pilot.json` confirma la acción **Leer dataset actual de la propia GUI**: empezó el callback, se obtuvo el contexto real y la ventana volvió al estado inactivo. Los identificadores y rutas privados se han redactado en los recibos públicos. Ambos recibos registran cero comandos de hardware, escrituras de parámetros y adquisiciones; se incluyen en el ZIP. Los auxiliares locales usados para el diagnóstico no se distribuyen. Ninguna prueba simulada, captura o lectura de contexto valida adquisición real, exactitud instrumental o compatibilidad completa con TopSpin 3.6.4.

Para repetir las pruebas del backend desde esta carpeta, conservando la dependencia hermana descrita al final:

```powershell
python -B -m unittest test_workflow test_instrument_setup
```

## English

### Launch from TopSpin

With a dataset open, enter this in the TopSpin command line:

```text
xpy C:/DiffAtOnce/python/calibration_gui/dist/spectrometer_calibration_gui.py
```

Replace the full path if you extract the package elsewhere. If your installation does not accept this path form in `xpy`, copy **the self-contained script only** to `<TopSpin>/exp/stan/nmr/py/user` using your laboratory's procedure, retain the earlier version and run:

```text
xpy spectrometer_calibration_gui.py
```

Choose English or Spanish in the window. Launching starts no acquisition. First use **Read current dataset** to check GUI → `EXEC_PYSCRIPT` → CmdThread → `CURDATA` communication. This read-only check is separate from acquiring data or calibrating hardware.

Running `xpy` again brings the current window to the front. The launcher can replace an older idle version; it always preserves an instance with an active job and its callbacks.

Prerequisites are an installed TopSpin environment with `TopCmds`, Java/Jython and Swing; a direct-layout dataset `directory/name/EXPNO/pdata/PROCNO`; reviewed templates; unused destination EXPNOs; and a writable reports directory. The bundle includes the calculation core and uses the standard library. External Python 3 can run backend tests but cannot replace TopSpin's integrated Jython for this GUI or instrument commands.

The code targets the requested TopSpin 3.6.4 workflow. **Live acquisition on TopSpin 3.6.4 has not been validated.** The inspected instrument documentation and the tested Jython runtime came from TopSpin 3.8.0. Verify command support, hardware configuration and command return behavior on the target system.

### Demo without an instrument

Run the following in PowerShell:

```powershell
& 'C:\DiffAtOnce\python\calibration_gui\run_demo.ps1'
```

The launcher's only option is `-TopSpinRoot`; its default is `C:\Bruker\TopSpin3.8.0`. To select another installed runtime:

```powershell
& 'C:\DiffAtOnce\python\calibration_gui\run_demo.ps1' -TopSpinRoot 'C:\Bruker\TopSpin3.6.4'
```

It locates that installation's `jre/bin/java.exe` and `jython*.jar`, then launches the bundle with `--demo`. It downloads and installs no dependencies and stops if the runtime is missing. The demo creates synthetic Bruker files in separate session directories and uses the actual reader and fitting code on those files; it does not connect to `TopCmds`. Its ideal example has P90 = 11 µs and b100 = 2 × 10⁹ s/m². These values are not a calibration of your instrument.

### Workflow

1. **Instrument.** Check the dataset, sample, probe, channel and RF power. First create a new preparation copy; the suggested EXPNO is **1050**, from P1 template **1000**. `wraparam` copies parameters, rejects existing destinations and verifies the absence of `fid`, `ser` and processed spectra. Source hashes are recorded and the previously open dataset is restored.
2. **Optional instrument preparation.** Enable only supported capabilities, separately. Each button dispatches one action on the working copy: LOCK (`lock -acqu`, checked SOLVENT), ATMA (`atma`, requires an ATM probe), or TOPSHIM (`topshim`, requires the configured probe and reviewed lock). Command completion does not certify stable lock, acceptable tuning or spectral line shape. ATMA does not calibrate the 90° pulse.
3. **Temperature.** Enable the controller before reading or changing its demand. `teget` updates the stored TE in the copy; `teset <K>` requires operator-configured temperature limits. `GETPAR('TE')` is the saved demand and `GETPARSTAT('TE')` is saved status. Even a fresh controller readback does not establish calibrated sample temperature or equilibration. Thermal equilibration and reference D(T) remain operator checks.
4. **P1.** Use a reviewed `zg` template, normally EXPNO 1000. Keep RF power, RG, NS, D1 and phase fixed. Choose an isolated signal and a ppm interval; include the positive maximum, first null and negative signal. The fit preserves sign and uses `I(P1) = A·sin[π·P1/(2·P90)] + offset` within a bounded P90 range. Do not rectify the integrals or autophase every spectrum independently. In the supplied example, the first null at P180 ≈ 22 µs gives P90 ≈ 11 µs at that power and channel; it is not a universal setting.
5. **DOSY.** Use the reviewed diffusion template, normally EXPNO 10. Configure GPZ6, the integration interval, Dref in units of 10⁻⁹ m²/s, temperature and the source for Dref. Sequence, gradient shape and timings remain fixed across the series. P30, D20, D16, D5 and double-stimulated-echo timings are inherited from the template: check their meaning in the pulse program. Fitting `ln(I/Imax)` against `(GPZ6/100)²` gives `b100 = |slope|/Dref` in s/m². This scale belongs to that experimental profile; changing Δ or sequence requires a new calibration or a verified model. An optional previous b100 is only a scale comparison and does not replace the empirical fit.
6. **Review and run.** Inspect the plan, EXPNOs and collisions. **Prepare series** creates parameters only. **Acquire and fit** acquires and processes each point through ZG/EFP after operator checks; it can reuse a series prepared by the same controller instance if its parameters remain unchanged. **Analyze series** analyzes already available spectra without acquiring new data. **Stop after point** is cooperative: the active ZG/EFP finishes and the next point does not start.
7. **Review the result.** Inspect spectra, signed integrals, fit and residuals. After reviewing a P1 result, **Apply P1 to new EXPNO** creates another parameter-only copy, checks RF power and recorded nucleus/probe information, and writes P1 locally without acquisition. DOSY results are saved as profiles/proposals for review; they do not alter the spectrometer's global gradient calibration.

The suggested EXPNOs and sweeps are editable and are not recommended hardware limits. Each operation gets a new output directory containing available receipts, plan and results, including JSON, CSV and the DOSY HTML report. Partial targets remain available for inspection. Original templates and experimental data are not overwritten. The shared `calibracion/TBO_HDO_20260904.json` remains separate and must not be replaced with a nominal gradient or demo output.

Loading settings restores editable values but resets results and sample, hardware and review checks. Review the current session conditions again.

### Verification and limitations

Checked on 3 October 2026: **51 simulated tests** —18 controller tests and 33 instrument-preparation tests— passed in Jython 2.7.2. CPython passes the 41 portable tests and skips the 10 Java-only tests. They exercise source preservation, collisions, parameter-only copies, signed fitting, stopping between points and rejection of invalid configuration or unconfirmed returns. Java tests inject `RuntimeException` to verify failure receipts and dataset restoration; they do not connect to the instrument. `GUI_VERIFICATION.json` records real Swing component rendering and synthetic curves in both languages.

Native launch and the read-only dataset handshake of the source GUI before this public edition are **confirmed in TopSpin 3.8.0**. The rebuilt public bundle has not been tested on an instrument. The receipt `verification/native_pilot.json` records that `EXEC_PYSCRIPT` receives a callback through its argument, runs it on `CmdThreadImpl` and reads `CURDATA`. In addition, `verification/native_gui_pilot.json` confirms the **GUI's own Read current dataset action**: its callback started, the actual context was returned and the GUI became idle again. Private identifiers and paths are redacted in the public receipts. Both receipts record zero hardware commands, parameter writes and acquisitions; they are included in the ZIP. The local diagnostic helper scripts are not distributed. Simulated tests, screenshots and context reads cannot validate live acquisition, instrument accuracy or full TopSpin 3.6.4 compatibility.

To rerun backend tests from this directory, preserve the sibling dependency below:

```powershell
python -B -m unittest test_workflow test_instrument_setup
```

## Archivos y distribución / Files and distribution

`dist/spectrometer_calibration_gui.py` is self-contained for deployment: it embeds the v3 core, workflow controller, instrument setup and GUI. The readable sources remain alongside it. The source backend has a fallback import of `../topspin_console_v3/dist/dosy_workshop_v3.py`; preserve that sibling path for tests and rebuilding. `test_workflow.py` imports this backend, so distributing only the source files without the fallback bundle breaks those tests. The GUI itself needs Swing/Jython; the backend tests do not.

El script de `dist` es autónomo para el despliegue. Para probar o reconstruir las fuentes, conserva la estructura hermana siguiente; no basta con entregar los tests y `calibration_workflow.py` sin el bundle v3.

Extract the standalone public ZIP into `C:/DiffAtOnce/python/` to use the example paths above, or adjust those paths to your checkout. The ZIP includes the application sources, backend tests, source hashes, two PDF manuals, 24 screenshots and verification receipts. Original experimental datasets, the shared TBO calibration and Bruker's installation manuals remain external reference sources and are not included in the package.

Extrae el ZIP público independiente en `C:/DiffAtOnce/python/` para usar las rutas de ejemplo, o adáptalas a tu checkout. El ZIP incluye fuentes de la aplicación, tests del backend, hashes, dos manuales PDF, 24 capturas y recibos de verificación. Los datos experimentales originales, la calibración TBO compartida y los manuales de la instalación Bruker son fuentes externas y no se incluyen en el paquete.

```text
package/
  MANIFEST_SHA256.json
  calibration_gui/
    README.md
    run_demo.ps1
    dist/
      spectrometer_calibration_gui.py
      sources_sha256.json
    PUBLICATION_PROVENANCE.json
    gui.py
    calibration_workflow.py
    instrument_setup.py
    build_bundle.py
    backend_contract.json
    test_workflow.py
    test_instrument_setup.py
    GUI_VERIFICATION.json
    RELEASE_VERIFICATION.json
    verification/
      native_pilot.json
      native_gui_pilot.json
    screenshots/
      [24 PNG images, ES/EN]
    output/pdf/
      Manual_Calibracion_Espectrometro_ES.pdf
      Spectrometer_Calibration_Manual_EN.pdf
  topspin_console_v3/
    dist/
      dosy_workshop_v3.py
```

The source rebuild requires Python 3: run `python build_bundle.py` from `calibration_gui`. It rewrites the generated script and its source-hash manifest, not the experimental data. Local bytecode/cache folders and generated demo sessions are not runtime dependencies.

La reconstrucción de fuentes requiere Python 3: ejecuta `python build_bundle.py` desde `calibration_gui`. Regenera el bundle y su manifiesto de hashes, sin modificar datos experimentales. Las cachés/bytecode y las sesiones de demostración generadas no son dependencias de ejecución.

## Documentación primaria / Primary documentation

Command syntax and thread behavior were checked against the local Bruker manuals in `C:/Bruker/TopSpin3.8.0/prog/docu/English/topspin/pdf/`:

- `python.pdf`, pp. 7–8 and 20–21: `EXEC_PYSCRIPT`, `EXEC_PYFILE`, `XCMD` and the CmdThread requirement. A generic Python worker or Swing listener must not directly run the critical TopSpin calls.
- `acquisition-reference.pdf`, p. 37, pp. 114–116 and 199–201: TE demand, lock, `teget` and `teset`.
- `Atma.pdf`, pp. 19–20: ATM probe requirement and automatic tune/match.
- `topshim.pdf`, pp. 5–9: hardware prerequisites and configured TopShim operation.

Public mirrors of Bruker-authored manuals: [ATM manual](https://2210pc.chem.uic.edu/nmr/downloads/bruker/en-US/pdf/z31510.pdf) and [Acquisition Reference](https://chemistry.beloit.edu/classes/instruments/Manuals/Bruker_acquisition-reference%202017.pdf). Documentation establishes command semantics, not successful execution on a particular spectrometer.
