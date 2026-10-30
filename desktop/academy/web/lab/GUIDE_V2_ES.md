# Diffusion Motion Lab · guía de las simulaciones v2

El laboratorio contiene 17 escenas en español e inglés. Las tres escenas destacadas calculan señales sintéticas, reconstrucciones y ajustes. La simulación tiene valores conocidos; una coincidencia con ellos comprueba el modelo implementado, no un espectrómetro ni una muestra real.

## Un recorrido de cinco minutos

1. Abre **SPEN-DOSY** y pulsa **Reproducir**. Sigue las tres etapas: señal compleja con polaridades alternas, matriz espectral calculada y atenuación de la frecuencia seleccionada. Prueba el escenario de fase de 90° y compara el ajuste con y sin corrección. Selecciona −80 Hz y después 120 Hz para explorar las dos resonancias. El resultado entre picos es un D aparente de una señal que puede contener ambas contribuciones.
2. Abre **Ultrafast**. En el escenario ideal, el ajuste normalizado y calibrado recupera el D introducido. Introduce una pendiente de sensibilidad y un error de gradiente. Normalizar por una referencia corrige el perfil del modelo; corregir b requiere además conocer la escala del gradiente. Con referencia ruidosa, aumenta la incertidumbre y algunos puntos dejan de ser utilizables.
3. Abre **Time-resolved**. Las moléculas A y B tienen D constantes, pero A se convierte en B. Compara la misma reacción con rampa creciente y decreciente: el D aparente cambia porque composición y b están correlacionados en el tiempo. Una adquisición espacial rápida comparte una ventana temporal y reduce ese sesgo. La permutación mejora la distribución de tiempos, pero no detiene la reacción.

## Los cuatro relojes

**Δ**, en milisegundos, es la separación de los pulsos de difusión. **t_read** pertenece a la lectura. **t_lab**, en segundos, sigue la evolución de la muestra. La ventana de un frame y su cadencia describen el promedio temporal y la separación entre resultados; ventanas solapadas comparten puntos y ruido. La barra de 18 s controla únicamente el progreso visual de la animación.

## Resultados y controles

Las tarjetas muestran referencias conocidas y estimaciones calculadas. «No estimable» identifica falta de señal utilizable o una pendiente incompatible con el ajuste físico. El ajuste monoexponencial utiliza puntos positivos por encima del 1,5 % del máximo y estima también la amplitud inicial. Este umbral es una decisión del ejemplo y no una estimación del ruido.

Los escenarios restablecen los parámetros del ejemplo antes de aplicar sus cambios. Los deslizadores permiten comprobar qué sucede al cambiar un parámetro. El ruido gaussiano tiene una semilla fija para comparar condiciones de forma reproducible.

Puedes pausar, desplazar el progreso visual, cambiar de idioma y abrir pantalla completa. Las teclas Espacio y las flechas controlan la reproducción y las escenas cuando el foco no está en otro control. En móvil puedes plegar la biblioteca de escenas.

## Exportaciones

**CSV** exporta señales sintéticas calculadas, con unidades en las cabeceras. **PNG** guarda el estado actual. **Grabar WebM** registra 18 s de la simulación con los parámetros seleccionados si el navegador dispone de un codificador compatible. La grabación no contiene audio.

Los 32 MP4 y cuatro GIF conservados proceden de la versión 1. Los enlaces SPEN/ultrafast los identifican como esquemas históricos: no representan las nuevas reconstrucciones calculadas. La nueva escena time-resolved usa PNG/WebM y CSV; no se ofrece un enlace a un MP4 inexistente.

## Qué física está implementada

Ultrafast usa un sustituto PGSE ideal con duraciones rectangulares locales δ(z), b(z) calculado en SI, perfil de recepción y relajación a un eco común. Un chirp real requiere integrar el historial local q(z,t), incluyendo su programa de pulsos.

SPEN usa una adquisición EPSI compleja simplificada en los centros de eco, reordenación espacial de las polaridades, corrección de fase conocida, IDFT espacial y DFT espectral. No simula RF chirp finita, evolución química intralóbulo, shear z–ν ni todos los efectos de una secuencia real. Ajusta una atenuación seleccionada; no calcula ILT ni un mapa DOSY objetivo.

Time-resolved usa una reacción de primer orden A→B con resonancias separadas y D constantes, integra la composición durante las ventanas y comparte puntos cuando las ventanas de la serie se solapan. No simula intercambio durante Δ ni una polimerización experimental.

La escena D–T₂ histórica del laboratorio sigue mostrando una señal calculada y un mapa objetivo esquemático, identificado como tal; no ejecuta una ILT. La figura aportada por el investigador se conserva por separado, con su procedencia original.

Las fuentes primarias y lo que sustentan están en `science-v2-references.json`, las referencias de cada escena y `REFERENCES.md`. Los originales, vídeos previos y calibraciones experimentales se conservan.
