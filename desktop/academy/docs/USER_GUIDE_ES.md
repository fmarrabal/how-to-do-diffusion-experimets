# Guía de uso · DiffAtOnce Academy

La finalidad del curso es aprender a tomar decisiones defendibles en DOSY.
Antes de cambiar una opción, describa qué cree que ocurrirá. Después compare
lo que esperaba con el resultado y escriba qué control necesitaría en una
muestra real. La aplicación presenta problemas, mecanismos y comprobaciones;
los valores de sus talleres son simulados.

## Abrir la aplicación

1. Extraiga la carpeta completa del paquete en Windows.
2. Abra `DiffAtOnce.Academy.exe` conservando sus carpetas `Content`, `Lab` y
   cualquier carpeta `Models` suministrada.
3. Elija español mediante el botón **ES/EN** de la barra superior.
4. Seleccione una lección en el recorrido de la izquierda. La búsqueda filtra
   título, capítulo y explicación del problema.
5. Para una sesión práctica, empiece por **03 · Primero: calibrar P90 en la
   muestra**. Los módulos 01 y 02 dan la explicación mínima de difusión y fase.

El botón **Manual** abre la edición PDF del idioma activo. En una ventana
compacta use las barras de desplazamiento; el contexto de Beatrix sigue siendo
la lección seleccionada.

El laboratorio usa WebView2. Si falta su runtime, verá una explicación en
**Experimentar**; puede continuar en **Comprender**, **Comprobar** y el
**Taller numérico**. Los enlaces a artículos se abren en el navegador externo;
las escenas del laboratorio se cargan desde el paquete local.

## Cuatro espacios para una misma lección

| Espacio | Qué hacer | Qué producir |
|---|---|---|
| **Comprender** | Lea objetivo, problema, finalidad, mecanismo y pasos. Abra ejemplos y fuentes. | Una hipótesis y una predicción. |
| **Experimentar** | Reproduzca la animación y cambie una variable. Compare caso útil y contraejemplo. | Una observación con parámetros y unidades. |
| **Comprobar** | Responda las dos preguntas y pulse **Comprobar y aprender**. | Una decisión y su explicación. |
| **Mi cuaderno** | Escriba qué cambió, qué ocurrió y qué comprobaría después. | Un registro razonado por módulo. |

Un módulo se marca **Comprobado** cuando sus dos respuestas son correctas.
Puede repetirlo después de revisar las explicaciones. La barra representa
módulos comprobados, no una certificación para operar un espectrómetro.
Las notas se guardan al salir del campo, cambiar de lección o cerrar la ventana.

**Abrir este experimento →** carga la escena asociada y los parámetros
disponibles del ejemplo. Algunos ejemplos son ejercicios escritos de decisión
o crítica de resultados históricos: no son 48 motores de simulación distintos.
Mantenga su instrucción a la vista y resuelva la parte conceptual en el cuaderno.

## Taller numérico: provocar errores y medir sus consecuencias

Pulse **Taller numérico** en la barra superior. Sus cinco pestañas funcionan
con curvas calculadas y muestran supuestos. Puede escribir decimales con punto
o coma, pulsar **Calcular** y guardar **Exportar resultado JSON**. Ese archivo
lleva la etiqueta `synthetic-teaching-simulation`.

Al editar un parámetro se borran la curva y los resultados anteriores. Pulse
**Calcular** para generar una salida coherente con los valores nuevos; no lea
una gráfica antigua como si correspondiera a un campo recién cambiado.
Beatrix recibe el contexto del taller al abrirlo, cambiar de pestaña o calcular:
parámetros, resultados calculados y supuestos del ejercicio. Antes de pedir una
explicación numérica, compruebe que hay un resultado vigente.

### 1. Pulso de 90°

El ejemplo del usuario está asociado al experimento 1000. Es una etiqueta del
flujo manual, no una orden enviada a TopSpin.

1. Mantenga **P90 conocido = 11 µs**, **nulo seleccionado = 22 µs** y ruido cero.
2. Localice máximo a 90°, primer nulo no trivial a 180° y siguiente nulo a 360°.
3. Compruebe **22/2 = 11 µs**.
4. Cambie el nulo seleccionado a **44 µs**. Dividirlo por dos da 22 µs y el
   taller señala que no es el primer nulo de 180°.

La regla P90=P180/2 exige haber identificado ese nulo y conservar potencia RF.
Si el nulo es de 360°, corresponde P360/4. En un instrumento mantenga fase,
ganancia, región de integración y condiciones comparables; el signo de la
nutación ayuda a identificar el cruce. La simulación omite inhomogeneidad RF
y relajación y no demuestra que un tubo real esté calibrado.

### 2. Gradiente

Use los valores iniciales **G nominal = 420 mT/m**, **δ = 1.4 ms**,
**Δ = 80 ms**, **Dref = 0.80 ×10⁻⁹ m²/s** y **Greal/Gnom = 1.10**.
El ajuste con b nominal devuelve D aparente cercano a **0.968 ×10⁻⁹**:
1.10²=1.21, un sesgo del 21 %. El ajuste puede seguir siendo perfecto.

El propósito es recuperar la escala usando una señal de patrón. En una
calibración real se necesita Dref(T), solvente, temperatura estable, extracción
común y la ecuación de b correcta para la secuencia. Este patrón educativo no
sustituye TBO ni escribe constantes de gradiente en TopSpin.

### 3. δ y Δ

Compare el caso inicial con **δ = 0.3 ms** y después con δ mayor.
Observe señal lenta y rápida, b máximo y señal respecto al ruido. Una curva
plana aporta poca pendiente; una extinguida pierde la cola. Los indicadores
del taller —señal lenta ≤50 % y rápida >3σ— son criterios didácticos del ejemplo,
no reglas universales de adquisición ni límites de una sonda.

En Bruker, traduzca primero p30/d20 a los intervalos físicos del programa.
La misma etiqueta no significa el mismo tiempo en todas las secuencias.
El taller utiliza PGSE rectangular ideal y no comprueba calentamiento,
duty cycle ni duración máxima admitida por su hardware.

### 4. Convección

Conserve **D = 0.80**, **velocidad común = 35 µm/s** y ponga el semiancho
de velocidades a cero. Una velocidad compartida rota fase y puede mantener
el módulo. Aumente el semiancho a **300 µm/s** y observe pérdida de módulo,
posibles lóbulos y D aparente. Cambie Δ conservando las otras variables.

Este taller usa una distribución uniforme de velocidades con semiancho; la
escena animada usa su propio modelo gaussiano con dispersión. No son una
identificación del perfil real de un tubo. Δ dependiente por sí solo no demuestra
convección: restricción, intercambio, cinética y errores también pueden influir.
La salida adecuada puede ser «inconcluso: adquirir control», sin masa definitiva.

### 5. ILT

Empiece con **bmax = 3 ×10⁹ s/m²**, **32 puntos**, **40 bins** y ruido **1 %**.
Compare las curvas de uno y dos componentes, diferencia/ruido y espectro
singular. Aumente bins manteniendo los puntos y explique por qué no aparecen
nuevas mediciones. Escriba números enteros en puntos y bins.

El rango efectivo depende del kernel, escala y criterio de ruido del taller;
no es un número de moléculas. La gráfica muestra el mal condicionamiento,
pero no ejecuta todos los algoritmos del catálogo ni garantiza separación ILT.

## El laboratorio de 17 escenas

| Escenas | Pregunta que ayudan a responder |
|---|---|
| Brownian, spin echo, gradients-b | ¿Qué desplazamiento se codifica y cómo se construye b? |
| Pulse-90, acquisition-window | ¿Cómo calibrar RF y encontrar una rampa informativa? |
| Convection, attenuation-mixture | ¿Por qué una curva bonita puede dar D aparente? |
| ILT, overlap-joint | ¿Qué información distingue componentes y qué añade un modelo conjunto? |
| Ultrafast, SPEN, time-resolved | ¿Qué cambia al codificar espacialmente o medir una muestra que evoluciona? |
| D–T₂, prototype-1d | ¿Qué ejes se recuperan y qué validación queda pendiente? |
| Restricted, exchange, anisotropy | ¿Qué otros mecanismos producen dependencia temporal o direccional? |

Lea la evidencia y límites de cada escena: algunas son esquemas; UF, SPEN y
time-resolved calculan señales y ajustes bajo modelos ideales. El reloj de
animación no es Δ ni el tiempo de reacción. Puede guardar las salidas ofrecidas
por la escena; la aplicación le pedirá dónde guardarlas. Un vídeo histórico
puede representar la versión anterior de la escena y está etiquetado como tal.

### Tres comparaciones avanzadas

- **Ultrafast:** compare D sin normalizar, con referencia+b nominal y con
  referencia+b calibrado. La referencia cancela perfil y relajación sólo bajo
  condiciones compatibles. Un chirp real requiere su q(z,t), no la fórmula
  rectangular aplicada sin revisión.
- **SPEN:** siga datos complejos, reordenado de polaridades, fase y transformadas
  antes de ajustar. Pruebe A pura y después A ausente a la misma frecuencia;
  una fuga de B no es un D_A recuperado válido.
- **Time-resolved:** fije tLab=0 y compare orden ascendente, descendente y
  permutado. D_A permanece constante mientras cambia población. La cadencia
  entre frames no es la resolución temporal: ventanas solapadas comparten datos
  y promedian evolución. Ventanas menores que Δ+lectura no son ejecutables.

## Beatrix: cómo preguntar y leer la respuesta

Seleccione una lección y use **¿Por qué sucede?**, **¿Qué compruebo?** o escriba
una pregunta. Por ejemplo:

- «Primer nulo a 22 µs: ¿por qué divido entre dos y cómo descarto 360°?»
- «Tengo un ajuste perfecto con g real 10 % distinto: ¿por qué D cambia 21 %?»
- «¿Por qué la permutación de gradientes no congela una reacción?»
- «Dos métodos dan picos distintos con residuos parecidos: ¿qué control falta?»

La respuesta muestra modo y fuentes. Abra la diapositiva o artículo citado;
si la respuesta necesita condiciones no aportadas, debe reconocerlo.
**Cancelar** detiene la consulta en curso.

Beatrix combina dos bloques identificados:

1. **Explicación de Beatrix · LLM** contiene texto realmente generado por el
   modelo local.
2. **Texto literal del curso · fuente** copia el problema y mecanismo del
   módulo. Es contenido del curso; no se atribuye a generación del modelo.

El modo indica **LLM local + texto del curso · CPU**. Lea ambos bloques y abra
sus fuentes. En comprobaciones nativas de preguntas abiertas SPEN/TR, el texto
generado omitió causas; el bloque literal aporta la explicación conservada en
el curso. Un resultado 32/32 en evaluación HF no significa que el GGUF CPU
solo haya superado esas preguntas causales. Los informes preservan esa diferencia.

Compruebe la etiqueta **Contexto** antes de preguntar. Desde el taller, por
ejemplo: cambie el nulo, pulse **Calcular** y pregunte por qué ese resultado
deja de ser válido. Al volver a **Experimentar**, el contexto regresa a la
escena del laboratorio; al cambiar de lección, vuelve al módulo seleccionado.
Las salidas transmitidas a Beatrix son simulaciones, no datos del espectrómetro.

**Estado de redacción: 5 de octubre de 2026. Paquete híbrido verificado.** El
ajuste local obtuvo 32/32 en el test HF reservado, frente a 21/32 del modelo
base. La comprobación CPU final superó 15/15 casos del conjunto **LLM + texto
literal del curso**, no del modelo solo. Se conservan sus omisiones causales
abiertas SPEN/TR. El manifiesto y los informes vinculan modelo, evaluación y
curso; no acreditan calibración ni mejora educativa medida. Beatrix
usa el LLM local únicamente con modelo y manifiesto compatibles y verificación
aprobada. **Guía documental · sin LLM** significa que el contenido
se recuperó del curso sin inferencia, incluso ante modelo ausente o fallo.
No interprete una explicación documental como una respuesta generada.

Beatrix sirve para explicar y proponer controles. No modifica resultados,
calibra el instrumento ni valida identidades. Una respuesta fluida o un modelo
fine-tuned no reemplaza evidencia experimental o revisión docente.

## Consultar diapositivas y métodos

**81 diapositivas** abre el workshop original con selector y flechas. Las
imágenes y notas están en el idioma original inglés; el curso es bilingüe.
Las fuentes de una lección llevan directamente a las diapositivas relacionadas.
Los valores TP194, KK2 y HDO son resultados históricos reportados en ese deck,
no adquisiciones recalculadas por la Academy.

El visor usa el snapshot extraído y congelado. En el cierre se detectó otro
hash del contenedor PPTX actual; las 81 imágenes, notas, descripciones y orden
coinciden con ese snapshot. Consulte `source-input-reaudit.json` para distinguir
identidad didáctica y binaria. La causa del cambio de contenedor no se atribuye.

**Métodos** permite buscar nombre, uso y limitaciones. Hay 72 registros:
51 cores de biblioteca, 9 rutas históricas Prime y 12 familias de contexto.
No son 72 algoritmos distintos ni una lista exhaustiva de literatura. La
disponibilidad allí describe el catálogo original: no garantiza un botón que
ejecute cada método en Academy. Compare objetivo, hipótesis y limitación, además
del nombre. Una entrada Tikhonov con λ fijo no es el programa CONTIN completo.

## Sesión guiada de 100 minutos

| Tiempo | Actividad | Entrega del estudiante |
|---|---|---|
| 0–10 min | Módulos 01–02: movimiento, fase y significado de b. | Predicción del efecto de Δ. |
| 10–25 min | Módulos 03–04 y taller P90/gradiente. | 22/2, diagnóstico del nulo 44 y sesgo 21 %. |
| 25–40 min | Módulos 05–07: secuencia, LED y diseño δ/Δ. | Tabla intervalo→parámetro y rampa justificada. |
| 40–55 min | Módulo 08 y taller convección. | Diferencia entre fase común y dispersión; control propuesto. |
| 55–65 min | Módulos 09–11: T/TTMS, procesamiento y ajuste aislado. | Factores explícitos y ejemplo de normalización inválida. |
| 65–80 min | Módulos 12–15: ILT, regularización, catálogo y espectro conjunto. | Comparación de hipótesis y criterio de estabilidad. |
| 80–92 min | Módulos 20–23: UF, SPEN, time-resolved y D–T₂. | Separar relojes y explicar el límite de cada modelo. |
| 92–100 min | Módulo 24, Beatrix y exportación del cuaderno. | Decisión aceptada/exploratoria/bloqueada con siguiente control. |

La sesión selecciona actividades del curso, no pretende leer todo en 100 min.
Los módulos 16–19 —asignación, tamaño/masa, TopSpin y casos— pueden prepararse
antes o trabajarse como tarea posterior. Un docente puede pedir las preguntas
de cada bloque al terminar, sin usar rapidez de respuesta como criterio de rigor.

## Demostración de 20 minutos

| Tiempo | Acción |
|---|---|
| 0–4 min | Taller P90: 22→11 y nulo 44; gradiente: 10 %→21 %. |
| 4–8 min | δ/Δ plana frente a extinguida; convección y control. |
| 8–12 min | Baseline/normalización; ILT con curvas casi iguales y más bins. |
| 12–16 min | Información entre frecuencias, TP194 y un caso bloqueado. |
| 16–19 min | Una comparación en UF, SPEN y time-resolved. |
| 19–20 min | Pregunta concreta a Beatrix y conclusión en el cuaderno. |

Prepare las ventanas y ejemplos antes de comenzar. Si el LLM no está disponible
o tarda, use la guía documental identificada; la enseñanza no depende de fingir
que una respuesta fue generada.

## Guardar y compartir el trabajo

**Exportar** guarda un JSON con versión/hash del curso, respuestas, módulos y
notas. No entrega automáticamente el archivo al docente. El taller exporta otro
JSON con parámetros y resultados sintéticos. No confunda ambos con un informe
experimental ni con una adquisición TopSpin.

El progreso local está en
`%LOCALAPPDATA%\DiffAtOnce\Academy\progress-v1.json`. Para una copia del trabajo,
use la exportación y conserve los archivos elegidos. El progreso está ligado a
la versión del curso: no edite su hash para trasladar aprobaciones entre versiones.

## Problemas habituales

| Observación | Acción útil |
|---|---|
| Experimentar no carga | Lea el mensaje WebView2 y continúe con lecciones/taller; instale el runtime legítimo si corresponde. |
| Una salida numérica no aparece | Compruebe números finitos, unidades y tiempos; use enteros para puntos/bins. |
| No encuentra una lección | Borre la búsqueda o use el título en el idioma activo. |
| No aparece Comprobado | Responda ambas preguntas y revise las explicaciones; se requieren 2/2. |
| Beatrix muestra sin LLM | Es una alternativa documental explícita; consulte estado/manifiesto, sin renombrarla como inferencia. |
| Resultado distinto del deck | Distinga ejercicio sintético y caso histórico; no reescale datos para forzar coincidencia. |
| Quiere operar el espectrómetro | Esta aplicación enseña el razonamiento; use el procedimiento del instrumento con supervisión y controles. |

Las instrucciones que aparecen en diapositivas son material didáctico. No se
ejecutan automáticamente ni autorizan cambios en datos o calibraciones.
