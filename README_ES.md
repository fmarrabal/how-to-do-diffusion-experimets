# Cómo realizar experimentos de difusión por RMN

[English](README.md) · [Contenido completo del workshop](docs/es/presentation-content.md) · [Guía Bruker paso a paso](docs/es/bruker-paso-a-paso.md)

Repositorio docente bilingüe sobre preparación, adquisición, procesado e interpretación de experimentos de difusión por RMN. Contiene el workshop completo en español e inglés, incluidos apéndices, notas del ponente, vídeos y material numérico de apoyo, además de herramientas Python para Bruker TopSpin.

Autores del workshop: **Ignacio Fernández** ([ORCID](https://orcid.org/0000-0001-8355-580X)) y **Francisco Manuel Arrabal-Campos** ([ORCID](https://orcid.org/0000-0002-5510-6297)), Universidad de Almería. La exposición principal dura 20 minutos y dispone de apéndices técnicos adicionales. El nombre del repositorio conserva la grafía solicitada por su mantenedor: `how-to-do-diffusion-experimets`.

## Presentaciones y contenido completo

| Material | Español | English |
|---|---|---|
| PowerPoint, 45 diapositivas con 20 apéndices ocultos | [Descargar PPTX](presentations/es/workshop-es.pptx) | [Download PPTX](presentations/en/workshop-en.pptx) |
| PDF estático, las 45 páginas | [Leer PDF](presentations/es/workshop-es.pdf) | [Read PDF](presentations/en/workshop-en.pdf) |
| Texto completo, tablas/valores de gráficos, imágenes y notas | [Leer en GitHub](docs/es/presentation-content.md) | [Read on GitHub](docs/en/presentation-content.md) |
| Notas completas del ponente | [Notas](materials/presenter/NOTAS_PONENTE_ES.txt) | [Speaker notes](materials/presenter/SPEAKER_NOTES_EN.txt) |
| Guion hablado de las 25 diapositivas principales | [Guion de 20 minutos](materials/presenter/GUION_HABLADO_20MIN_ES.txt) | [20-minute script](materials/presenter/SPOKEN_SCRIPT_20MIN_EN.txt) |

Los PPTX conservan gráficos/tablas editables, siete vídeos incrustados por idioma y el aspecto original de las diapositivas. Para reproducirlos use PowerPoint de escritorio: F5 inicia la presentación y Mayús+F5 empieza en la diapositiva actual. El PDF es estático. Las [copias MP4](presentations/media/) sirven como respaldo. Los [tiempos](materials/presenter/TIEMPOS_ES_EN.txt) corresponden a las 25 diapositivas principales; los apéndices no cuentan en los 20 minutos.

El recorrido incluye preparación de muestra y equipo, calibración de pulsos y gradiente, codificación de difusión según la secuencia, rampas, estabilidad térmica, procesado espectral coherente, atenuación y residuos, ambigüedad de la inversión de Laplace, regularización y ajustes conjuntos, interpretación DOSY, referencias, masas moleculares aparentes, SPEN-DOSY y difusión/relajación ultrafast. Los casos prácticos distinguen coherencia numérica y validación experimental independiente.

## Herramientas Python para Bruker

| Herramienta | Entorno | Función |
|---|---|---|
| [Generador de rampas](python/ramp_generator/) | Python 3 externo, CLI o GUI Tk | Planifica rampas 1D configurables, previsualiza EXPNO/GPZ/tiempos y exporta CSV/JSON y un programa TopSpin con comprobaciones |
| [Asistente TopSpin v2](python/topspin_console/) | Jython 2.7 integrado en TopSpin | Prepara copias de parámetros, integra series 1D procesadas existentes y propone escala empírica b y actualización revisable de la constante de gradiente |
| [Asistente TopSpin v3](python/topspin_console_v3/) | Jython 2.7 integrado en TopSpin | Añade nutación P1 y barrido de gradiente del patrón, con modos explícitos de preparar solamente o preparar/adquirir/procesar/analizar y registros de ejecución |
| [Calibración de series sin TopSpin](python/calibrate_series.py) | Python 3 externo | Lee datos Bruker procesados sin modificarlos y usa el mismo núcleo de calibración para exportar informes JSON/CSV/HTML |
| [Constructor de bundles](python/build_bundles.py) | Python 3 externo | Reconstruye los archivos autocontenidos TopSpin desde las fuentes incluidas y registra sus hashes |
| [Pruebas sin hardware](python/run_tests.py) | Python 3 externo | Ejecuta las comprobaciones sintéticas y con TopCmds simulado, sin instrumento |

Bruker distingue Jython integrado de su API moderna externa de Python 3. Estos asistentes utilizan la interfaz histórica **Jython/TopCmds**. No necesitan la API de red moderna ni distribuyen bibliotecas de Bruker. Véase la [documentación oficial de la interfaz](https://www.bruker.com/en/products-and-solutions/mr/nmr-software/topspin/topspin-python-interface.html).

### Empezar sin instrumento

1. Clone el repositorio o use **Code → Download ZIP** en GitHub y descomprímalo.

   ```console
   git clone https://github.com/fmarrabal/how-to-do-diffusion-experimets.git
   cd how-to-do-diffusion-experimets
   ```

2. Use Python 3 para las herramientas externas. El núcleo y las pruebas emplean la biblioteca estándar. La GUI requiere además Tkinter, que puede ser un paquete independiente del sistema operativo. Para ejecutar únicamente los asistentes Jython autocontenidos dentro de un TopSpin compatible no necesita instalar Python externo.

3. Ejecute las pruebas y consulte la ayuda:

   ```console
   python python/run_tests.py
   python python/ramp_generator/generate_ramps.py --help
   python python/ramp_generator/generate_ramps.py --gui
   python python/calibrate_series.py --help
   ```

4. Genere un ejemplo docente bloqueado en una carpeta **nueva**:

   ```console
   python python/ramp_generator/generate_ramps.py --config python/ramp_generator/config_ejemplo_tres_Delta.json --out mi-primer-plan-docente
   ```

5. Revise `plan.csv`, `plan.json` y `config.json`. El ejemplo tiene tres rampas de 23 puntos con distintos tiempos de difusión. Son valores editables, no parámetros prescritos para su muestra o sonda. Las dos configuraciones incluidas bloquean la ejecución hasta que se revisen deliberadamente y se regenere el plan.

### Usar dentro de TopSpin

Después de leer la [guía completa paso a paso](docs/es/bruker-paso-a-paso.md), copie `python/topspin_console/dist/dosy_workshop.py` y, si lo necesita, `python/topspin_console_v3/dist/dosy_workshop_v3.py` a:

```text
<TopSpin>/exp/stan/nmr/py/user/
```

Abra el dataset correcto y ejecute uno de estos comandos **en la consola de TopSpin**:

```text
xpy dosy_workshop.py
xpy dosy_workshop_v3.py
```

Los diálogos nativos actuales están en español; la guía inglesa explica cada operación. **v2 no adquiere datos. v3 puede lanzar comandos reales ZG/EFP únicamente cuando el operador selecciona y confirma expresamente el modo de adquisición.** Revise plantilla, destinos, RF, tiempos y gradientes antes de usar ese modo. Ejecutar el bundle Jython con CPython ordinario no lo conecta a TopSpin.

## Límites científicos y operativos

- Compruebe programa de pulsos, sonda, núcleo, disolvente, temperatura, forma de gradiente y tiempos reales. En el ejemplo documentado `stebpgp1s1d`, D20 está en segundos, P30 en microsegundos, δ = 2 × P30 y GPZ6 es el gradiente variable. Estas correspondencias no son universales.
- Conserve los experimentos originales. La preparación exige destinos nuevos y copia parámetros, no FID/SER. La calibración externa escribe informes fuera del dataset de entrada. Los destinos existentes o parciales no se borran ni reutilizan silenciosamente.
- GPZ es un porcentaje, no un gradiente calibrado. Crear una rampa no calibra por sí mismo el equipo. D de referencia debe corresponder al patrón, disolvente y temperatura indicados; el programa no aplica la calibración histórica del autor a su equipo.
- Convergencia, R² alto o una gaussiana estrecha no confirman una especie ni descartan convección. El área de un componente es fracción de señal RMN salvo que se establezca un modelo adecuado de respuesta cuantitativa.
- Las masas moleculares son valores aparentes dependientes de calibración. Una calibración de polímeros lineales no valida masas absolutas de arquitecturas ramificadas.
- La figura ultrafast D–T₂ procede de una reconstrucción experimental histórica de **cuatro transitorios**, 32 ecos y **27,768 segundos para toda la adquisición**. No es single-scan ni valida cuantitativamente el prototipo actual. Su máximo de D alcanza un borde de la rejilla; se conserva esa limitación.
- Las pruebas de software y Jython con stubs no validan el espectrómetro. La ejecución real en TopSpin 3.6.4 y la adquisición siguen sin comprobarse. Antes de adquirir, acuerde un ensayo controlado con el responsable del equipo.

## Material de apoyo, fuentes y procedencia

- [Referencias bilingües](materials/presenter/REFERENCIAS_ES_EN.txt) y [guía de referencias](references/README.md).
- [72 registros solapados de métodos/algoritmos](materials/catalogo/ILT_Algorithm_Catalog_ES_EN.csv), con catálogos [español](materials/catalogo/ILT_Algorithm_Catalog_ES.txt) e [inglés](materials/catalogo/ILT_Algorithm_Catalog_EN.txt). No son 72 algoritmos DOSY independientes.
- [Historia bilingüe](materials/story.json), [datos derivados de casos](materials/casos/), [simulaciones](materials/simulaciones/) y [procedencia de la figura ultrafast](materials/ultrafast/ultrafast_image_provenance.json).
- [Procedencia de la edición pública](provenance/README.md), [hashes de las presentaciones](provenance/presentation-manifest.json) e [instrucciones de verificación](docs/es/verificacion.md).
- [Solución de problemas](docs/es/solucion-de-problemas.md), [colaboración](CONTRIBUTING.md) y [derechos/atribución](RIGHTS.md).

La edición pública elimina rutas textuales privadas y el serial de la sonda en los metadatos. Las capturas conservan sus etiquetas científicas originales, incluidas referencias genéricas a carpetas/muestras. No se incluyen datos experimentales originales, artículos editoriales completos, binarios de aplicaciones, credenciales ni QA privada. No se han modificado los originales del workshop. Se mantienen autoría y atribución de terceros; la visibilidad pública no concede una licencia general sobre todas las obras citadas.
