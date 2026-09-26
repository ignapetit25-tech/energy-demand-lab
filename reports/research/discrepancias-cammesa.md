# Discrepancias de CAMMESA: agosto de 2026

Revisión: 26/09/2026. Unidad: MW medios. Se comparan los mismos 31 días de agosto. Los PDF se revisaron en su página 7; las cifras de la base son cálculos propios sobre datos diarios, no transacciones definitivas.

## Resultado

El total pasa de 2.293,1 a 2.295,2 MW entre PDF: +2,1 MW de cambio documental del mismo mes. La base diaria da 2.292,0401 MW. La distancia del PDF del 24/09 frente a la base es 3,1599 MW, aproximadamente 0,138% de la base. No se confirma cuál valor es definitivo ni la causa exacta de la divergencia.

| Actividad o subtotal | PDF 17/09 | PDF 24/09 | Base diaria | PDF 24/09 menos base |
| --- | ---: | ---: | ---: | ---: |
| ALIMENTACIÓN, COMERCIOS Y SERVICIOS | 462,0 | 462,8 | 460,7662 | 2,0338 |
| CARGAS Y PUERTOS | 9,6 | 9,6 | 9,5956 | 0,0044 |
| COMERCIO Y SERVICIOS (PRINCIPALMENTE SUPERMERCADOS Y OTROS CENTROS COMERCIALES) | 50,9 | 50,9 | 50,9360 | -0,0360 |
| INDUSTRIA DE LA ALIMENTACIÓN Y ARTÍCULOS DE CONSUMO MASIVO | 331,9 | 332,7 | 330,6916 | 2,0084 |
| SECTOR DE SERVICIOS PÚBLICOS Y TRANSPORTE (AGUA Y TRANSPORTE EN GBA) | 69,5 | 69,5 | 69,5430 | -0,0430 |
| ALUAR ** | 547,2 | 547,2 | 547,1720 | 0,0280 |
| INDUSTRIAS | 1.093,1 | 1.093,8 | 1.093,3003 | 0,4997 |
| INDUSTRIA AUTOMOTRIZ | 45,1 | 45,1 | 44,8658 | 0,2342 |
| INDUSTRIA DE DERIVADOS DE PETRÓLEO | 158,6 | 158,6 | 158,5798 | 0,0202 |
| INDUSTRIA DE LA CONSTRUCCIÓN (ELABORACIÓN DE CEMENTO Y CANTERAS) | 90,2 | 90,2 | 90,2110 | -0,0110 |
| INDUSTRIA DE LA MADERA Y EL PAPEL | 105,3 | 105,4 | 105,2691 | 0,1309 |
| INDUSTRIA DE PRODUCTOS METÁLICOS NO AUTOMOTORES | 36,4 | 36,4 | 36,3343 | 0,0657 |
| GRAN SIDERURGIA | 286,7 | 286,7 | 286,6665 | 0,0335 |
| INDUSTRIA TEXTIL | 40,6 | 40,6 | 40,6327 | -0,0327 |
| INDUSTRIAS QUÍMICAS, DEL CAUCHO, PLÁSTICO Y OTROS MATERIALES MINERALES NO METÁLICOS | 330,3 | 330,9 | 330,7413 | 0,1587 |
| PETROLEOS Y MINERALES | 190,8 | 191,4 | 190,8016 | 0,5984 |
| EXTRACCIÓN DE MINERALES | 36,2 | 36,2 | 36,1609 | 0,0391 |
| EXTRACCIÓN DE PETRÓLEO | 154,6 | 155,2 | 154,6407 | 0,5593 |
| TOTAL | 2.293,1 | 2.295,2 | 2.292,0401 | 3,1599 |
| TOTAL SIN ALUAR | 1.745,9 | 1.748,0 | 1.744,8681 | 3,1319 |

No sumar filas de actividades junto con sus subtotales. Las diferencias están calculadas contra valores redondeados del PDF; no implican esa precisión en la fuente.

## Explicaciones contrastadas

- **Error de suma o distinta hoja diaria:** se cotejaron las tres hojas diarias por fecha y rama, con 1.727 fechas cada una. La diferencia máxima es inferior a 0,000001 MW; el total de agosto coincide. La conciliación interna no prueba exactitud de las mediciones originales.
- **Días hábiles:** los 20 días marcados hábiles dan 2.363,2214 MW; los 11 no hábiles, 2.162,6197 MW. Ninguno reproduce 2.295,2 MW. El resumen superior del XLSX está configurado para hábiles, pero esta convención no explica la brecha de la tabla mensual del PDF, que declara 31 días.
- **Redondeo:** un total presentado con un decimal admite ±0,05 MW si comparte la misma base. Incluso sumar 15 componentes redondeados y redondear el total daría una cota conservadora de 0,8 MW. La diferencia de 3,1599 MW supera ambas cotas. No basta el redondeo decimal ordinario como única explicación.
- **Revisión de la fuente:** hay cambios verificables entre PDF de igual período. Alimentos sube 0,8 MW, químicas 0,6 MW, extracción de petróleo 0,6 MW y madera/papel 0,1 MW entre las dos ediciones; explican los 2,1 MW publicados. Esto acredita cambios entre versiones, no su causa operativa.
- **Foco de la diferencia PDF-base:** alimentos y extracción de petróleo concentran la mayor parte del saldo. Aluar está dentro del margen de redondeo de un decimal. No hay evidencia en esta comparación de que Aluar origine la discrepancia total.

## Lo que falta para cerrarla

CAMMESA explica que los datos operativos son provisorios y se ajustan antes de consolidarse con el DTE. Eso hace plausible una diferencia de revisión o de corte, pero no identifica qué registros cambiaron aquí. También quedan abiertas diferencias de cobertura, actualización de tablas o de medición. Se necesita el archivo que alimentó cada PDF, su fecha/hora de corte y una conciliación con el DTE. No se atribuye responsabilidad ni se corrigen originales sin esa evidencia.

Las columnas de septiembre de estos PDF cubren 16 y 23 días: no se interpretan sus diferencias como revisiones del mismo período. La afirmación de este informe se restringe a agosto.

## Fuentes y reproducción

- [Publicación y metodología oficial](https://cammesaweb.cammesa.com/2026/09/25/covid-19-comportamiento-de-la-demanda-de-energia-electrica-en-el-mem/), consultada el 26/09/2026.
- [Base diaria oficial](https://cammesaweb.cammesa.com/download/base-de-datos-2/?wpdmdl=39428), captura archivada del 26/09/2026. Este enlace puede cambiar de versión.
- [PDF 17/09 archivado](../../data/reference/cammesa-gumas-2026-09-17.pdf), página 7.
- [PDF 24/09 archivado](../../data/reference/cammesa-gumas-2026-09-24.pdf), página 7.
- [Resultados y hashes](discrepancias-cammesa.json). Reproducir con `python3 scripts/analyze_sector_followups.py` desde el repositorio; requiere `pdftotext`.

No se alteraron el Excel descargable, las fuentes publicadas ni los pronósticos congelados. La [solicitud preparada](../../docs/solicitudes-datos-aluar-cammesa.md) contiene las preguntas pendientes.
