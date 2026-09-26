# Balance mensual de Aluar e historia eléctrica

Revisión del 26/09/2026. Esta ampliación no altera los datos nacionales, los modelos ni el pronóstico congelado de octubre.

## Resultado de la investigación

Se localizó la [base diaria oficial de grandes usuarios](https://cammesaweb.cammesa.com/download/base-de-datos-2/?wpdmdl=39428), enlazada desde la publicación de CAMMESA del 25/09/2026. El ZIP contiene `Base de datos GU Semanal.xlsx`. Su hoja `Base Detalle diaria GUMAs ACT` tiene 1.727 registros diarios consecutivos, del 01/01/2022 al 23/09/2026. Se incorporan 56 meses completos, enero 2022-agosto 2026, y septiembre parcial separado. Son 798 registros actividad-período: 784 completos y 14 parciales.

Las 14 actividades son categorías de usuarios, no establecimientos individuales. El universo es GUMAs + AUTO, con Aluar individualizada y subtotales separados. Las altas y bajas de usuarios impiden presentarlo como un panel fijo. No se empalma con GUMA/GUME/GUDI ni con las categorías nacionales.

### Aluar: parte del balance ya observable

| Variable | Agosto 2025 | Agosto 2026 |
| --- | ---: | ---: |
| Días completos | 31 | 31 |
| Demanda neta de red, MW medios calculados | 375,7153 | 547,1720 |
| Energía neta de red, GWh calculados | 279,532209 | 407,095973 |

Variación interanual: aproximadamente +45,63%. Se calcula la energía como suma de MW medios diarios por 24 horas, dividida por 1.000. No se trata de una medición del consumo bruto de planta ni de una liquidación definitiva DTE. Las cifras conservan precisión en el archivo; las vistas redondean sin modificar los originales.

No se encontró en las fuentes consultadas el balance mensual conjunto de toneladas producidas, consumo bruto, generación propia efectivamente utilizada, ventas/inyecciones y pérdidas. Por eso no se asignan porcentajes causales a producción, autogeneración o IA. No encontrarlos no demuestra que esos datos no existan.

El [estado trimestral de Aluar a septiembre 2025](https://cdn.aluar.com.ar/assets/uploads/EEFF_Aluar_Ejercicio_2025_2026_1_T_ec2d20bfc1.pdf), PDF página 34, declara 113.363 t para julio-septiembre y ventas de energía eólica/térmica de 81,8 GWh. No son producción de agosto ni autoconsumo. No se divide un trimestre por tres. La tabla inferior de Futaleufú lleva una cabecera de período diferente: no se incorpora como balance mensual de Aluar.

También se revisaron la página de inversores, la información pública de MEMNet y el histórico renovable. MEMNet requiere usuarios autorizados para informes personalizados; no se accedió a información privada ni se enviaron solicitudes. La respuesta pública histórica renovable consultada devuelve agregados por tecnología, insuficientes para identificar autoconsumo de Aluar. La descarga del informe renovable mensual falló en esta revisión. Las consultas y brechas quedan en `data/aluar_monthly_research.json`.

### Historia de actividades

En agosto 2026, diez actividades de GUMAs + AUTO aumentan frente a agosto 2025. Construcción cae aproximadamente 26,4%, productos metálicos no automotores 23,7%, textiles 18,8% y servicios públicos/transporte 4,5%. Industrias sin Aluar, como bloque ponderado por su demanda, cae aproximadamente 0,9%. Contar actividades con suba no equivale a ponderar su tamaño ni a describir toda la industria argentina.

Las comparaciones anuales se calculan exclusivamente entre meses completos. Septiembre 1-23 no se compara con septiembre completo; sus tasas anuales se guardan como nulas. El año inicial carece de comparaciones anteriores en esta base. Los meses bisiestos conservan sus días: los niveles son promedios diarios, no sumas de MW.

## Discrepancias entre archivos: no ocultarlas

Para agosto 2026, el PDF del 17/09 muestra 2.293,1 MW; el PDF actualizado al 24/09 muestra 2.295,2 MW; la media de registros diarios del XLSX capturado el 26/09 da 2.292,0401 MW. Se validó que los componentes diarios y las ramas del XLSX concilian. La causa de la diferencia externa no quedó confirmada: no se la interpreta como crecimiento, no se corrige el original y no se reemplazan silenciosamente las ediciones archivadas. El nombre de descarga del PDF conserva una fecha antigua que no se usa para fechar su contenido.

La fecha 25/09 del nombre del ZIP archivado corresponde a la edición enlazada y a su metadato; la fecha de captura es 26/09. No se infiere una fecha de primera disponibilidad de cada registro histórico. Esta es una instantánea retrospectiva revisable, no una base de vintages contemporáneos para backtesting.

## Reproducción y controles

`scripts/build_activity_history.py` usa la biblioteca estándar: abre el ZIP, encuentra la hoja por nombre y relación OOXML, lee los valores almacenados, reconstruye la fecha con mes y número de día y valida continuidad, duplicados, valores finitos y conciliación de componentes. Nunca recalcula ni guarda el XLSX de CAMMESA. Los hashes del ZIP, el miembro XLSX y los PDF permiten comprobar la captura. El JSON incluye columnas y filas de origen de cada mes.

El sitio muestra un selector de mes completo, las 14 comparaciones y el mismo mes a través de los años para cada actividad. Se mantienen controles nativos y tablas desplazables del diseño existente. No se introduce un gráfico continuo que mezcle meses completos con parciales.

## Excel ampliado

Se preservan `Informe`, `Datos` e `IA y energía`, incluidos sus valores, fórmulas, formato, validación y gráfico. Se añaden:

- `Concentración`: aportes nacionales mensuales/acumulados vinculados a `Informe!B4` y descomposición de las 12 publicaciones GUMA/GUME/GUDI. Las tasas y los porcentajes de aumento neto son conceptos distintos. Si el total no crece, se muestra `n.a.`.
- `Aluar`: balance anual, residuo documental de 385 MWh y serie mensual de toma de red. La conversión a GWh es una fórmula con constantes visibles. Los campos no observados permanecen vacíos, nunca cero.
- `Actividades`: tabla filtrable de 798 registros, con mes, categoría, rama, días, estado completo/parcial, MW medios, comparación anterior y tasas calculadas mediante fórmulas.

El control mensual cambia el informe y la concentración; no desplaza el período fiscal del balance anual ni borra la historia completa de las otras hojas. El archivo no consulta internet automáticamente.

Se probaron recálculo, mes anterior, mes ausente, total sin crecimiento y potencia cero restaurando luego los valores. Se compararon las tres hojas originales con la copia previa: valores, fórmulas, estilos efectivos y validación iguales. Se verificaron el gráfico y las fórmulas guardadas en OOXML, las celdas faltantes y ausencia de errores. Los renders se revisaron visualmente. La comprobación se hizo con el motor de hojas de cálculo y el archivo exportado; no se ejecutó Excel de Microsoft en esta sesión.

El manifiesto del Excel incluye las huellas de las nuevas fuentes. La publicación falla si las fuentes cambian sin regenerar el libro. Para actualizar: archivar originales, revisar diferencias, regenerar historia, actualizar el Excel con `scripts/build_excel.mjs`, ejecutar pruebas, construir y verificar el sitio. El CSV nacional permanece intacto.
