# DOSY en Bruker: preparación y calibración paso a paso

[Inicio del repositorio](../../README.md) · [Solución de problemas](solucion-de-problemas.md) · [Referencias](../../references/README.md) · [English](../en/bruker-step-by-step.md)

Esta guía acompaña a la edición pública y portable de los scripts del workshop. Deriva de la implementación original; el empaquetado público puede retirar rutas privadas de procedencia. Consulte los registros de procedencia y verificación del paquete público, sin suponer que sus archivos autocontenidos son idénticos byte a byte a una copia privada anterior.

## 1. Elegir la ruta correcta

| Herramienta | Dónde funciona | Qué permite | ¿Inicia adquisición? |
|---|---|---|---|
| `python/ramp_generator/` | Python externo, versión 3.8 o posterior | Generar planes por GUI/CLI y un script de preparación para TopSpin | No |
| `python/topspin_console/dist/dosy_workshop.py` | Jython integrado en TopSpin | Preparar rampas 1D; analizar una serie del patrón ya adquirida; proponer una constante de gradiente | No |
| `python/topspin_console_v3/dist/dosy_workshop_v3.py` | Jython integrado en TopSpin | El asistente anterior más recorridos de nutación P1 y adquisición del patrón | Solo tras elegir adquirir y confirmarlo expresamente |

Los diálogos incluidos utilizan actualmente textos en español. Estas herramientas no sustituyen el procedimiento de operación del equipo ni la formación proporcionada por su responsable.

La compatibilidad se apoya en fuentes Bruker revisadas y pruebas con APIs simuladas, también en el entorno Jython 2.7.2 de TopSpin 3.8.0. **No se ha validado una adquisición real ni el funcionamiento en TopSpin 3.6.4.** Un resultado correcto de pruebas locales no constituye una cualificación del instrumento.

## 2. Revisar el experimento antes de crear copias

Abra una **plantilla 1D** válida del dataset previsto. Revise con el responsable del instrumento:

- Identidad de la muestra, disolvente, núcleo, sonda, sintonía/adaptación, lock, shimming y estabilidad térmica.
- Programa de pulsos, potencia RF, duraciones, límites de forma/amplitud de gradiente, retardo de relajación D1, NS, DS y ganancia de receptor RG.
- Parámetros de adquisición y procesado, fase, línea base y región espectral del patrón.
- EXPNO/PROCNO de plantilla, dataset destino y rangos de EXPNO **libres**.

No traslade la ventana ppm del patrón ni índices de otra muestra sin revisar este espectro. No ejecute dos preparaciones sobre los mismos números de destino.

El mapeo siguiente corresponde al ejemplo revisado `stebpgp1s1d`; no es una convención universal de RMN:

| Parámetro | Significado en este ejemplo | Unidad |
|---|---|---|
| D20 | Tiempo de difusión grande Δ | segundos |
| P30 | Duración de cada lóbulo bipolar; δ pequeña = 2 × P30 | microsegundos |
| GPZ6 | Amplitud variable del gradiente de difusión | porcentaje del máximo calibrado |
| GPZ7 | Spoiler, no el gradiente de difusión que se barre | porcentaje |
| GPNAM6 | Forma del gradiente de difusión | identificador de forma |
| TE | Temperatura registrada por el equipo; no termometría independiente de la muestra | kelvin |

Compruebe su programa real antes de confirmar un mapeo D/P. Los porcentajes GPZ no son gradientes físicos ni valores b. El extremo del 96 % es un ejemplo editable del workshop, **no** un límite universal seguro o recomendado.

## 3. Generar el plan fuera de TopSpin: GUI o CLI

Ejecute estos comandos desde la raíz del repositorio. El generador externo utiliza la biblioteca estándar de Python; solo la GUI necesita Tkinter.

### Interfaz gráfica

```console
python python/ramp_generator/generate_ramps.py --gui
```

En Windows también puede abrir `python/ramp_generator/abrir_generador.pyw` con Python.

1. Indique EXPNO/PROCNO de plantilla, número de rampas, primer destino, salto y rango/paso GPZ.
2. Elija los tiempos para su experimento. La GUI admite milisegundos y los convierte a segundos.
3. Use **Previsualizar** para inspeccionar todos los puntos sin escribir un paquete.
4. La configuración inicial de tres Δ está marcada **Es un ejemplo**. Manténgala así mientras explora. Desmarque solo tras revisar valores y programa; confirme expresamente el mapeo.
5. Use **Generar** y elija una carpeta de salida que todavía no exista.

La GUI conserva P30 de la plantilla. Una lista de tiempos vacía genera repeticiones con D20 heredado; no son tiempos de difusión distintos.

### Comandos: generar primero un ejemplo bloqueado

```console
python python/ramp_generator/generate_ramps.py --config python/ramp_generator/config_ejemplo_tres_Delta.json --out mi_ejemplo
```

Con `example_only=true` el ejemplo no puede ejecutarse en TopSpin. De 8 a 96 % en pasos de 4 % hay 23 puntos por rampa: 100–122, 200–222 y 300–322, 69 puntos en total. Los tiempos de ejemplo son 0.05, 0.10 y 0.15 s; no están prescritos para su muestra.

Después de revisar el programa y elegir tiempos y límites apropiados, este comando muestra la **sintaxis** de un plan operativo; sustituya los valores de ejemplo antes de usarlo:

```console
python python/ramp_generator/generate_ramps.py --out mis_rampas_revisadas --ramps 3 --template-expno 10 --start-expno 100 --stride 100 --gradient-index 6 --gradient-start 8 --gradient-stop 96 --gradient-step 4 --delay-parameter D20 --delay-s 0.05 0.10 0.15 --pulse-program stebpgp1s1d --confirm-delay-mapping --ds 16
```

`--delay-s` utiliza **segundos**, no milisegundos. Utilice punto decimal en los campos numéricos (`0.05`, `1.902`); en los diálogos nativos la coma separa elementos de las listas. Para tres repeticiones sin modificar D20/P30 heredados:

```console
python python/ramp_generator/generate_ramps.py --config python/ramp_generator/config_tres_repeticiones.json --out mis_repeticiones
```

**Los dos JSON incluidos son ejemplos bloqueados**, también el de repeticiones. Revise una copia de la configuración y establezca `example_only=false` solo cuando vaya a generar un plan operativo; regenere en una carpeta nueva. Repetir tiempos heredados sigue exigiendo revisar plantilla y límites instrumentales.

La CLI puede fijar un parámetro de pulso con `--pulse-parameter P30 --pulse-us VALOR --confirm-pulse-mapping`; introduzca su `VALOR` numérico revisado y el programa esperado. No equipare P30 con δ sin inspeccionar la secuencia. La GUI no ofrece esa modificación de P30.

Cada paquete nuevo contiene `plan.csv`, `plan.json`, `config.json`, `dosy_prepare_ramps.py`, una macro que llama al script y unas instrucciones breves. La macro expandida de referencia está marcada **NO_EJECUTAR** y no incorpora las comprobaciones del programa Python. Editar un JSON no modifica el script ya generado: regenere en una carpeta nueva e instale ese nuevo script.

## 4. Llevar la preparación generada a TopSpin

1. Conserve una copia inalterada del plan y la configuración.
2. Copie el `dosy_prepare_ramps.py` generado a:

   ```text
   <TopSpin>/exp/stan/nmr/py/user/
   ```

   También puede usar `edpy → File → Import`.
3. Abra el dataset correcto y revise de nuevo la plantilla. El campo opcional `expected_dataset_name` restringe el dataset previsto.
4. Ejecute en la consola de TopSpin:

   ```text
   xpy dosy_prepare_ramps.py
   ```

5. Compare los primeros y últimos puntos, tiempos, DS y RG con `plan.csv` antes de adquirir.

El script comprueba todos los destinos antes de copiar y vuelve a comprobar cada uno antes de usarlo. Utiliza `wraparam` para copiar **parámetros**, no `wrpa` ni `WR` para copiar datos adquiridos. Verifica que los nuevos destinos no contengan FID/SER ni señales procesadas, comprueba las escrituras y restaura la vista del dataset original. No ejecuta `zg`, `multizg` ni `rga`.

Si falla a mitad de preparación, conserva las carpetas parciales. No las borre ni reutilice sin revisión: documente el fallo, inspeccione la causa y elija nuevos destinos libres para otro intento.

## 5. Instalar y abrir el asistente nativo

Copie `python/topspin_console/dist/dosy_workshop.py` al mismo directorio TopSpin `py/user`, o impórtelo con `edpy`. Es autocontenido; dentro de TopSpin no hace falta instalar Python externo.

En Windows, el instalador opcional realiza esa copia y verifica su SHA-256. Ejecútelo desde la raíz, sustituyendo el marcador por el directorio real de instalación:

```powershell
& .\python\topspin_console\install_topspin_console.ps1 -TopSpinHome '<SU_INSTALACION_TOPSPIN>'
```

No abre TopSpin. Si el script existente es idéntico, lo conserva; si es distinto, guarda una copia antes de sustituirlo. Si lo impiden permisos o comprobaciones de ruta, pida al responsable que utilice el procedimiento de importación manual autorizado.

Abra una plantilla en TopSpin y escriba:

```text
xpy dosy_workshop.py
```

Seleccione **Preparar rampas** para crear el plan directamente en los diálogos nativos. Revise índice/rango GPZ, destinos libres, DS, programa esperado y tiempos. Este formulario admite tiempos en **milisegundos**. Deje la lista de tiempos vacía para repetir los heredados. Inspeccione el plan completo y elija **Exportar plan solamente** o **Crear experimentos**. Ninguna opción inicia adquisición.

El lector de calibración de este asistente está mapeado específicamente a **GPZ6**, D20, P30, D16 y GPNAM6. Cambiar el índice GPZ de la generación de rampas no cambia ese lector. Otra secuencia exige revisar su mapeo e implementación por separado.

## 6. Calibrar mediante las integrales de la serie del patrón

Adquiera el patrón mediante un procedimiento autorizado y procese todos los espectros de forma consistente. El asistente básico lee esos archivos ya existentes sin modificarlos.

1. Revise identidad, disolvente, concentración/condiciones y aplicabilidad del D de referencia. Seleccione la región ppm real y aislada del patrón en esta muestra.
2. Abra un experimento del dataset y seleccione **Calibrar con serie 1D**.
3. Introduzca EXPNO como `100-122` o lista, PROCNO y límites ppm. Incluya una sola rampa de tiempos constantes.
4. Introduzca identidad, disolvente y fuente del patrón; Dref en **10⁻⁹ m²/s** a la temperatura de referencia indicada expresamente en K. Revise las tolerancias TE configurables.
5. Inspeccione todos los espectros, las integrales firmadas, la recta, los residuos, metadatos y advertencias antes de aceptar una calibración candidata.

El lector recupera la escala de intensidad almacenada: los enteros de 32 bits utilizan `2**NC_proc`; los datos float64 se leen directamente. Integra por trapecios con signo e interpolación de extremos, no valores absolutos. Esta ruta logarítmica requiere integrales netas positivas y finitas y al menos cuatro amplitudes cuadradas distintas; no descarta puntos inválidos silenciosamente para mejorar R².

El modelo ajustado es:

```text
x = (GPZ6 / 100)^2
ln(I / Imax) = intercepto - s*x, con s > 0
b100 = s / (Dref * 10^-9)       [s/m^2]
b(g) = b100 * (GPZ6 / 100)^2
```

El intercepto queda libre. El primer punto al 8 % **no** es una medida a gradiente cero. Imax es una escala de normalización; I(0) se extrapola. Un buen R² no demuestra pureza del patrón, relación señal/ruido suficiente ni ausencia de convección.

La salida contiene `calibracion.json`, `atenuacion_residuos.csv` e `informe.html`, con hashes y ámbito de aplicación. `b100` es una escala experimental para la misma sonda, secuencia, forma y tiempos. **Cada Δ necesita su propia escala**, salvo transferencia respaldada por un modelo de secuencia revisado de manera independiente. No mezcle 50/100/150 ms como una sola calibración de tiempos constantes.

TE es un metadato instrumental, no temperatura independiente de la muestra. El programa comprueba las tolerancias configuradas expresamente; no infiere ni aplica corrección térmica silenciosa. El valor literal HDO/D2O D = 1.902 × 10⁻⁹ m²/s corresponde a 298.15 K, no a cualquier temperatura o disolvente. **El paquete público no incluye un perfil experimental de calibración de sonda TBO ni D de referencia por defecto.** Solo incluye el modelo de secuencia documentado de la sección 7; debe aportar una referencia apropiada y su temperatura.

### Alternativa: analizar espectros existentes con Python externo

El lanzador externo de solo lectura utiliza el **mismo núcleo de calibración** del asistente TopSpin; no es un algoritmo científico nuevo. Requiere Python 3.8 o posterior y su biblioteca estándar, no TopSpin ni su API instrumental. Consulte primero sus opciones reales:

```console
python python/calibrate_series.py --help
```

Este es un modelo de comando, **no una calibración lista para ejecutar**. Sustituya todos los marcadores en mayúsculas por dataset revisado, límites ppm reales, Dref numérico positivo a la temperatura indicada e identidad/fuente documentadas. La carpeta de salida debe ser nueva y **estar fuera** del directorio experimental de entrada:

```console
python python/calibrate_series.py --dataset "DIRECTORIO_DATASET" --expnos "100-122" --procno 1 --ppm-low PPM_INFERIOR --ppm-high PPM_SUPERIOR --dref DREF --reference-temperature-k TREF --reference-name "NOMBRE_PATRON" --solvent "DISOLVENTE" --reference-source "DOI_O_FUENTE_DOCUMENTADA" --confirm-sequence-mapping --out "CARPETA_INFORME_NUEVA_FUERA_DATASET"
```

Utilice `--confirm-sequence-mapping` solo después de verificar GPZ6, D20, P30, D16 y GPNAM6 en el programa guardado. La temperatura es obligatoria junto a Dref; no se adivina un valor. `--max-temperature-span-k` y `--max-reference-temperature-difference-k` controlan las mismas comprobaciones nativas (ambas por defecto 0.5 K); no las relaje solo para obtener un ajuste.

El lanzador escribe `calibracion.json`, `atenuacion_residuos.csv` e `informe.html` en la carpeta nueva. No importa `TopCmds` del proveedor ni conecta al instrumento, adquiere, alinea automáticamente, infiere correcciones de deriva, sobrescribe espectros o aplica propuestas. Revise la salida con las mismas comprobaciones de espectros, patrón y residuos descritas antes.

## 7. Proponer y revisar la constante física de gradiente G

Hay dos rutas distintas; no mezcle sus entradas.

### A. Propuesta condicional desde la serie integrada

Solo se propone G físico cuando los bytes guardados de `pulseprogram` y `gpnam6` coinciden con las identidades de [`python/sequence_model.json`](../../python/sequence_model.json) y se cumplen las condiciones requeridas `stebpgp1s1d` / `SMSQ10.100` / ¹H. Este archivo público contiene identidad del modelo, hashes, expresión y factor de forma al cuadrado 0.81, **no una calibración experimental de sonda**. **Ver modelo de secuencia** abre ese modelo, no un perfil privado de calibración.

Solo para ese modelo documentado exacto:

```text
delta = 2 * P30 * 10^-6                 [s, P30 introducido en microsegundos]
t_efectivo = D20 - 0.32525*delta - D16/2
b100 = (gamma * Gmax * delta)^2 * 0.81 * t_efectivo
gamma = 267.52218744 * 10^6             [rad/s/T, 1H]
Gmax = sqrt(b100 / ((gamma*delta)^2 * 0.81 * t_efectivo))   [T/m]
```

El tiempo efectivo debe ser positivo. Es el modelo específico conservado, no una ecuación Stejskal–Tanner universal ni un algoritmo nuevo validado. Para bytes, secuencias o formas diferentes se conserva la escala empírica b **sin inventar G**. La coincidencia de fuentes es necesaria para esta ruta, no una validación del instrumento ni del modelo.

### B. Propuesta desde un D calculado con G anterior conocida

Seleccione **Constante Bruker desde D medido**. Introduzca G anterior realmente utilizada para calcular D, su unidad, D medido, D de referencia a la temperatura aplicable e identidad/disolvente/fuente del patrón:

```text
G_nueva = G_anterior * sqrt(D_medido / D_referencia)
```

Ambos D deben corresponder a las mismas condiciones y a un modelo coherente de secuencia/forma. No sustituya la constante utilizada por el máximo nominal del hardware.

| Unidad de gradiente | Conversión |
|---|---|
| 1 G/cm | 0.01 T/m |
| 1 G/mm | 0.1 T/m = 10 G/cm |

La ruta B guarda `constante_propuesta.json`; la A registra la propuesta en `calibracion.json`. Ninguna escribe automáticamente la calibración global. Tras revisarla con el responsable, use **`gradpar`** (o `setpre → Edit → Gradient parameters`) y guarde la configuración de sonda mediante **`setpre → File → Write`**. La incertidumbre mostrada cubre solo la regresión, no la del patrón, temperatura ni modelo de secuencia.

Si una lista DOSY existente se generó con otra G, `xau dosy restore` permite regenerar `difflist`. Hágalo en una **copia de análisis** documentada, conservando los datos y la lista originales.

## 8. Opcional v3: separar preparación y adquisición

Instale `python/topspin_console_v3/dist/dosy_workshop_v3.py` mediante la misma copia/importación y abra:

```text
xpy dosy_workshop_v3.py
```

El asistente anterior sigue accesible por **Asistente anterior: rampas y analisis**. v3 ofrece **Calibrar P1: barrido de nutacion** y **Calibrar DOSY: adquirir rampa del patron**.

Empiece con **Exportar plan** o **Preparar sin adquirir**. Antes de elegir **Preparar, adquirir y analizar**, obtenga la conformidad del responsable sobre muestra, sonda, límites RF, barrido, relajación, RG, fase, temperatura y destinos libres. Otro diálogo exige **Iniciar serie**; de lo contrario se vuelve sin adquirir.

Para cada punto autorizado, v3 vuelve a comprobar los parámetros conservados, espera a `ZG`, espera a `EFP` y lee el espectro procesado. Exige `CmdThread.getResult()` igual a 0 para ambos comandos. Un estado ausente/ambiguo, parámetros cambiados o datos incompletos detienen la serie; que exista un FID no demuestra una terminación correcta. `execution.json` registra los pasos y conserva los parciales. El script no reanuda una ejecución anterior: otro intento necesita EXPNO nuevos. Tampoco reutiliza silenciosamente un rango ya preparado mediante autorun.

La nutación P1 requiere una plantilla 1D `zg` revisada, potencia RF y fase fijas, al menos nueve duraciones distintas, áreas firmadas positivas y negativas y un barrido que cubra subida y primera inversión. No ejecute APK independientemente en cada punto. Se ajusta `I(P1) = A*sin(pi*P1/(2*P90)) + offset` dentro de límites expresos; se rechaza un óptimo en el borde. No se presupone que P1 actual sea P90. P90/P180 propuestos solo corresponden a potencia, muestra, canal y condiciones registradas; v3 no sintoniza, hace shimming, elige potencia RF ni mide T1 automáticamente.

El autorun DOSY barre GPZ6 con tiempos fijos y utiliza la calibración integral anterior. v3 no escribe una calibración global de gradiente, no aplica P1 a otras muestras ni modifica el modelo de secuencia documentado. Revise sus salidas antes de adoptar manualmente una propuesta.

## 9. Conservar evidencia y distinguir la alternativa Bruker

Conserve espectros originales, plantilla, plan/configuración, decisiones de procesado, fuente y temperatura del patrón, hashes, residuos, informes, decisión del responsable y cualquier fallo de comandos de su versión. Documente adquisición, calibración y análisis posterior como pasos separados.

El AU estándar Bruker `xau dosy 8 96 23 l n` prepara una lista de gradientes para un dataset **pseudo-2D** apropiado. No equivale a los 69 EXPNO 1D del generador, no adquiere por sí solo ni mide una referencia de difusión. Consulte el programa correcto y la documentación Bruker antes de elegir esa alternativa.

Fuentes primarias: el [índice de referencias del repositorio](../../references/README.md) enlaza la bibliografía completa. [Bruker TopSpin Python Interface](https://www.bruker.com/en/products-and-solutions/mr/nmr-software/topspin/topspin-python-interface.html) distingue Jython integrado de la API externa Python posterior. El [tutorial DOSY de Bruker](https://2210pc.chem.uic.edu/nmr/downloads/dosy_ts13.pdf), especialmente su apartado de calibración, respalda la distinción entre medir una calibración y preparar la lista. Los manuales Bruker instalados de Python, adquisición/procesado, difusión y formato de datos, y el programa de pulsos real, son la referencia para su versión; no se redistribuyen aquí.

[Continuar con solución de problemas](solucion-de-problemas.md) · [Inicio del repositorio](../../README.md)
