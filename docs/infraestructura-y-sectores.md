# Ramas argentinas e infraestructura de IA

Revisión documental: 24 de septiembre de 2026. La prioridad es describir la demanda argentina y documentar infraestructura sin atribuir variaciones agregadas a la IA.

## Tres universos distintos

1. La serie nacional histórica en GWh mantiene sus categorías, fuentes y archivos originales. Alimenta el informe principal, CSV y Excel.
2. La apertura de CAMMESA de agosto de 2026 cubre más de 8.000 empresas GUMA, GUME y GUDI, aproximadamente 90% de la gran demanda mayor según su introducción. Se transcribió y cotejó visualmente la tabla de la página 4; la cobertura está en la página 2. Conserva la unidad publicada, MW, sin convertir a GWh ni suponer que se trata de un pico instantáneo. Los porcentajes son los publicados: los niveles redondeados no permiten reproducirlos exactamente. Componentes, subtotales y total están identificados para evitar dobles sumas.
3. La utilización de capacidad instalada del INDEC mide otro universo productivo. La observación incorporada es julio de 2026 (58,2%, frente a 58,4% en julio de 2025). En el informe de agosto se muestra explícitamente como contexto del mes anterior; no es una observación eléctrica ni una comparación causal.

La apertura CAMMESA muestra +3,4% interanual en el total de su muestra y −1,2% sin Aluar. La rama industrias presenta −0,7%. Esto advierte que el aumento agregado no es uniforme. No identifica cargas de IA y no debe empalmarse con la categoría grandes usuarios de Datos Argentina, que tiene otra delimitación.

## Fuentes y trazabilidad

- [CAMMESA: gran demanda](https://cammesaweb.cammesa.com/gran-demanda/). Original conservado en `data/reference/cammesa-ramas-2026-08.pdf`; captura y SHA-256 en `data/sector_deep_dive.json`. La fecha de captura no reemplaza la fecha de publicación.
- [INDEC: capacidad instalada](https://www.indec.gob.ar/Nivel4/Tema/3/6/15). Publicación del 15/09/2026. El dato de agosto estaba anunciado para el 15/10/2026; no se anticipa ni se imputa.
- `data/infrastructure_registry.json` contiene las fuentes, fechas, actores y limitaciones de cada caso. Son comunicaciones de promotores, organismos y partes litigantes; no todas tienen la misma función probatoria.

## Registro inicial, no censo

Argentina: Stargate / Sur Energy, Clementina XXI, Cirion BUE1, EdgeConneX BUE01 Pilar y ARSAT Benavídez. Referencias estadounidenses: Project Camellia y Colossus 2 / planta de Southaven. El filtro inicial muestra los cinco casos argentinos; el contador general abarca siete casos y el indicador técnico distingue cuatro argentinos con parámetros eléctricos documentados. Los casos extranjeros no se incluyen en la demanda argentina.

El estado está documentado a la fecha de cada fuente, no verificado en tiempo real. Una carta de intención no es obra iniciada, una operación informada no es una lectura de medidor y potencia de cómputo no es potencia eléctrica. Los MW anunciados de suministro tampoco son GWh consumidos. No se convierten usando horas supuestas ni un factor de utilización inventado.

Un valor `null` significa no documentado en las fuentes incorporadas, no cero ni inexistencia universal de datos. Ninguno de los siete casos cuenta aquí con GWh medidos y un período. La proporción atribuible específicamente a IA también queda nula. Clementina admite otras aplicaciones de supercómputo: no es una instalación exclusivamente de IA. Cirion sí menciona cargas de IA en su ampliación; EdgeConneX y ARSAT son contexto de infraestructura digital, sin atribución documentada a IA.

## Historia sectorial incorporada

El explorador usa doce publicaciones de septiembre de 2025 a agosto de 2026. Cada tabla interanual conserva las tasas publicadas; no se reconstruyen a partir de MW enteros redondeados. En diez informes aumenta el total, en cuatro aumenta el subtotal sin Aluar, y en seis crece el total mientras cae ese subtotal. Es un recuento descriptivo de comparaciones internas, no una estimación causal ni una tasa de crecimiento del conjunto de doce meses.

La cobertura declarada cambia de 98% en las once primeras ediciones a 90% en agosto. No se verificó si hubo cambio efectivo de muestra o de descripción. Por ello no se dibuja una línea que empalme los niveles de diferentes ediciones. El gráfico histórico compara un mismo mes del calendario entre años, siempre usando la historia contenida en una sola edición.

Se incorporaron 164 registros de período, cada uno con cuatro ramas (656 valores). Septiembre y octubre cubren 2018–2025; noviembre y diciembre 2012–2025; enero a agosto 2012–2026. Quedan doce huecos explícitos en septiembre/octubre de 2012–2017. No se rellenan ni se presentan como 164 meses consecutivos.

La revisión visual detectó erratas de encabezado: octubre de 2025 dice AGO en el título de la comparación, aunque sus columnas y portada corresponden a octubre. En las tablas históricas de noviembre/diciembre de 2025 y enero de 2026 el título empieza en 2018, pero las columnas empiezan en 2012. Se conservaron las fechas de las columnas, registrando las discrepancias en el manifiesto y en la interfaz.

El informe INDEC de septiembre contiene 19 meses (enero de 2025 a julio de 2026) de doce actividades y del nivel general: 247 valores. Son datos provisorios. Las diferencias se expresan en puntos porcentuales, no crecimiento de producción. Alimentos excluye actividad vitivinícola e ingenios azucareros; químicos excluye industria farmacéutica. Los bloques no se empalman uno a uno con las ramas CAMMESA. Las comparaciones cuyo año anterior no está incorporado quedan sin dato.

## Magnitudes técnicas de infraestructura

- Stargate: hasta 500 MW y hasta USD 25.000 millones, según anuncio oficial del 10/10/2025. No son capacidad instalada verificada ni inversión ejecutada.
- Clementina: 233 kW como parámetro eléctrico declarado en 2023, 296 GPU y 15,3 petaFLOPS. kW no es kWh; no se supone utilización constante. Las pruebas de puesta en marcha de 2023 y la operación plena desde 2025 informada en 2026 son hitos diferentes.
- Cirion: ampliación en ejecución anunciada en agosto de 2025, superior a 2 MW y aproximadamente 160 racks adicionales. No se la confunde con la capacidad total del centro ni se afirma su terminación.
- EdgeConneX: ficha técnica con 3,5 MW N+1 y capacidad potencial del emplazamiento de 10,5 MW. No se suman. El PDF no tiene fecha editorial acreditada: la ruta URL no se usa para inventarla; se registra la consulta y se archivan los bytes.
- ARSAT: 4.500 m² y cuatro salas de 365 m² documentados por el operador. Superficie y certificación no equivalen a potencia o energía consumida.

Cada cifra tiene referencia individual en `technical_facts`. Las fuentes sin fecha editorial requieren fecha de consulta. Los parámetros de cómputo, superficie, capacidad eléctrica, ampliación y capacidad potencial usan categorías separadas.

## Reproducción y archivo

`data/reference/branch-source-manifest.json` conserva enlaces, captura, fecha editorial, páginas, unidades, cobertura, notas y hashes. Los doce PDF CAMMESA están archivados sin modificar; también el INDEC y la ficha EdgeConneX. La descarga inicial usa `scripts/fetch_branch_history.py`; revisar manualmente su salida antes de modificar el manifiesto curado.

Con Poppler disponible, `python3 scripts/extract_sector_history.py` reproduce `data/sector_history.json` sin red. Valida hashes, rótulos y cantidad de columnas; los subtotales de la comparación se transcribieron y cotejaron visualmente. Después ejecutar `python3 scripts/build_site.py` y `python3 scripts/verify_release.py`. La publicación no requiere Poppler: verifica el JSON versionado y las huellas de los originales.

Los eventos judiciales distinguen quién afirma qué y cuándo. Demanda, intervención solicitada y fallo son etapas diferentes. No se verificó sentencia definitiva en los casos incorporados ni retraso cuantificado atribuible a ellos. Se muestran como contexto regulatorio y de plazos, nunca como medición eléctrica. No incorporar un litigio local tampoco certifica su ausencia.

## Actualizar sin contaminar el diagnóstico

1. Obtener la publicación original y registrar período, publicación cuando esté acreditada, captura y cobertura. Archivar el PDF sin modificar y calcular su SHA-256.
2. Cotejar visualmente tabla y unidad. Revisar cambios de muestra antes de comparar. No trasladar una observación a meses sin datos.
3. Actualizar los JSON de fuente. Para infraestructura exigir fuente de estado; si hay potencia, su fuente específica; si hay energía medida, fuente y período. Registrar litigios aparte con atribución de parte.
4. Ejecutar `python3 scripts/build_site.py`, `python3 scripts/verify_release.py` y la prueba de navegador `scripts/check_research.cjs` con Playwright disponible. Revisar informe, filtro, descarga y móvil antes de publicar.
5. Revisar el diff y publicar. No modificar el pronóstico prospectivo ya emitido.

Los nuevos módulos alimentan web y TXT, con JSON independientes descargables. CSV y XLSX conservan la serie nacional y no incluyen esta nueva tabla de MW. La actualización documental es manual: publicar automáticamente el sitio no descarga ni verifica nuevas fuentes.

## Interfaz y verificación

Se mantienen los colores, tarjetas y puntos de adaptación del sitio existente, siguiendo la guía `frontend-designer`. Los filtros usan `select` nativo y el contexto documental usa `details`: conservan navegación por teclado y foco del navegador sin introducir controles personalizados o dependencias nuevas. Se descartaron un framework adicional y un mapa de instalaciones: el primero añade migración sin necesidad; el segundo sugeriría precisión geográfica que no acreditan todas las fuentes.

Las pruebas cubren 390 y 1440 píxeles, meses sin cobertura, las 48 combinaciones de mes/rama, cambio de país por teclado, descargas JSON y distinción entre alegaciones y fallos. Se revisaron capturas de pantalla. Se conserva el modo de movimiento reducido existente y no se agregan animaciones. Registro y explorador necesitan JavaScript; sin él permanecen disponibles los enlaces al JSON. Tablas y gráfico histórico permiten desplazamiento horizontal en pantallas estrechas, evitando achicar las etiquetas hasta hacerlas ilegibles. Las doce filas mensuales y las doce actividades se muestran sin recorte vertical. Estas comprobaciones en Chromium no equivalen a una auditoría completa de accesibilidad o compatibilidad en todos los navegadores.
