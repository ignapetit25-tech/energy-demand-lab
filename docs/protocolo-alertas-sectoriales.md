# Protocolo propuesto de alertas sectoriales

Versión `proposal-1`, definida el 26/09/2026 después de conocer los datos. Propuesta de revisión editorial, no sistema desplegado. No crea tareas programadas ni envía mensajes. La [aplicación ilustrativa a agosto](../reports/research/alertas-sectoriales.md) no es una evaluación fuera de muestra.

## Qué decisión ayuda a tomar

Decidir qué actividades merecen investigación adicional en el informe mensual. «Prioridad» significa revisar antes; no significa emergencia, anomalía estadística, recesión o expansión confirmada. Una subida no es necesariamente buena ni una caída necesariamente mala. No permite atribuir cambios a la IA.

## Métrica y cobertura

Para cada una de las 14 actividades GUMAs + AUTO, comparar el promedio de MW medios diarios del mes completo con el mismo mes del año anterior:

`variación (%) = 100 × (MW_mes / MW_mismo_mes_año_anterior − 1)`

`cambio (MW) = MW_mes − MW_mismo_mes_año_anterior`

El porcentaje considera la escala relativa; los MW permiten ordenar por magnitud. Se conserva además la contribución de cada actividad al cambio de su rama: `100 × cambio_MW_actividad / MW_rama_año_anterior`, en puntos porcentuales. No es porcentaje del aumento neto. Las contribuciones suman la tasa de la rama, siempre que las categorías sean exhaustivas y comparables.

Aluar se evalúa aparte como toma neta de red y no se cuenta entre las 14 actividades. No sumar actividades y subtotales. La cobertura no representa a toda la industria argentina ni asegura un panel fijo.

## Reglas iniciales

| Estado | Condición, en valor absoluto salvo persistencia | Acción |
| --- | --- | --- |
| No evaluable | Mes parcial, comparación ausente, valor inválido o base del año previo igual a cero | Mostrar el faltante; no asignar un estado tranquilizador |
| Prioridad | Al menos 20% **y** 10 MW; **o** tres meses consecutivos con al menos 10% **y** 5 MW, todos en igual dirección | Revisar cobertura, fuentes y contexto sectorial antes de interpretar |
| Observar | Al menos 10% **y** 5 MW, sin cumplir prioridad | Mantener en revisión para la próxima edición |
| Sin umbral | No cumple las condiciones anteriores | Conservar el dato; no equivale a normalidad o ausencia de riesgos |

Los límites son inclusivos. Un cero actual frente a una base positiva es una caída de 100%, no un faltante. Una base cero impide calcular la tasa. No calcular persistencia a través de meses faltantes o parciales. Orden: primero prioridad, después observar; dentro de cada grupo, mayor cambio absoluto en MW. Conservar el resto de las actividades visible, porque los umbrales pueden omitir movimientos relevantes.

Los valores 10%/5 MW y 20%/10 MW son elecciones iniciales del proyecto, **no criterios oficiales ni umbrales calibrados estadísticamente**. Se eligieron para combinar magnitud relativa y absoluta con una regla simple de persistencia. No se ajustarán para conseguir un número deseado de alertas. La regla puede dejar sin señal a una actividad pequeña con una variación porcentual elevada: debe explicitarse y revisarse como limitación, no ocultarse.

## Calidad de datos separada de la señal

Antes de publicar una interpretación:

1. Verificar fechas consecutivas, duplicados, unidad, conciliación de categorías y meses completos en ambas ventanas. Un fallo bloquea el cálculo afectado.
2. Conservar archivo original, hash, fecha de captura, fecha declarada del documento y versión de reglas. Nunca sustituir retrospectivamente una señal sin dejar historial de revisión.
3. Consultar altas, bajas y reclasificaciones. Si se conocen cambios de perímetro, marcar «comparación afectada por cobertura» y no confirmar una señal económica sin un panel comparable. Si faltan datos de establecimientos, mostrar «cobertura no verificada», no asumir estabilidad.
4. Si PDF y XLSX discrepan más que su redondeo, abrir revisión documental. Mantener valores separados. La señal calculada puede presentarse como exploratoria, pero no como conciliada o definitiva.
5. Diferencia de al menos dos días hábiles entre meses comparados: marcar «revisar calendario». Esta marca no corrige los MW ni demuestra que el calendario cause el cambio. Siempre considerar feriados móviles, paradas de planta y clima.

La variación interanual reduce la confusión por estacionalidad anual, pero no constituye una desestacionalización ni un ajuste meteorológico. Tres tasas interanuales consecutivas tampoco son tres observaciones independientes. La [guía NIST de estabilidad](https://www.itl.nist.gov/div898/handbook/ppc/section4/ppc45.htm) y su [referencia sobre autocorrelación](https://www.nist.gov/publications/statistical-process-monitoring-autocorrelated-data) motivan no presentar estos límites editoriales como un test estadístico.

## Investigación que sigue a cada señal

| Grupo | Pregunta principal | Evidencia que se buscaría |
| --- | --- | --- |
| Alimentos y comercio | ¿Cambió la demanda por actividad, temperatura o cobertura? | Cantidad de usuarios, composición regional, producción o ventas físicas comparables |
| Construcción, metales y textiles | ¿La baja persiste y coincide con menor producción física o con paradas? | Indicadores oficiales de actividad con rezago documentado, paradas publicadas y cobertura |
| Minería y petróleo | ¿Entraron proyectos o cambiaron operaciones de grandes usuarios? | Puesta en operación verificable, producción física y altas agregadas de usuarios |
| Aluar | ¿Cambió la producción o la fuente de abastecimiento de energía? | Balance de importación/exportación, consumo bruto y autogeneración bajo un mismo perímetro |

Los indicadores externos deben corresponder a actividades comparables. No equiparar automáticamente una categoría de usuarios eléctricos con una clasificación industrial nacional. Su coincidencia es contexto, no identificación causal.

## Cómo validar antes de activar

Si el usuario decide implementarlo, congelar esta versión y registrar las siguientes 12 publicaciones mensuales completas, comenzando con septiembre de 2026 cuando esté disponible. Para cada edición registrar fecha de disponibilidad, valores entonces conocidos, estado, dirección, motivo, cambios de cobertura y posterior revisión. No usar una captura histórica actual como si fuera la información disponible entonces.

Evaluar carga de revisión (número de señales y tiempo empleado), persistencia y cuántas señales cambian por correcciones de datos. Registrar explicaciones documentadas y señales sin explicación. No llamar «falsa alarma» a una señal solo porque no se encontró una explicación: falta una verdad de referencia económica para estimar sensibilidad o precisión.

Hasta esa evaluación, las señales serán descriptivas. Cualquier cambio de umbral crea una nueva versión y se explica; no mejora retrospectivamente una evaluación anterior. Si luego se desean notificaciones, definir destinatario y frecuencia por separado. Este documento no las activa.

## Reproducción

Parámetros en `data/sector_alert_rules.json`; cálculo en `scripts/analyze_sector_followups.py`; pruebas de límites, faltantes y persistencia en `tests/test_sector_followups.py`. Salidas en `reports/research/`. No se modifican el Excel, los modelos, el CSV nacional ni el pronóstico congelado.
