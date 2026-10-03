# Verificación y reproducibilidad

[Inicio](../../README_ES.md) · [English](../en/verification.md)

Desde la raíz del repositorio, con Python 3:

```console
python python/run_tests.py
python tools/audit_public_repo.py
```

El primer comando ejecuta seis grupos de pruebas sintéticas/offline. Las llamadas TopCmds son simuladas, incluida la ruta de adquisición. No importa la API del fabricante, abre TopSpin, conecta al instrumento ni adquiere datos. El segundo comprueba hashes de distribución, enlaces Markdown locales, las presentaciones completas de 45 diapositivas/45 notas con 20 ocultas y siete vídeos incrustados, configuraciones de ejemplo bloqueadas y comprobaciones textuales de privacidad/secretos.

[verification.json](../verification.json) registra 63 pruebas CPython y 16 de Jython aislado durante la preparación, además de comprobaciones estáticas del instalador y reconstrucción desde fuentes. Son QA de software, no cualificación instrumental ni validación química/física. En esta tarea no se verificó visualmente la GUI nativa ni se adquirió con TopSpin 3.6.4.

Para reconstruir los scripts autocontenidos desde las fuentes públicas:

```console
python python/build_bundles.py
python python/run_tests.py
```

El motor generado y los bundles v2/v3 deben ser idénticos byte a byte si no cambian las fuentes incluidas ni el modelo de secuencia documentado. [build_sources_sha256.json](../../python/build_sources_sha256.json) registra entradas y salidas. No se requiere el espacio de trabajo privado ni código propietario del fabricante.

Únicamente un mantenedor revisando un cambio deliberado de distribución debe regenerar el manifiesto con `python tools/audit_public_repo.py --write-manifest`. No regenere hashes para ocultar diferencias sin explicar. No hay workflows de GitHub Actions y estos comandos no los activan.

La procedencia de las presentaciones conserva hashes del archivo original y sus miembros y enumera las notas modificadas. Se mantienen los bytes de diapositivas, gráficos, libros incrustados, imágenes y vídeos. No cambian páginas PDF ni etiquetas científicas originales. Los hashes acreditan integridad de distribución, no una calibración correcta ni validación de una nueva secuencia ultrafast.
