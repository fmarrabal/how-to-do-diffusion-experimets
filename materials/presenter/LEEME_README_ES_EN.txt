DOSY: de la dificultad a un resultado revisable / From difficulty to a reviewable result
Workshop bilingüe · v8 · 20 minutos / Bilingual workshop · v8 · 20 minutes

ESPAÑOL

Recorrido
La historia empieza con las dificultades para calibrar y preparar el espectrómetro.
Después muestra cómo el procesado y la inversión pueden cambiar la interpretación.
Sólo entonces presenta cuatro herramientas propias y sus ejemplos prácticos:
asistente TopSpin, DiffAtOnce Prime, ResinAtOnce y marco reproducible DALTAIL.
Cierra con SPEN/ultrafast y el desarrollo propio pendiente de validación cuantitativa.

Presentar
Hay 25 diapositivas principales y 20 apéndices ocultos: 16 del catálogo, dos de
ecuaciones y dos de inversión. Los apéndices no cuentan en los 20 minutos.
Abra el PPTX en PowerPoint de escritorio. F5 inicia; Mayús+F5 ensaya desde la
diapositiva actual. Avance manualmente. Use la vista del moderador para las notas.
Los siete vídeos incrustados están en las diapositivas 7, 8, 11, 12, 13, 14 y 23;
duran 18, 18, 18, 16, 16, 14 y 18 segundos. Se narran dentro del tiempo asignado.
Las copias MP4 sirven de respaldo. Los PDF son estáticos e incluyen las 45 páginas.

Calibración: distinguir ejemplos
P1: el ejemplo real del usuario conserva P180 = 22 µs y P90 = 11 µs. Un nulo
aislado no distingue 180° de 360°; seguir el primer cruce tras el máximo de 90°.
Los espectros superpuestos tienen RG/NS/secuencia distintos: amplitudes cualitativas.
El perfil experimental TBO protegido conserva la pendiente histórica por altura
1,58627, Δ = 50 ms, δ = 1,20 ms y SMSQ10.100. No se sustituye por G nominal.

El nuevo caso por integral es un replay OFFLINE del núcleo sin cambios del asistente,
sobre 23 espectros HDO reales y una ventana fija 4,5–4,9 ppm inspeccionada alrededor
de 4,70536 ppm. Pendiente integral 1,557031; R² = 0,9997745. La regla predeterminada
rechaza la serie: deriva TE = 0,77 K > 0,5 K. También avisa fase y DS variables.
El candidato mostrado se obtuvo sólo con tolerancia explícita 0,8 K, para enseñanza;
no constituye aceptación. Estabilizar/repetir y revisar fase/DS antes de calibrar.
Los 115 hashes de entrada se comprobaron después del cálculo. El perfil protegido
permanece intacto. Dref(T media) = 1,688079 × 10⁻⁹ m²/s es una aproximación térmica;
no es la referencia efectiva 1,673921 del perfil histórico ponderado por gradiente.
El asistente v2 usado en los casos no inicia adquisición ni modifica la constante instrumental.
Ejecutar en consola: xpy dosy_workshop.py. TopSpin 3.6.4 real queda por verificar.

Casos de software y alcance
El flujo DOSY demostrado de Prime recibe una serie Bruker procesada pdata/N/1r;
no promete importación universal de FID/ser/2rr. Aplicaciones y algoritmos son
distintos: TRAIn/MF/RAI-S/DOME-S/SILT son motores, no cinco productos adicionales.
En TP194 la concordancia local/mapa usa la misma extracción, rejilla y protocolo:
es consistencia interna en datos experimentales, no validación independiente de D,
identidad química o número de especies. La captura de 256 bins y la tabla de
2048 bins tienen configuraciones distintas; no intercambiar sus cifras.
La proyección TP194 conserva cerca del 6 % de señal sin asignar. Dos bandas
respaldadas no demuestran dos especies; el error descriptivo no es el residuo ILT.

KK2 se presenta como análisis ARCHIVADO de 230 espectros y 10 rampas. La auditoría
actual encuentra 213 archivos procesados distintos del manifiesto (207 procs y seis
1r), mientras los archivos de adquisición comprobados coinciden. No se afirma que
todo el procesado actual reproduzca ese snapshot. TTMS y temperatura se aplican
una sola vez al eje completo; no se reescala KK2 a tablas previas. Las masas son
aparentes bajo la calibración molecular: no masas absolutas de polímeros ramificados.

Fuentes y reproducción
Las notas TXT se extraen de los PPTX finales. Fuentes/ contiene el guion, catálogo,
datos derivados de casos, modelos y scripts de simulación, con un manifiesto SHA-256.
GUION_HABLADO_20MIN_ES.txt conserva únicamente el relato de las 25 diapositivas
principales. NOTAS_PONENTE_ES.txt conserva las notas técnicas de las 45 diapositivas.
El catálogo reúne 72 registros solapados: no 72 algoritmos DOSY independientes.
Las simulaciones están identificadas; no son experimentos ni límites del equipo.
Los scripts científicos requieren sus dependencias y, cuando se indica, las rutas
locales de entrada documentadas. No ejecutarlos sobre originales sin revisar destino.
Los artículos completos, datos experimentales originales y QA privada no se incluyen.
El ultrafast propio necesita gradiente z; su validación experimental sigue pendiente.

ENGLISH

Story and presenting
The story first shows why spectrometer calibration and preparation are difficult,
then why processing and inversion can alter the interpretation. It introduces four
own tools afterwards: TopSpin helper, DiffAtOnce Prime, ResinAtOnce and the reproducible
DALTAIL framework, followed by practical cases and SPEN/ultrafast development.
There are 25 main slides and 20 hidden appendices: 16 catalogue, two equations and
two inversion slides. Hidden appendices are outside the 20-minute talk.
In desktop PowerPoint use F5, or Shift+F5 from the current slide. Advance manually.
Seven embedded videos appear on slides 7, 8, 11, 12, 13, 14 and 23, lasting
18, 18, 18, 16, 16, 14 and 18 seconds. They are included in the speaking time.
Separate MP4 copies are backups. Static PDF previews contain all 45 slides.

Calibration and cases
The P1 example uses actual saved P180 = 22 µs and P90 = 11 µs. One isolated null
does not distinguish 180° from 360°; follow the first crossing after the 90° maximum.
The overlay is qualitative because receiver gain, scans and sequence differ.
Preserve the protected TBO height-based calibration: slope 1.58627, Δ = 50 ms,
δ = 1.20 ms, SMSQ10.100. Do not replace it with a nominal gradient constant.

The new integral case runs the unchanged helper core OFFLINE on 23 real HDO spectra.
A fixed 4.5–4.9 ppm window was inspected around the actual 4.70536 ppm line.
Integral slope = 1.557031; R² = 0.9997745. The default rule rejects this series:
recorded temperature drifts by 0.77 K, exceeding 0.5 K. Phase and dummy-scan variation
are also flagged. A displayed candidate uses an explicit 0.8-K tolerance solely for
teaching; it is not accepted calibration. Stabilise/repeat and review phase/scans.
All 115 input hashes were checked after calculation; the protected profile is unchanged.
Mean-temperature Dref = 1.688079 × 10⁻⁹ m²/s is an approximate thermal reference,
different from the historical gradient-weighted effective reference 1.673921.
No hardware acquisition or instrument calibration change took place. Launch the
helper using xpy dosy_workshop.py; live TopSpin 3.6.4 execution remains unverified.

Prime's demonstrated DOSY flow reads processed Bruker pdata/N/1r series rather than
promising universal FID/ser/2rr import. Products differ from their numerical engines.
TP194 local/map agreement uses matching extraction, grid and protocol: internal
consistency on real data, not independent physical validation or chemical identity.
The 256-bin screenshot and 2048-bin table use different configurations. TP194's
projection keeps about 6% unassigned signal visible; two bands do not prove two species.

KK2 is an ARCHIVED analysis of 230 spectra in 10 ramps. The current integrity check
finds 213 changed processed files: 207 procs and six 1r. Checked acquisition files
still match. Do not claim the whole current processing snapshot is unchanged.
TTMS and temperature factors are applied once to the complete axis, without rescaling
KK2 to old result tables. Molecular weights are model-dependent apparent values.

Sources and limits
TXT notes come from the actual final PPTX files. Fuentes/ contains story, catalogue,
derived case data, simulation models/scripts and SHA-256 manifest.
SPOKEN_SCRIPT_20MIN_EN.txt contains only the narrative for the 25 main slides;
SPEAKER_NOTES_EN.txt contains the full technical notes for all 45 slides.
The 72 catalogue records overlap; they are not 72 independent DOSY algorithms. Labelled simulations
are not experiments or hardware limits. Scripts require documented dependencies
and, where indicated, local input sources. Review destinations before running.
Full papers, original experimental datasets and private QA are excluded.
Our ultrafast development requires a z gradient; quantitative validation is pending.


ACTUALIZACIÓN V8 / V8 UPDATE
La diapositiva 24 usa el mapa original DT2_map_10.png, sin recorte ni modificación.
Es una reconstrucción TRAIN2D del experimento UF D-T2 de 2025: NS=4, 32 ecos,
27.768 segundos para la adquisición completa. No es single-scan ni un resultado
del prototipo EPSI 9.4 actual. La exactitud absoluta de D y T2 requiere controles.
El PNG y su procedencia se incluyen; los datos originales ser no se redistribuyen.
Slide 24 uses the complete unmodified original DT2_map_10.png. It is a TRAIN2D
reconstruction of a 2025 UF D-T2 acquisition: four scans, 32 echoes, 27.768 seconds
for the full acquisition. This is neither a single-scan result nor output of the
current EPSI 9.4 prototype. Absolute D and T2 accuracy requires controls.

CALIBRACIÓN AUTOMÁTICA / AUTOMATIC CALIBRATION
El paquete v3 añade adquisición secuencial y procesado automático con TopSpin,
además de un barrido de nutación para estimar P90 con fase fija. El v2 sigue
incluido para preparar y analizar sin adquisición. Cada modo se elige en el menú.
Archivo autocontenido: dosy_workshop_v3.py. Copiar a exp/stan/nmr/py/user/ y ejecutar:
xpy dosy_workshop_v3.py
Revise README y los parámetros de la plantilla antes de elegir adquirir.
Se guardan propuestas y registros; no se cambian globalmente P1 ni gradpar.
Las pruebas de software usan TopCmds simulado; no validan el espectrómetro.
TopSpin 3.6.4 debe comprobarse con un ensayo controlado en el equipo real.
The v3 package adds sequential acquisition and automatic processing in TopSpin,
plus a fixed-phase nutation sweep to estimate P90. The v2 preparation/analysis
helper remains included. Select the intended mode in the menu.
Copy the self-contained dosy_workshop_v3.py to exp/stan/nmr/py/user/ and launch:
xpy dosy_workshop_v3.py
Review the README and template parameters before choosing acquisition. Proposals
and journals are saved; global P1 and gradpar are not changed. Software tests use
simulated TopCmds and do not validate the instrument. TopSpin 3.6.4 needs a
controlled pilot on the actual spectrometer.
