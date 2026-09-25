# Concentración, Aluar y apertura eléctrica

Revisión: 24/09/2026. Análisis descriptivo, no atribución causal a IA.

## Tres avances

1. **Abastecimiento de Aluar:** dos memorias anuales permiten distinguir producción de aluminio, consumo total y fuentes de abastecimiento. Entre julio 2024–junio 2025 y julio 2025–junio 2026, la producción crece 1,20%, el consumo eléctrico 1,68% y el abastecimiento del sistema nacional bajo contrato Futaleufú 8,49%. La térmica propia cae 4,69% y la eólica propia sube 4,14%. Eso demuestra que las magnitudes difieren, no identifica la causa mensual de agosto.
2. **Concentración del crecimiento:** el residencial representa 69,39% del incremento nacional de agosto; grandes usuarios aporta 99,82% del incremento enero–agosto porque otros aportes se compensan. En la muestra mensual GUMA/GUME/GUDI, Aluar aporta 171 de los 131 MW de incremento neto (130,53%); su participación en el nivel es solo 13,86%. Las participaciones en un aumento neto pueden superar 100% o ser negativas.
3. **Detalle eléctrico:** 14 actividades, no 14 establecimientos, dentro del informe operativo GUMAs + AUTO. Agosto completo y septiembre 1–16 se ofrecen como niveles separados. Otra tabla del documento compara septiembre 1–16 contra iguales días de 2025: total +6,8%, sin Aluar +5,8%, cuatro bloques con suba. No debe extrapolarse a un cierre mensual.

## Originales y límites

- [Aluar, memoria 2024–2025](https://cdn.aluar.com.ar/assets/uploads/EEFF_Aluar_Ejercicio_2024_2025_4_T_7869bb3511.pdf), PDF página 4: Planta Puerto Madryn, División Primario. Total eléctrico 6.706.909 MWh; fuentes 6.706.524 MWh. Se conserva el residuo documental de **385 MWh**, no se corrige ni asigna a una tecnología.
- [Aluar, memoria 2025–2026](https://cdn.aluar.com.ar/assets/uploads/EEFF_Aluar_Ejercicio_2025_2026_4_T_c41c605c28.pdf), PDF página 5: total y fuentes concilian en 6.819.827 MWh. Página 8: la compañía declara concluida en agosto la construcción, implementación y puesta en marcha de una ampliación eólica de 336 MW nominales, total 582 MW. No equivale a energía generada ni a verificación independiente de habilitación. Este hito posterior al cierre no explica retrospectivamente el balance anual terminado en junio.
- [CAMMESA, informe operativo actualizado 17/09/2026](https://cammesaweb.cammesa.com/download/analisis-demanda-grandes-usuarios-al-j25-de-febrero-21/?wpdmdl=39430), PDF páginas 1, 5, 7 y 11. El slug de descarga conserva una fecha antigua: se verifica la fecha dentro del archivo, no se deduce de la URL. Página 5 advierte altas y bajas de usuarios; página 7 identifica la demanda de Aluar como neta de la red y publica 14 actividades. Sus columnas tienen ventanas distintas: no usamos sus tasas como comparaciones de iguales días. Página 11 sí compara 16 días y 12 días hábiles en ambos años, por cuatro bloques.

Las fechas documentales no acreditan la primera disponibilidad pública. Se guarda por separado la fecha de consulta; esta evidencia no se introduce en pronósticos ya emitidos. Los originales archivados, páginas y SHA-256 están en `data/concentration_evidence.json`. Los datos mensuales previos y sus fuentes se mantienen en `data/sector_history.json`.

## Contabilidad reproducible

- Aporte sectorial en puntos porcentuales = 100 × cambio sectorial / total anterior.
- Participación en aumento neto = 100 × cambio sectorial / cambio total, solamente si el total aumenta. Si cae o no cambia, se guarda `null`, no infinito ni una participación engañosa.
- Participación en nivel = 100 × nivel del componente / nivel total actual. No es la participación en aumento.
- Los aportes CAMMESA se calculan con niveles enteros publicados, conservando el residuo de redondeo y las tasas originales por separado.
- Balance anual de cambios de Aluar, GWh: **230,481 − 149,916 + 32,738 − 0,385 = 112,918**. El cuarto término es el cambio del residuo documental, no una fuente física.
- GUMAs: las sumas por actividad toleran 0,21 MW de diferencia por redondeo. Aluar y subtotales no se suman nuevamente a las actividades.
- Persistencia INDEC: siete signos interanuales por actividad, enero–julio 2026 vs. iguales meses 2025. No mide magnitud, ponderación, producción ni consumo eléctrico. Se conservan las notas de alimentos y químicos.

## Lo que sigue sin resolverse

- Balance mensual homogéneo de producción, consumo bruto, toma de red y generación propia utilizada para agosto 2025 y 2026. Las memorias anuales terminan en junio: no permiten asignar porcentajes causales al salto mensual.
- Motivo del cambio documental de cobertura mensual CAMMESA, 98% a 90%. No se equipara con las altas y bajas del informe operativo.
- Panel fijo y observaciones de iguales días para las 14 actividades; no se incorporó agosto 2025 en esa apertura. No hay una lista pública verificada de establecimientos individuales adicionales en esta entrega.
- Medición eléctrica que aísle cargas de IA. Ni la actividad industrial ni los anuncios de capacidad resuelven esa atribución.

## Interfaz y actualización

Se conserva el sistema visual del sitio. Las tablas y selectores nativos permiten distinguir ventanas, unidades y universos; las advertencias están junto a cada resultado. En móvil, las tablas tienen desplazamiento horizontal accesible por teclado, sin desbordamiento de la página. No se añaden gráficos que sugieran una serie mensual homogénea inexistente.

`scripts/build_concentration.py` valida fuentes, hashes, ventanas, sumas y valores desconocidos, y genera `dashboard/concentration-data.js` y la descarga JSON. `build_monthly_reports.py` añade este contexto únicamente al informe de agosto, con fecha de revisión y señal posterior explícita. Los CSV nacionales, el Excel y los pronósticos congelados permanecen intactos.

Para actualizar: archivar y cotejar visualmente los originales, editar el registro curado, ejecutar `python3 scripts/build_site.py`, `python3 scripts/verify_release.py` y las comprobaciones de navegador de concentración, investigación e informe mensual. Revisar las capturas antes de publicar.
