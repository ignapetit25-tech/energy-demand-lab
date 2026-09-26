# Estado y próximos pasos

## Entregado

- Web pública y publicación automática al enviar cambios a `main`.
- Informe sectorial mensual con comparación interanual, aportes y acumulado.
- Apertura CAMMESA por ramas para agosto de 2026, con PDF archivado y tasas de la fuente, y capacidad instalada INDEC de julio como contexto de otro período. Registro documental de infraestructura de IA con filtro por país y descargas JSON. [Alcance y mantenimiento](infraestructura-y-sectores.md). Desde el 26/09, el Excel añade Concentración, Aluar y Actividades con 56 meses completos de apertura GUMAs + AUTO en hojas separadas. El CSV y las hojas nacionales originales no cambian. [Método y límites del balance mensual](balance-mensual-y-actividades.md).
- Excel con `Informe` (mes editable en B4, fórmulas y gráfico), `Datos` (260 registros y fuente) e `IA y energía` (evidencia internacional y límites de atribución local). El archivo es histórico completo; no cambia el mes inicial según el selector web. La interfaz explica esa diferencia. El CSV exporta el mes seleccionado, tres sectores y total, acumulados y trazabilidad. El TXT incluye el diagnóstico y las fuentes de IA.
- Evaluador prospectivo conectado al tablero y a la descarga del registro. Calcula error firmado, absoluto y porcentual de los cuatro modelos; agrega MAE, RMSE, MAPE y sesgo, general y otoño/primavera. Sin observaciones, las métricas son nulas, no cero.

## Dependiente de una publicación futura

Octubre de 2026 sigue pendiente. El evaluador rechaza capturas anteriores al fin del mes objetivo, fechas futuras, demandas no positivas, duplicados y pronósticos emitidos tarde. Conserva la primera observación **registrada por el proyecto**, sin afirmar que sea la primera publicación oficial. Si la fuente corrige un dato ya registrado, detiene la importación para revisar la revisión por separado.

Para registrar un resultado, descargar la consulta CSV oficial que contenga `indice_tiempo` y `demanda_total`, conservar la hora real de descarga con zona horaria y ejecutar:

```sh
python3 scripts/evaluate_prospective.py --snapshot ARCHIVO.csv --captured-at FECHA_ISO_CON_ZONA --source-url URL_HTTPS_DE_APIS_DATOS_GOB_AR
```

Si se conoce la fecha oficial de publicación, añadir `--publication-date AAAA-MM-DD`. Si no se conoce, queda nula; la fecha de captura no se presenta como fecha de publicación. No inventar ni retroceder fechas. El script archiva los bytes fuente por hash y agrega el registro a `prospective/outcomes.json`; no modifica `prospective/forecasts.csv`. Las ejecuciones repetidas con el mismo dato no duplican registros. Revisar cambios antes de enviar a GitHub.

## Pendiente de implementación o investigación

1. **Ingesta periódica de nuevas publicaciones y gestión de revisiones.** La actualización sigue siendo manual. La publicación automática del sitio no descarga datos nuevos.
2. **Intervalos predictivos calibrados.** No se usa el MAE como margen de confianza. Requiere diseño y evaluación antes de incorporarlo.
3. **Clima disponible al pronosticar y referencia profesional de CAMMESA.** Falta verificar archivos de pronósticos con fechas de emisión recuperables. El SMN trimestral no equivale a una temperatura mensual numérica.
4. **Calendario histórico de feriados.** Falta una colección oficial fechada antes de incorporarlo a otro modelo. No cambia el pronóstico congelado de octubre.
5. **Comparabilidad por ramas y medición de infraestructura.** Ya hay doce ediciones CAMMESA con historia por mes del calendario y 19 meses de capacidad instalada INDEC. Falta resolver el cambio documental de cobertura CAMMESA (98% a 90%) antes de construir una serie mensual homogénea, extender desagregaciones y encontrar energía medida por instalación. Los siete casos del registro (cinco argentinos) no son un censo ni una estimación de consumo de IA.

## Mantenimiento del Excel

El archivo está versionado y se copia a la web. Su manifiesto vincula la huella del XLSX con las huellas de los datos sectoriales y de `data/ai_energy_evidence.json`. El constructor del sitio rechaza un Excel desactualizado o alterado. La creación usa `@oai/artifact-tool` del entorno de autoría; GitHub Actions no necesita ese paquete para publicar el archivo ya verificado.

Para regenerar en el entorno de autoría, ejecutar `python3 scripts/build_monthly_reports.py`, usar `scripts/build_excel.mjs` con las dependencias de escritorio instaladas y luego `python3 scripts/build_site.py`. Se verificaron recálculo con cambios de mes y mes fuera de cobertura, fórmulas, valores guardados, hojas y gráfico. Se revisaron las hojas visualmente. La prueba nativa con LibreOffice no pudo ejecutarse en este entorno; no se afirma una prueba en Microsoft Excel. El alcance de la investigación está en [IA y electricidad](ia-electricidad.md).
