# Alertas, producción y sensibilidad de umbrales

Revisión: 26/09/2026. Las alertas se integran como módulo descriptivo del tablero, sin notificaciones ni actualización automática. La regla base sigue siendo `proposal-1`; los umbrales no se optimizaron para conseguir un resultado deseado.

## Producción: el contraste válido llega a julio

El [IPI manufacturero de julio](https://www.indec.gob.ar/uploads/informesdeprensa/ipi_manufacturero_09_26B810401E77.pdf) fue publicado el 08/09/2026 y consultado el 26/09. Se comparan tasas interanuales de julio en ambas fuentes, no electricidad de agosto con producción de julio.

| Categoría eléctrica | Electricidad julio interanual | Indicador INDEC | IPI julio interanual | Lectura |
| --- | ---: | --- | ---: | --- |
| Construcción: elaboración de cemento y canteras | -16,0% | IPI Cemento | -6,9% | Ambas caen |
| Productos metálicos no automotores | -43,3% | IPI Productos de metal | -8,4% | Ambas caen |
| Industria textil | -17,5% | IPI Productos textiles | -13,0% | Ambas caen |

Cemento es un proxy parcial de la categoría eléctrica de cemento y canteras. Metales no equivale a industrias metálicas básicas. Textiles no incluye aquí prendas de vestir. No hay un panel común validado entre INDEC y CAMMESA. La coincidencia de signo no mide causalidad, intensidad energética ni elasticidades. No promediar índices de volumen con MW.

El IPI combina variables de volumen y otras aproximaciones, incluidas ventas deflactadas; no representa toneladas medidas para todas las ramas (metodología, página 26). Los cuadros usados son 2.3 (página 9), 2.9 (página 15) y 2.11 (página 17). Los valores son provisorios.

La [página oficial](https://www.indec.gob.ar/Nivel4/Tema/3/6/14) anuncia el 07/10/2026 para el informe de agosto. A esta revisión, producción de agosto se mantiene ausente: no se la estima ni se usa julio como sustituto. La captura eléctrica es retrospectiva y revisable.

## Sensibilidad: no existe una única cantidad natural de alertas

Se evaluaron las 27 combinaciones de umbral de observación {5%, 10%, 15%}, cambio absoluto {2,5; 5; 10 MW} y persistencia {2, 3, 4 meses}. La prioridad por magnitud permanece fija en 20% y 10 MW. Para agosto, resultan entre **4 y 8 actividades prioritarias**, frente a 6 con la regla base.

| Actividad | Prioridad en combinaciones de la grilla |
| --- | ---: |
| Cargas y puertos | 0/27 |
| Comercio y servicios: principalmente supermercados y centros comerciales | 10/27 |
| Alimentación y artículos de consumo masivo | 27/27 |
| Servicios públicos y transporte: agua y transporte en GBA | 0/27 |
| Industria automotriz | 3/27 |
| Derivados de petróleo | 0/27 |
| Construcción: elaboración de cemento y canteras | 27/27 |
| Madera y papel | 0/27 |
| Productos metálicos no automotores | 27/27 |
| Gran siderurgia | 0/27 |
| Industria textil | 18/27 |
| Químicas, caucho, plástico y otros minerales no metálicos | 0/27 |
| Extracción de minerales | 27/27 |
| Extracción de petróleo | 2/27 |

El cociente sobre 27 describe dependencia de esos criterios, no una probabilidad, nivel de confianza ni prueba de robustez a otras fuentes. Las actividades que cumplen 20% y 10 MW siempre entran en esta grilla por construcción. Los cuatro escenarios adicionales de abajo examinan precisamente esa regla de magnitud, cambiando un parámetro por vez y dejando observación y persistencia en la base.

| Prioridad por magnitud | Prioritarias en agosto | Actividad-meses prioritarios en historia |
| --- | ---: | ---: |
| 20% y 10 MW | 6 | 104 |
| 15% y 10 MW | 6 | 117 |
| 25% y 10 MW | 5 | 99 |
| 20% y 5 MW | 6 | 106 |
| 20% y 15 MW | 5 | 94 |

Historia: 44 meses comparables, enero de 2023-agosto de 2026, 14 actividades, 616 actividad-meses. Los conteos repiten actividades persistentes; no son eventos independientes. Aluar queda aparte. Al principio de la historia puede faltar la persistencia requerida. Son resultados retrospectivos sobre una sola captura, no desempeño prospectivo, falsos positivos ni exactitud predictiva.

## Uso en el tablero

El selector de mes mantiene la regla base. El laboratorio de sensibilidad tiene controles separados y un botón para restaurarla; cambiar controles no guarda ni redefine la regla oficial del proyecto. El contraste de producción mantiene su propio período visible. Los estados textuales acompañan el color, las tablas pueden recorrerse con teclado y los originales permanecen intactos.

La calidad de fuente sigue condicionada por cobertura de establecimientos no verificada y la discrepancia PDF-XLSX documentada. Ningún indicador identifica demanda de IA. El Excel descargable y los pronósticos congelados no se modifican en esta ampliación.

Los resultados completos y las huellas de entradas están en la descarga JSON del módulo de alertas. Reproducir: `python3 scripts/build_sector_alerts.py`.
