# Solución de problemas de las herramientas Bruker del workshop

[Inicio del repositorio](../../README.md) · [Guía paso a paso](bruker-paso-a-paso.md) · [Referencias](../../references/README.md) · [English](../en/troubleshooting.md)

Estos pasos son de diagnóstico, no instrucciones para saltarse las protecciones del instrumento. Conserve espectros originales, carpetas parciales y registros. No inicie una adquisición para comprobar si una configuración fallida se arregla sola. La adquisición real y la compatibilidad TopSpin 3.6.4 siguen sin validarse; las pruebas simuladas no cambian ese límite.

## No arranca el generador externo

- Compruebe `python --version`; requiere Python 3.8 o posterior. Ejecute desde la raíz, con las rutas `python/ramp_generator/` de la [guía](bruker-paso-a-paso.md).
- Si `--gui` indica que falta Tkinter, utilice una distribución Python que lo incluya o la CLI. La CLI no necesita Tkinter.
- `--gui` no se combina con `--config` ni `--out`. Consulte las opciones reales con `python python/ramp_generator/generate_ramps.py --help`.
- Se rechaza una carpeta de salida existente incluso vacía. Elija otra nueva; no sustituya un plan previo.
- El paso debe alcanzar exactamente el extremo del gradiente. Revise inicio/final/paso, recuentos y rangos EXPNO sin cruces; cambiar el extremo para cuadrar el paso también exige revisar los límites de la sonda.

## TopSpin no encuentra o no ejecuta el script

1. Confirme que el archivo previsto está en `<TopSpin>/exp/stan/nmr/py/user/` de la **instalación que realmente está abierta**, o impórtelo con `edpy → File → Import`.
2. Use el comando correspondiente: `xpy dosy_prepare_ramps.py`, `xpy dosy_workshop.py` o `xpy dosy_workshop_v3.py`.
3. `dosy_prepare_ramps.py` sale de un plan generado; los otros dos salen de sus respectivos directorios `dist/`. No ejecute una plantilla/módulo interno ni la macro expandida de referencia **NO_EJECUTAR**.
4. TopSpin utiliza Jython nativo; no intente resolver un error de `TopCmds` instalando un paquete Python ajeno. Python externo ejecuta el generador y las pruebas simuladas, no la interfaz del instrumento.
5. Permisos, enlaces de directorios inesperados o un layout antiguo requieren revisión del responsable. El motor admite el layout directo de cuatro campos de `CURDATA` y rechaza el campo de usuario de layouts anteriores en lugar de adivinar rutas. No retire esas comprobaciones.

## El plan está bloqueado como ejemplo o tiene tiempos incorrectos

`example_only=true` bloquea la ejecución en TopSpin deliberadamente. Verifique programa y mapeo y regenere un plan operativo expresamente. En un JSON editado, establezca `example_only=false` y `delay_mapping_confirmed=true` únicamente después de esa revisión. Los scripts ya generados no releen la configuración modificada.

Las dos configuraciones incluidas, también `config_tres_repeticiones.json`, son ejemplos bloqueados. Las repeticiones de tiempos heredados no introducen un nuevo mapeo D20; la plantilla y límites siguen necesitando revisión antes de habilitar expresamente una copia del plan.

- GUI/diálogos nativos de preparación: tiempos de difusión en **ms**.
- CLI `--delay-s` y D20 almacenado: **segundos**; 50 ms son 0.05 s, no 50 s.
- P30: **µs**; en `stebpgp1s1d` revisado, δ pequeña = **2 × P30**.
- Lista D20 vacía: repeticiones del tiempo heredado, no distintos Δ.
- Utilice punto decimal (`0.05`, `1.902`); en los diálogos nativos la coma separa elementos, no decimales.
- El índice GPZ del plan es configurable; el lector de calibración está **fijo en GPZ6**. No lo utilice con otro índice modificando solo el plan.

## Existe un destino o falla la preparación a mitad

Se rechazan EXPNO existentes y se comprueba que no haya FID/SER/datos procesados tras copiar parámetros. No se reanuda ni sobrescribe una adquisición anterior.

Inspeccione las rutas indicadas y `preparacion.json` o `execution.json` cuando existan. Conserve las carpetas parciales como evidencia. Resuelva errores de dataset, parámetros o comandos antes de elegir un rango nuevo completo. No ejecute preparaciones simultáneas, no sustituya `wraparam` por `wrpa`/`WR` ni borre datos originales para que un destino pase la comprobación.

## No se propone una constante de gradiente G

La serie integrada puede proporcionar una escala empírica `b100`. Convertirla a G físico requiere los hashes exactos de programa y forma guardados documentados en `python/sequence_model.json`, y sus condiciones de secuencia/núcleo/forma. Ese archivo es un modelo con factor de forma al cuadrado 0.81, no una calibración experimental ni Dref por defecto. Un archivo ausente o una secuencia distinta desactivan esa conversión deliberadamente.

No cambie nombres de programas ni sustituya formas para forzar una coincidencia. Conserve la escala empírica con su ámbito de tiempos/sonda u obtenga un modelo revisado aparte. Si dispone de D calculado independientemente con una G anterior conocida, utilice **Constante Bruker desde D medido** con esos valores reales, no una amplitud nominal de hardware.

## Se rechaza la integral o la calibración logarítmica

Revise EXPNO indicado, PROCNO, región ppm real del patrón, fase, línea base, integridad de archivos, parámetros de procesado guardados y señal/ruido. Esta ruta exige **integrales netas firmadas** positivas y finitas, al menos cuatro amplitudes cuadradas distintas y atenuación decreciente.

No aplique valor absoluto a integrales negativas/ruidosas, no imponga un suelo positivo arbitrario ni descarte puntos solo para maximizar R². Cambiar una ventana necesita justificación científica y revisión de la misma región en toda la rampa. Reprocese consistentemente en una copia de procesado documentada, conservando FID/SER y el procesado anterior.

RG, NS, tiempos de difusión, forma de gradiente y parámetros pertinentes de pulso/adquisición deben mantenerse consistentes. Los distintos Δ necesitan calibraciones separadas. Variaciones registradas de fase/línea base pueden generar advertencias aunque coincidan los parámetros estructurales; inspeccione esos espectros, no solo la recta. El lector corrige la escala almacenada `NC_proc`; normalizar manualmente cada espectro alteraría la evidencia.

## Falla la comprobación térmica o el ajuste parece demasiado bueno

Revise TE de todos los experimentos y la temperatura asociada a Dref. Estabilice la muestra y use Dref documentado para esas condiciones. No amplíe tolerancias solo para aprobar la calibración. TE no es una medida independiente de la temperatura real de la muestra.

Dref = 1.902 × 10⁻⁹ m²/s del ejemplo HDO/D2O citado corresponde a 298.15 K. No se aplica automáticamente a 293 K, a otro disolvente ni a un polímero. Aquí no se realiza corrección térmica silenciosa.

R² y el error estándar de pendiente describen la regresión, no pureza, ausencia de convección ni incertidumbre total. Revise estructura de residuos, solapamiento, cobertura de atenuación, ruido y aplicabilidad del patrón. Si los últimos puntos son mayormente ruido, diseñe una rampa revisada en lugar de ocultarlos. El primer punto al 8 % no es I(0); el intercepto es libre.

## v3 no empieza o se detiene tras ZG/EFP

Para adquirir hay que elegir **Preparar, adquirir y analizar** y después confirmar **Iniciar serie**. **Exportar plan** y **Preparar sin adquirir** nunca adquieren. Un rango ya preparado anteriormente no se reutiliza automáticamente: organice un procedimiento manual controlado por el responsable o elija destinos nuevos para otro autorun.

Durante una ejecución autorizada, v3 exige terminación confirmada (`CmdThread.getResult() == 0`) de ZG y EFP. `None`, un código distinto de cero, cambios RF/RG/tiempos/fase o espectros incompletos detienen el flujo. No modifique el código para considerar éxito la mera presencia de un FID. Lea `execution.json`, conserve los puntos adquiridos y revise la respuesta API de su versión TopSpin con el responsable antes de repetir. El script no diagnostica averías ni sintoniza/hace shimming de la sonda.

## Falla la nutación P1 o P90 es inverosímil

Use la plantilla 1D `zg` revisada y compruebe potencia RF, fase, D1, muestra, canal y ventana ppm. P1 actual puede ser un pulso de 180°, no P90. Defina límites P90 justificados y al menos nueve duraciones distintas que cubran señal positiva/negativa y primera inversión, respetando los límites RF.

No ejecute APK independiente en cada punto ni convierta las áreas a valores absolutos. Se rechaza un óptimo en el borde en lugar de presentarlo como calibración. Inhomogeneidad RF, relajación o desviación de resonancia pueden invalidar el seno ideal aunque el ajuste parezca atractivo. La propuesta no modifica P1 de otras muestras ni la calibración RF global.

## No coinciden G/cm, G/mm o las listas DOSY recalculadas

Compruebe la unidad y la constante anterior utilizada realmente para obtener D medido. `1 G/mm = 10 G/cm`; `1 G/cm = 0.01 T/m`. Se implementa `G_nueva = G_anterior * sqrt(D_medido / D_referencia)`, no su inversa.

Solo tras revisar la propuesta debe el responsable editar `gradpar` y guardar con `setpre → File → Write`. Si corresponde, `xau dosy restore` regenera `difflist` en una **copia de análisis** documentada. No aplique otro factor de referencia/temperatura silencioso ni reescriba la lista histórica sin registrar el valor anterior.

## Falla el lanzador externo de calibración de solo lectura

Consulte `python python/calibrate_series.py --help`. Requiere un dataset existente con espectros 1D procesados, EXPNO/límites ppm expresos, Dref, su temperatura, nombre del patrón, disolvente y fuente, además de `--confirm-sequence-mapping` tras revisar el mapeo. Emplea el mismo núcleo GPZ6 del asistente nativo; no alinea ni corrige deriva/temperatura automáticamente para forzar un resultado.

`--out` debe ser una carpeta nueva **fuera** del dataset experimental; no coloque informes entre los espectros de entrada. Si falta el archivo autocontenido, `python python/build_bundles.py` lo reconstruye desde fuentes públicas locales sin acceder al instrumento. Siguen siendo aplicables las comprobaciones de integración, metadatos, patrón y temperatura. No introduzca Dref ficticio ni retire comprobaciones para producir un informe.

## Reproducir un problema de software sin hardware

Desde la raíz, estos comandos ejecutan **pruebas simuladas**, no adquisiciones:

```console
python python/run_tests.py
```

El lanzador ejecuta los grupos simulados incluidos en `tests/ramp_generator/test_ramp_generator.py`, `tests/topspin_console/test_calibration.py`, `tests/topspin_console/test_console.py`, `tests/topspin_console/test_jython_bundle.py`, `tests/topspin_console_v3/test_autorun.py` y las comprobaciones del paquete público. Utiliza simulaciones, no `TopCmds` del proveedor. No establece compatibilidad operativa con el espectrómetro. Consulte los registros de verificación del paquete público para los resultados de su ejecución real de pruebas.

Para comunicar un problema, incluya herramienta/versión o commit, acción/comando exacto, versión TopSpin/Jython, mapeo de pulso/gradiente y unidades relevantes, error, comportamiento esperado y observado, configuración mínima sin datos sensibles y plan/registros de ejecución anonimizados. Puede aportar hashes, pero **no publique datos crudos de investigación, identidades de muestras, rutas privadas, credenciales ni manuales/código Bruker sujetos a licencia sin permiso**. Consulte primero con el responsable del instrumento los fallos relacionados con hardware.

[Volver a la guía paso a paso](bruker-paso-a-paso.md) · [Inicio del repositorio](../../README.md)
