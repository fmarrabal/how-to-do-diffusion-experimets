# DiffAtOnce Academy 1.3 - Guía de investigación

Ediciones WPF y web. Esta guía complementa el curso original y el manual doctoral.

[Academy](https://diffatonce.com/academy)

## Cómo aprender con esta versión

Transformar una pregunta sobre difusión en una conclusión proporcionada a los datos.

1. Abre Investigación en Academy web o pulsa Investigación continua en WPF y selecciona ES/EN. La misma interfaz y los mismos motores numéricos sustentan ambas ediciones.
2. Recorre las doce etapas. Antes de pulsar una acción, escribe una predicción y su motivo en el panel de ayuda.
3. Usa las actividades Doctorado, Derivaciones y Animaciones para profundizar y vuelve al mismo caso.
4. Exporta la investigación al acabar cada sesión. Practica después con otra semilla y sin consultar el ejemplo resuelto.

Las siete ampliaciones enlazan muestra, incertidumbre, datos reales, competencias, diseño de controles, codificación espacial y tutoría/revisión.

**Comprobación:** Al terminar debes poder explicar qué mediste, cómo elegiste la ecuación, qué sesgos quedan y qué control podría refutarte.

**Límite:** Completar pantallas o superar pruebas de software no demuestra dominio ni valida un experimento.

## Qué conserva la misma muestra

Distinguir datos adquiridos, decisiones, supuestos y verdad de una simulación.

1. La semilla fija una muestra sintética reproducible; no identifica una molécula real.
2. Calibración, diseño, serie compleja, procesado y ajuste permanecen unidos a su identidad e historial.
3. Si cambias una decisión anterior, revisa las etapas posteriores y vuelve a calcular. Un resultado previo no prueba el nuevo diseño.
4. Al vincular integrales públicas o CSV, la evidencia se declara experimental/importada y su procedencia sigue siendo necesaria.

Las unidades internas son SI: D en m²/s, b en s/m² y gradiente en T/m. La interfaz muestra pulsos en µs y tiempos de secuencia en ms.

**Comprobación:** Comprueba identidad, unidades y estado del procesado antes de comparar dos resultados.

**Límite:** Los originales experimentales no se modifican. La calibración virtual no recalibra automáticamente datos importados ni el espectrómetro.

## 01 - La pregunta

Formular una hipótesis y un resultado que la pueda contradecir.

[Ver la captura real en el manual PDF](RESEARCH_MANUAL_ES.pdf)

1. Selecciona Dificultad oculta e Identidad reproducible; pulsa Crear otro caso sólo cuando quieras iniciar otra muestra.
2. Empieza con Señal aislada; después prueba Calibración del gradiente, Convección, Deriva temporal, Solapamiento o Fallos combinados.
3. Escribe una pregunta concreta: por ejemplo, si una diferencia de D puede explicarse por orden de rampa y no sólo por dos especies.
4. Registra qué observarías bajo cada hipótesis antes de adquirir.

La causa no se revela por acertar una palabra. Las decisiones y los controles deben sostener tu argumento.

**Comprobación:** Tu pregunta contiene una observación medible, una alternativa y un control posible.

**Límite:** Elegir un preset informa de la familia del problema. Para evaluar sin esa pista usa casos y preguntas reservados del docente; una práctica guiada no es una prueba completamente ciega.

## 02 - Calibrar antes de medir

Separar calibración RF, escala de gradiente y condiciones del patrón.

[Ver la captura real en el manual PDF](RESEARCH_MANUAL_ES.pdf)

1. Inspecciona la curva de nutación con signo. Identifica el primer nulo de 180° mediante el máximo anterior y el cambio de signo.
2. Introduce P90 = P180/2 a potencia y condiciones constantes. Un nulo de 360° se divide entre cuatro; el nulo aislado no identifica su orden.
3. Ajusta el decaimiento del patrón frente a b nominal; para una escala común g_real=s·g_nominal usa s=√(D_nominal/D_ref).
4. Comprueba temperatura del patrón y referencia; después pulsa Aplicar calibración al caso.

Si se usa b nominal, un error de escala del gradiente aparece al cuadrado en D. Repetir más scans no elimina ese sesgo.

**Comprobación:** Justifica el nulo elegido, el D de referencia, su temperatura y qué forma de onda cubre la calibración.

**Límite:** P90 debe comprobarse para la muestra y potencia adecuadas. p30, d20 y d5 requieren el programa de pulsos concreto; no tienen una traducción universal.

## 03 - Diseñar una medida informativa

Elegir una ventana de atenuación y controles dentro de un presupuesto.

1. Elige Eco de espín, Eco estimulado, LED o Doble estimulado y documenta por qué.
2. Ajusta δ, Δ, d5/LED, gradiente máximo, niveles, NS, réplicas y orden de rampa.
3. Pulsa Comprobar diseño y presupuesto; revisa duración, b máximo y restricciones antes de adquirir.
4. Predice qué cambiará al aumentar Δ o invertir/intercalar la rampa. Cambia una variable cada vez cuando quieras atribuir una causa.

Más ponderación puede mejorar contraste y perder señal. LED añade tiempo; las pérdidas y la compensación dependen de la secuencia.

**Comprobación:** Puedes explicar qué aporta cada nivel y qué parte de tu presupuesto sirve para controlar errores.

**Límite:** Los tiempos son un modelo docente ideal. Verifica el programa real y los límites del instrumento antes de trasladar una receta al laboratorio.

## 04 - Adquirir la misma muestra

Relacionar el diseño con una serie compleja y con su orden temporal.

1. Después de calibrar y diseñar, pulsa Adquirir la serie virtual.
2. Inspecciona el FID y el número de adquisiciones; conserva la identidad de muestra y semilla.
3. Compara una réplica con una adquisición invertida/intercalada. Describe qué debería cambiar si existe deriva.
4. Conserva la primera investigación exportada antes de iniciar otra semilla.

Los datos sintéticos contienen ruido reproducible y dificultades fijadas por la muestra; el FID no es un gráfico decorativo.

**Comprobación:** La señal, el orden temporal y b se mantienen emparejados en tu análisis.

**Límite:** Esta acción no envía órdenes a TopSpin ni adquiere una muestra física. Los datos experimentales entran por Datos públicos o importación.

## 05 - Procesar con decisiones explícitas

Conservar el signo y comprobar la dependencia de fase, ventana y línea de base.

1. Ajusta Corrección de fase, Offset sustraído, apodización y Ventana de señal.
2. Pulsa Procesar e integrar. Inspecciona el espectro y el decaimiento de las integrales.
3. Compara Todo el espectro, Señal 1 y Señal 2 cuando exista solapamiento.
4. Explica por qué una ventana o fase distinta puede alterar una atenuación sin que D física haya cambiado.

Una integral es una decisión sobre datos complejos. Tomar sólo magnitudes o recortar valores negativos puede cambiar el ruido y sesgar el ajuste.

**Comprobación:** Tu informe permite repetir fase, ventana y tratamiento de línea de base.

**Límite:** Para archivos Bruker reales comprueba filtro digital, referencia, secuencia y metadatos en el flujo experimental. No traslades índices de otra muestra.

## 06 - Interpretar sin sobreafirmar

Comparar modelos sobre exactamente las mismas observaciones.

1. Selecciona Monoexponencial, NNLS, Tikhonov no negativo o L1 no negativo y pulsa Ajustar los mismos datos.
2. En ILT registra λ y la malla; compara residuos, estabilidad y máximos, no sólo el aspecto del mapa.
3. Mantén el mismo procesado para atribuir cambios al método. Después estudia por separado la sensibilidad al procesado.
4. Vuelve al laboratorio Doctorado para profundizar en el núcleo ILT, correlaciones y análisis conjunto.

Una curva bien ajustada no determina una distribución única. La penalización introduce una preferencia y puede fusionar o crear máximos aparentes.

**Comprobación:** Puedes distinguir ajuste numérico, resolución, distribución y asignación química.

**Límite:** La D monoexponencial de una mezcla es condicional al modelo. No atribuyas masas absolutas ni especies a partir del mapa por sí solo.

## 07 - Propagar errores compartidos

Separar dispersión aleatoria de sesgos y dependencias comunes.

[Ver la captura real en el manual PDF](RESEARCH_MANUAL_ES.pdf)

1. Introduce Muestras Monte Carlo y las desviaciones de escala g, temperatura, procesado, ruido y modelo b.
2. Pulsa Propagar errores compartidos y compara contribuciones e intervalo condicional.
3. Repite reduciendo sólo ruido; después reduce la incertidumbre de calibración. Compara la diferencia.
4. Describe qué fuentes comparten una misma realización entre gradientes y señales, y cuáles varían por observación.

La misma calibración puede desplazar juntas varias D. Tratar ese error como ruido independiente fabricaría información que no se adquirió.

**Comprobación:** Justifica un control que reduzca la fuente dominante y enumera errores que tu intervalo no cuantifica.

**Límite:** El intervalo es condicional a los modelos y distribuciones introducidos. No es cobertura experimental validada ni corrige automáticamente un modelo erróneo.

## 08 - Elegir la próxima medida

Usar la ambigüedad para diseñar un control discriminante.

1. Compara Mayor rango b, Repetir el diseño, Invertir el orden, Cambiar Δ y Compensación de flujo.
2. Escribe una predicción antes de pulsar Comparar diseños.
3. Elige una adquisición y pulsa Observar control reservado. Las observaciones reservadas usan una realización independiente.
4. Contrasta tu predicción con los resultados y explica qué alternativas sobreviven.

Dos distribuciones pueden predecir casi igual los datos disponibles y divergir en otra región b. La adquisición propuesta explora esa diferencia.

**Comprobación:** Puedes defender por qué este control discrimina mejor que adquirir más puntos equivalentes.

**Límite:** La selección de diseño y el dato reservado sintético no son validación externa de una muestra real. La compensación de flujo ideal no equivale a cualquier programa doble STE.

## 09 - RF, gradientes y espacio

Comprender el origen físico de la codificación espacial y sus límites numéricos.

[Ver la captura real en el manual PDF](RESEARCH_MANUAL_ES.pdf)

1. Ajusta celdas espaciales, longitud, duración/amplitud RF, barrido chirp, gradientes, evolución, lectura y perfil de bobina.
2. Pulsa Calcular Bloch-Torrey; inspecciona magnetización, fase, perfil transversal y señal de lectura.
3. Pulsa Comprobar convergencia para comparar el paso temporal y la malla refinados. Revisa los avisos de aliasing.
4. Compara con el modelo introductorio ultrafast/SPEN de Doctorado: explica qué añade el cálculo desde RF y qué continúa siendo ideal.

El modelo es dM/dt = Ω×M + D·d²M/dz² - (Mx/T2, My/T2, (Mz-1)/T1). Ω contiene RF y gradiente, con fase chirp integrada en el tiempo. Se usan paredes reflectantes, difusión Crank-Nicolson y rotaciones exactas por paso. La lectura suma magnetización compleja ponderada por la bobina.

**Comprobación:** Puedes distinguir fase RF, integral física del gradiente, resolución nominal y error de discretización.

**Límite:** Durante RF, γ∫Gdt no es una vía de coherencia ni un b DOSY. Con lectura lineal, un offset Δf produce Δz_aparente=Δf/(γHz·G): no es movimiento molecular. El protocolo genérico no valida una secuencia UF/SPEN-DOSY concreta.

## 10 - Comprobar lo aprendido

Demostrar transferencia y retención, además de completar actividades.

[Ver la captura real en el manual PDF](RESEARCH_MANUAL_ES.pdf)

1. Realiza Diagnóstico inicial antes de consultar pistas. Usa Practicar para trabajar conceptos pendientes y registra la ayuda utilizada.
2. Completa Caso de transferencia con parámetros nuevos e inspecciona el estado por competencia. Vuelve a un caso que obligue a usarla.
3. El piloto docente voluntario empieza vacío. Si participas, usa un código local opcional, marca el consentimiento y pulsa Consentir y abrir el caso inicial. Pretest y postest contienen siete preguntas con semillas diferentes; declara si respondiste sin ayuda.
4. El caso de retención se habilita tras siete días, en la fecha mostrada; no hay un botón para adelantar ese plazo. Usa Comprobar fecha actual y Exportar resultados del piloto. No se precargan alumnos ni resultados.

Las comprobaciones automáticas se limitan a elecciones y números explícitos. Un argumento escrito necesita revisión humana.

**Comprobación:** Resuelve una situación nueva sin pista y explica la regla que aplicaste.

**Límite:** La aplicación no certifica formación doctoral ni deduce comprensión de la longitud del texto. La eficacia educativa debe medirse con estudiantes y evaluación independiente.

## 11 - Defender, revisar y mejorar

Conservar un razonamiento revisable y una segunda versión trazable.

[Ver la captura real en el manual PDF](RESEARCH_MANUAL_ES.pdf)

1. Completa objetivo, física, diseño, procesado, incertidumbre, controles y conclusión.
2. Pulsa Guardar una nueva entrega. Exportar expediente conserva investigación, evidencias y entregas.
3. El docente usa los cinco criterios 0-4, cita evidencias, escribe comentarios/preguntas y pulsa Crear y exportar devolución.
4. El alumno utiliza Importar devolución, responde a las preguntas y guarda otra entrega sin sustituir la primera.

Las devoluciones se vinculan a una entrega concreta y su identidad; una revisión de otro caso no debe convertirse en su evaluación.

**Comprobación:** Tu segunda versión explica qué cambiaste, qué evidencia te convenció y qué permanece sin resolver.

**Límite:** La puntuación y el juicio son del docente. Las verificaciones de integridad no autentican la identidad civil del evaluador ni sustituyen un sistema institucional de notas.

## 12 - Trabajar con originales públicos

Procesar experimentos reales y reconocer cuándo falta información para inferir D.

[Ver la captura real en el manual PDF](RESEARCH_MANUAL_ES.pdf)

1. Abre Datos públicos y selecciona una adquisición PMA1, PMA6, PMMA1 o PMMA6. Cada grupo incluye dos adquisiciones del repositorio.
2. La carga comprueba bytes y SHA-256 antes de interpretar FID y metadatos. Inspecciona programa, temperatura guardada, filtro digital, NS y RG.
3. Ajusta fase, apodización y ventana; pulsa Procesar serie pública. Proporciona un b por adquisición y documenta su procedencia antes de ajustar.
4. Pulsa Continuar la investigación con estas integrales para vincularlas al caso. Documenta qué condiciones permiten comparar las dos adquisiciones.

Los ocho conjuntos proceden del depósito Monash/Figshare de Silva, McKay y Junkers, CC BY 4.0. Las condiciones guardadas no acreditan por sí solas controles de temperatura o convección.

**Comprobación:** Distingue ausencia de b verificados, escala nominal, calibración absoluta y una D condicional al procesado.

**Límite:** Estos ocho conjuntos no aportan parámetros DOSY guardados suficientes para justificar automáticamente b. No inventes ese eje ni una D verdadera o masa absoluta.

## Ejemplo continuo - preparar y adquirir

Reproducir una investigación sintética con parámetros y salidas verificables.

1. En La pregunta, selecciona Fallos combinados y semilla 20261030; crea el caso RJ-combined-20261030.
2. El primer nulo de 180° es 19.8993 µs y el máximo anterior está en 9.94964 µs. Introduce P90=9.94964 µs.
3. Usa D_ref=1.9×10^-9 m²/s a 298.15 K. La curva nominal ajusta D=2.20719e-09 m²/s: s=√(D_nominal/D_ref)=1.07781.
4. Introduce esa escala, ambas temperaturas 298.15 K y aplica la calibración. Diseña STE: δ=2 ms, Δ=80 ms, LED=5 ms, g_max=0.3 T/m, 20 niveles, NS=8, una réplica, reciclado=2 s, orden ascendente y presupuesto=15 min.
5. Comprueba duración aproximada 6.352 min y b_max=2.37445e+09 s/m²; adquiere la serie virtual.

Los valores se calculan con el motor que acompaña a esta edición. Las cifras mostradas están redondeadas; la exportación conserva la precisión disponible.

**Comprobación:** Compara el ejemplo con escala g=1 en una copia exportada, manteniendo el resto de decisiones.

**Límite:** Este ejemplo no proporciona parámetros de operación para tu espectrómetro ni un resultado experimental aceptado.

## Ejemplo continuo - interpretar y cuestionar

Llegar a un resultado reproducible que todavía exige controles.

1. Procesa con fase=0°, offset=0, LB=0 Hz y ventana Todo el espectro. Ajusta Monoexponencial con los mismos datos.
2. El ejemplo devuelve D≈4.92791e-10 m²/s y RMS residual≈0.0198293. Una cifra reproducible no convierte la mezcla/fallo combinado en una especie única.
3. Propaga 40 muestras Monte Carlo: SD relativa g=0.02, SD T=0.3 K, procesado=0.01, ruido=0.01 y escala b de secuencia=0.01.
4. El intervalo condicional ilustrativo es [4.51375e-10, 5.48915e-10] m²/s. Compara las contribuciones antes de decidir qué reducir.
5. Predice el efecto de Invertir el orden y observa el control reservado. Escribe qué explica y qué no explica la diferencia, y prepara una entrega.

El ejemplo muestra por qué una estimación, su incertidumbre y una explicación causal son objetos distintos.

**Comprobación:** Prueba otra semilla sin copiar estos valores: la justificación debe sobrevivir al cambio de muestra.

**Límite:** Si cambias versión, parámetros, procesado o semilla, no fuerces coincidencia con esta tabla. Guarda y explica la nueva identidad.

## Beatrix, fuentes y modos de respuesta

Utilizar ayuda trazable sin sustituir tu predicción ni el cálculo.

1. Escribe primero Predicción y motivo. Pulsa Pista siguiente para recibir ayuda gradual vinculada a la etapa.
2. Introduce Tu pregunta y pulsa Consultar fuentes: la recuperación documental presenta pasajes revisados y referencias.
3. En WPF, Preguntar al modelo local solicita la inferencia disponible con contexto acotado. Lee siempre la etiqueta de modo y distingue guía documental de texto generado.
4. Comprueba cualquier número en el motor de cálculo y contrasta la respuesta con las fuentes citadas.

La edición web usa guía documental, no ejecuta un LLM en PHP. En Windows sólo se usa un modelo cuyo manifiesto y evaluación CPU estén aprobados; en caso contrario se ofrece guía documental. Un candidato entrenado no se convierte automáticamente en el modelo activo.

**Comprobación:** Puedes señalar qué parte procede de una fuente, cuál del cálculo y cuál de una generación real.

**Límite:** Recuperación documental, entrenamiento ejecutado y modelo aprobado son estados distintos. La fluidez no valida una ecuación, calibración, asignación ni evaluación del alumno.

## Protocolo docente y evaluación independiente

Comprobar si el recorrido mejora decisiones en situaciones nuevas.

[Ver la captura real en el manual PDF](RESEARCH_MANUAL_ES.pdf)

1. Antes del curso, reserva casos y preguntas de transferencia que no se usen para entrenar al tutor ni para seleccionar parámetros.
2. Registra diagnóstico inicial, decisiones, pistas consultadas, predicciones y primera entrega.
3. Dos docentes pueden revisar informes con la misma rúbrica, comparar desacuerdos y documentar la segunda versión.
4. Realiza caso final diferente y revisión diferida. Compara física, controles, incertidumbre y calidad de la conclusión, no sólo respuestas de opción múltiple.

El panel de Competencias ejecuta el piloto local con consentimiento, casos inicial/final distintos y retención diferida. La revisión de argumentos es humana. Este manual no presenta resultados de una cohorte que no se ha evaluado.

**Comprobación:** Define por adelantado qué mejora sería relevante y conserva también fallos y resultados negativos.

**Límite:** Las pruebas de software verifican comportamiento informático y controles sintéticos. No sustituyen revisión experta ni evaluación educativa independiente.

## Guardar, importar y reproducir

Conservar evidencia sin confundir estado local, originales y resultados.

1. Exportar investigación/expediente produce JSON de la versión 1.3: muestra, decisiones, resultados, aprendizaje y entregas. El expediente de interfaz omite los FID brutos: conserva los originales por separado.
2. Importar investigación restaura un expediente compatible. Para reprocesar, vuelve a cargar la serie original o readquiere la simulación reproducible. Importar devolución exige una entrega correspondiente y verificación de su identidad.
3. La importación CSV requiere pares b/señal finitos y unidades correctas. Una procedencia local sin verificar no adquiere licencia ni calibración por importarse.
4. Para reproducir, registra versión, semilla o hashes, parámetros, fuentes b, operaciones de procesado, método y controles. Guarda el expediente fuera de la caché del navegador.

El almacenamiento es local. Cambiar de navegador, limpiar caché o usar otro perfil puede cambiar el progreso visible; la exportación es la copia transportable.

**Comprobación:** Abre una exportación en una sesión aislada y comprueba identidad y resultados antes de dar por terminada una entrega.

**Límite:** Los JSON tienen límites de tamaño y compatibilidad. No edites hashes para forzar una importación. La web no sincroniza notas ni datos con una cuenta docente.

## Fuentes, enlaces y problemas frecuentes

Encontrar la ecuación, el dato y la ayuda que corresponden a cada afirmación.

1. Sinnaeve (2012), DOI 10.1002/cmr.a.21223, y Kuchel et al. (2012), DOI 10.1002/cmr.a.21241: fuentes del recorrido matemático. Consulta los 20 capítulos de Derivaciones para símbolos, páginas, ecuaciones y supuestos.
2. Torrey (1956), DOI 10.1103/PhysRev.104.563: difusión en las ecuaciones de Bloch. Shrot, Shapira y Frydman (2004), DOI 10.1016/j.jmr.2004.08.001: codificación espacial continua.
3. Silva, McKay y Junkers, DOI 10.26180/33075584.v1, CC BY 4.0: procedencia de los archivos experimentales públicos; conserva su atribución.
4. Si faltan datos públicos, revisa acceso al paquete/versionado. Si falta b, documenta su derivación; si aparece aliasing, revisa malla/lectura. Ante un fallo de guardado, exporta antes de cerrar.

Este manual complementa el manual doctoral y el curso original, que se mantienen disponibles con sus fuentes y convenciones explícitas.

**Comprobación:** Toda conclusión final identifica datos, modelo, condiciones, incertidumbre y limitaciones.

**Límite:** Un grupo de archivos, un buen ajuste o una captura atractiva no validan por sí solos una explicación física.

[Manual doctoral](DOCTORAL_MANUAL_ES.pdf)

https://doi.org/10.1002/cmr.a.21223
https://doi.org/10.1002/cmr.a.21241
https://doi.org/10.1103/PhysRev.104.563
https://doi.org/10.1016/j.jmr.2004.08.001
https://doi.org/10.26180/33075584.v1
