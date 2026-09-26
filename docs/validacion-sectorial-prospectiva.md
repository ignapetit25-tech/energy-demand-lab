# Validación futura de señales sectoriales

Versión 1. Diseñada el 26/09/2026 y fijada mediante el commit que incorpora este documento. El hash de la regla y el registro vacío se conservan en `prospective/sector-alerts-protocol.json`. No hay resultados prospectivos todavía ni un monitor automático. Este protocolo es independiente del pronóstico nacional de octubre: no lo cambia.

## Pregunta y alcance

¿La dirección del cambio eléctrico en meses señalados como prioridad aporta información sobre la dirección del IPI del mismo mes, todavía no publicado, frente a repetir la dirección del último IPI conocido?

Es un ejercicio de anticipación de una publicación de producción del mismo período, no un pronóstico de consumo futuro ni una prueba causal. Las categorías INDEC y CAMMESA no contienen necesariamente los mismos establecimientos. La referencia de producción es imperfecta y no determina si una alerta operativa era verdadera o falsa.

Se conservan los tres mapeos existentes: cemento (CLaNAE 26941) con cemento y canteras; productos de metal (28) con productos metálicos no automotores; textiles (17) con industria textil. No se incluyen Aluar ni otras once actividades en la métrica primaria por falta de un mapeo validado. Se publicarán las 14 señales como contexto, con su estado de cobertura.

## Períodos y emisión

- Ventana fija: octubre de 2026 a septiembre de 2027, doce meses completos. Toda historia hasta septiembre de 2026 queda fuera de la evaluación. No desplazar el inicio o ampliar la ventana según el resultado.
- Para cada mes, usar la primera captura completa de CAMMESA registrada por el proyecto, después del cierre mensual. Debe contener todos los días, los comparables del año anterior y los meses requeridos para persistencia.
- Congelar la señal en un commit público antes de la publicación del IPI de ese mes. Registrar hora UTC real de descarga, de cálculo y de publicación del commit, URL, bytes originales, SHA-256, código y parámetros. No retrofechar. Si la fuente de electricidad llega después del IPI, el mes no es elegible para la métrica primaria.
- Conservar simultáneamente la última publicación IPI conocida en ese momento (período, tasa, fecha de publicación, captura y hash). No completar ese dato después de conocer el objetivo. Si falta, no hay comparación pareada elegible.
- Si no se puede comprobar que la señal pública precede al IPI, marcar `emision_no_verificable`. Los meses tardíos, incompletos o ausentes se muestran con su motivo; nunca se cuentan como cero, acierto o ausencia de alerta.

No se promete que la primera captura registrada sea la primera publicación oficial de cada fuente. Si una publicación solo tiene fecha, exigir que el commit de emisión sea de un día UTC anterior; no asumir un orden intradiario.

## Regla fija y comparador

Regla `proposal-1`: observación cuando el cambio absoluto cumple simultáneamente 10% y 5 MW; prioridad cuando cumple 20% y 10 MW, o al cumplir observación durante tres meses consecutivos en la misma dirección. Se calculan tasas sobre meses completos, base positiva y datos no ausentes. Se conserva la implementación del clasificador y su hash.

No se selecciona ninguno de los 31 escenarios explorados. Cambiar umbrales o mapeos requiere una versión nueva y una cohorte futura distinta; los registros de esta cohorte permanecen intactos.

Predicción primaria: signo del cambio eléctrico en los registros con prioridad. Comparador: signo de la última tasa interanual IPI publicada y archivada antes de emitir la señal. El objetivo es la tasa interanual de la serie original del IPI para el mismo mes y código. Signo positivo si supera +0,5%, negativo si es inferior a −0,5%, y sin cambio material entre ambos límites, incluidos. El margen evita interpretar un redondeo próximo a cero como cambio de dirección; se fija ahora, no se ajusta al observar resultados. Se aplica la misma función a predictor, comparador y objetivo.

## Registro del resultado y revisiones

Registrar la primera observación IPI capturada después de la emisión con período, código, tasa, fecha de publicación y captura, URL, archivo y hash. Guardar revisiones posteriores en registros separados, sin reemplazar el resultado primario. Ausencias, discontinuidades o modificaciones de códigos se documentan y excluyen hasta resolver la correspondencia sin mirar qué opción mejora la métrica.

Campos obligatorios por señal: identificador `mes:actividad`, mes, actividad, MW actual/anterior, cambio MW y porcentaje, estado, dirección, persistencia, versión y hash de regla/código, fuentes eléctricas y sus hashes, timestamps, commit público, referencia IPI conocida y su hash. Por resultado: referencia a esa señal, fecha de publicación y captura, índice/tasa/código, hash y elegibilidad con motivo. Los estados pendientes quedan nulos en las métricas.

## Métricas y regla de lectura

La unidad es actividad-mes. En los mismos registros prioritarios y elegibles calcular: exactitud de dirección de la señal, exactitud del comparador y diferencia pareada en puntos porcentuales. Publicar numeradores y denominadores, desglose por categoría, cobertura de los 36 pares posibles, número de alertas y motivos de exclusión. Reportar también todos los meses elegibles como análisis secundario, sin reemplazar la métrica primaria.

Al cerrar la ventana, se contará como evidencia favorable limitada solo si hay al menos 12 registros prioritarios elegibles, distribuidos en al menos 6 meses, y la mejora primaria es al menos 10 puntos porcentuales. Además, el límite inferior del intervalo percentil del 95% de la diferencia debe ser mayor que cero. El intervalo se calcula con 10.000 remuestreos de meses completos, semilla 20260926, manteniendo juntas sus tres actividades; se descartan y contabilizan remuestreos sin registros prioritarios. Si más del 5% queda sin registros, no se emite una conclusión favorable.

Doce meses y tres categorías ofrecen poca información independiente. El bootstrap no elimina autocorrelación entre meses ni resuelve el mapeo de poblaciones; no se presenta como una prueba definitiva o calibración de falsas alarmas. Si no se cumplen todos los requisitos, la conclusión es insuficiente o no favorable, según los resultados. No prolongar el estudio para buscar significación.

Controles descriptivos secundarios: tasa de coincidencia por sector y semestre; persistencia de señales; cambios entre primera captura y revisión; diferencia de días hábiles, cortes, clima y cambios de cobertura cuando estén documentados. No usar estos controles para cambiar retrospectivamente la muestra primaria ni corregir resultados sin un protocolo nuevo.

## Publicación y operación

Publicar el registro de señales antes de los resultados y el informe final cualquiera sea el desenlace. Una actualización mensual informa datos nuevos o faltantes, no declara una victoria anticipada. El responsable es Energy Demand Evidence Lab; la captura y revisión siguen siendo manuales. Este documento diseña la validación: todavía no implementa un sistema de ingestión ni activa notificaciones.
