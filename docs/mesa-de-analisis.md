# Mesa de análisis: decisiones y evidencia

La web conserva sus componentes y controles nativos, sin nuevas bibliotecas ni servicios externos. El resumen mensual selecciona hasta tres señales de prioridad por valor absoluto del cambio en MW; no cambia la regla congelada ni produce una clasificación de riesgo económico. Intensidad y calidad se muestran por separado. No existe una probabilidad de confianza inventada.

## Calidad y expedientes

El panel muestra períodos, capturas, fechas de publicación verificadas o explícitamente desconocidas, cobertura y SHA-256. Describe los archivos archivados: no garantiza que no exista una publicación posterior en internet. La fecha de construcción no reemplaza la fecha de captura. Próxima comprobación significa tarea propuesta, no fecha oficial ni automatización.

El expediente de metales conserva hipótesis, apoyo, contraevidencia/límites, dato decisivo y acción. Sus cifras se generan desde `divergencias-metales.json`, no se escriben de nuevo en HTML. Las hipótesis cualitativas están en `data/metals_casebook.json`. Aluar mantiene su balance separado; no se extrapolan conclusiones entre empresas o categorías. No se enviaron solicitudes de información.

## Preparación prospectiva de solo lectura

Desde la raíz del repositorio:

```sh
python3 -m scripts.analysis_workbench
python3 -m scripts.sector_registry status
```

El primer comando identifica el primer mes pendiente y las comprobaciones necesarias. No declara que haya datos listos ni emite señales. Consultar [registro-sectorial.md](registro-sectorial.md) para emisión, verificación pública y resultados. La nueva fecha posible de captura corresponde al cierre calendario, no a una promesa de publicación de CAMMESA. No hay tareas programadas, descargas periódicas ni notificaciones. Primero capturar, revisar las versiones y probar; después publicar. Si falta una publicación, documentar el vacío y no sustituir meses.

## Asistencia documental con IA: preparada, no conectada

```sh
python3 -m scripts.document_review prepare
python3 -m scripts.document_review evaluate RUTA_RESPUESTA.json
python3 -m scripts.document_review compare RUTA_ANTES.json RUTA_DESPUES.json
```

`prepare` produce un paquete y un prompt en inglés para leer siete campos de la página 17, cuadro 2.11 del informe INDEC de abril de 2026. Adjuntar el PDF original indicado en el paquete; su huella se verifica localmente. El paquete no incluye las respuestas esperadas. El material del documento se trata como evidencia, nunca como instrucciones de ejecución. No se solicitan credenciales ni se envían archivos a proveedores desde el proyecto.

La respuesta esperada es un objeto JSON con `items`: cada elemento conserva `id`, `source_sha256`, `page`, `table`, `period`, `unit` y añade `value` numérico o nulo. No mezclar variaciones interanuales (`percent`) e incidencias (`pp`). No reemplazar la edición original por la historia revisada.

`evaluate` coteja cifras y metadatos contra referencias transcritas y revisadas en la investigación anterior. Reporta campos correctos, incorrectos, omitidos, abstenciones e identificadores adicionales. `compare` identifica diferencias entre propuestas; no determina que sean revisiones oficiales. Ninguno modifica datos, incorpora respuestas o aprueba su publicación. Siempre se necesita revisión humana del original.

La prueba tiene siete campos de un único documento ya conocido: sirve para depurar extracción, no como evaluación ciega ni evidencia de precisión general. Los tests sintéticos verifican el programa y no cuentan como ejecuciones reales de IA. Actualmente no hay modelo conectado ni resultados reales: exactitud nula significa no medida. Antes de usarlo en producción, separar documentos de desarrollo y evaluación, incluir ausencias, unidades y revisiones, registrar proveedor/modelo/fecha/prompt y medir errores sin corregir respuestas después de ver la referencia.

## Comprobaciones antes de publicar

1. `python3 scripts/build_site.py`: genera texto, datos y descargas a partir de las mismas fuentes.
2. `python3 scripts/verify_release.py`: pruebas, fuentes y resultados congelados.
3. `node scripts/check_analysis_workbench.cjs` con el entorno Playwright ya configurado: mes histórico, ausencias, descargas, móvil, teclado y errores de navegador.

El Excel, CSV nacional y protocolo prospectivo no se modifican con esta extensión. Las tablas móviles conservan lectura y navegación sin animaciones nuevas; el estado no depende solo del color.
