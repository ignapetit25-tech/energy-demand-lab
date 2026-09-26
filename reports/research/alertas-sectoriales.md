# Propuesta de alertas: aplicación a agosto de 2026

Fecha de diseño: 26/09/2026. Estado: propuesta exploratoria, no desplegada. No se enviaron alertas ni se programó un monitor. [Reglas y procedimiento](../../docs/protocolo-alertas-sectoriales.md).

Cada tasa compara MW medios del mes completo con el mismo mes del año previo. Los umbrales son decisiones editoriales: no significancia estadística ni detección confirmada de crisis o expansión.

| Actividad | Interanual | Cambio MW | Revisión propuesta | Persistencia de 3 meses |
| --- | ---: | ---: | --- | --- |
| Alimentación y artículos de consumo masivo | 15,9% | 45,3 | prioridad | Sí |
| Construcción: elaboración de cemento y canteras | -26,4% | -32,4 | prioridad | No |
| Productos metálicos no automotores | -23,7% | -11,3 | prioridad | No |
| Extracción de minerales | 42,8% | 10,8 | prioridad | Sí |
| Industria textil | -18,8% | -9,4 | prioridad | Sí |
| Comercio y servicios: principalmente supermercados y centros comerciales | 12,1% | 5,5 | prioridad | Sí |
| Derivados de petróleo | 9,5% | 13,8 | sin_umbral | No |
| Químicas, caucho, plástico y otros minerales no metálicos | 4,1% | 12,9 | sin_umbral | No |
| Gran siderurgia | 4,3% | 11,9 | sin_umbral | No |
| Extracción de petróleo | 6,6% | 9,6 | sin_umbral | No |
| Industria automotriz | 10,2% | 4,2 | sin_umbral | No |
| Servicios públicos y transporte: agua y transporte en GBA | -4,5% | -3,2 | sin_umbral | No |
| Madera y papel | 0,5% | 0,6 | sin_umbral | No |
| Cargas y puertos | 3,3% | 0,3 | sin_umbral | No |

`prioridad`: cambio de al menos 20% y 10 MW en valor absoluto, o tres meses consecutivos cumpliendo 10% y 5 MW en la misma dirección. `observar`: al menos 10% y 5 MW, sin prioridad. `sin_umbral`: no activa esas reglas, no equivale a normalidad. La persistencia de tres meses incluye junio, julio y agosto, cada uno frente a su mismo mes de 2025.

Aluar se informa aparte: 45,6%, 171,5 MW, estado `prioridad`. Es demanda neta de red: no atribuir el cambio a producción, autogeneración ni IA sin datos adicionales. No integra el conteo de las 14 actividades.

Las categorías son usuarios GUMAs + AUTO, no un panel fijo ni toda la industria. Hay que revisar cambios de establecimientos, calendario, clima y paradas antes de interpretar cualquier señal. Septiembre de 2026 está excluido por ser parcial. Las comparaciones de agosto tienen una diferencia de 0 días hábiles según la propia base; no se realizó ajuste por calendario.

La fuente sigue siendo provisoria y presenta una [discrepancia documental pendiente](discrepancias-cammesa.md). Las señales sirven para ordenar investigación, no para emitir una conclusión sectorial confirmada. El cruce con producción física debe respetar la cobertura de cada fuente.

Esta ilustración usa datos ya observados y una única captura histórica revisada. No acredita rendimiento prospectivo. [Resultados reproducibles, reglas y huella de fuente](alertas-sectoriales.json).
