# Tablero de demanda eléctrica

## Informe mensual sectorial

Abrir `monthly-report.html` o entrar desde «Abrir informe mensual» en el tablero. El mes predeterminado es agosto de 2026, último disponible en la instantánea. Se pueden consultar 248 meses comparables desde enero de 2006; son reconstrucciones con la descarga del 20 de septiembre de 2026, no informes emitidos en esas fechas.

Incluye comparación interanual, cambios por sector en GWh, contribuciones en puntos porcentuales, participación sectorial y acumulado de enero al mes seleccionado contra igual período anterior. No se suman acumulados incompletos. El texto se genera con reglas reproducibles y cálculos sobre los archivos del proyecto, sin llamadas a un modelo o servicio externo.

«Descargar Excel» entrega un XLSX completo con mes editable en Informe!B4, fórmulas, gráfico y datos originales. Abre en agosto de 2026, independientemente del mes seleccionado en la web. «Informe en texto» exporta Markdown y «CSV del mes» descarga los datos del mes seleccionado con su fecha de fuente. «Imprimir / PDF» abre el diálogo del navegador. El archivo del último informe queda también en `reports/monthly/2026-08.md`, con su JSON. No se automatizan descargas de datos nuevos.

Regenerar con `python3 scripts/build_dashboard.py` (tablero e informes) o `python3 scripts/build_monthly_reports.py` (informes). Este último valida la huella del archivo sectorial, períodos únicos, valores finitos no negativos y suma de componentes. Las pruebas cubren conciliación de aportes, acumulados incompletos, cambios que se cancelan y denominadores sectoriales nulos.

Verificación al 24 de septiembre de 2026: 20 pruebas del proyecto pasaron. `scripts/check_monthly_report.cjs` verifica selección histórica, cálculos visibles, descargas, acción de impresión, estilos de impresión y adaptación móvil. Se revisaron capturas de escritorio, móvil y estilo de impresión; no se generó un PDF paginado como entregable.

## Tablero general

Abrir `index.html` directamente en un navegador. No requiere conexión ni dependencias externas. Para previsualizar por HTTP desde la raíz del proyecto: `python3 -m http.server 8765`, y abrir `/dashboard/`.

Regenerar la instantánea después de actualizar los artefactos oficiales del proyecto: `python3 scripts/build_dashboard.py`. El generador lee las series, la evaluación anidada y el registro congelado; no reentrena ni cambia pronósticos. `data.js` es un archivo generado.

Incluye gráfico con selector de período y consulta mensual accesible por teclado; comparación de MAE por estación; tabla histórica; registro prospectivo descargable; fuentes y huellas SHA-256. El registro está conectado al evaluador de `prospective/outcomes.json`: muestra pendientes y, cuando existan observaciones archivadas, errores y métricas descriptivas. No hay actualización automática ni intervalo predictivo calibrado. Consultar `docs/estado-y-actualizacion.md` para incorporar publicaciones y revisar pendientes.

Validación realizada: las 15 pruebas científicas y el verificador de resultados del proyecto pasan. La prueba de navegador `scripts/check_dashboard.cjs` comprueba valores, filtros, navegación por teclado, descarga CSV y ausencia de desbordamiento en 390 px. Capturas revisadas en `desktop.png` y `mobile.png`. Requiere Playwright y Chromium instalados para repetirla.

Diseño: HTML semántico, CSS con variables compartidas, controles nativos, foco visible, layout adaptable y movimiento reducido. Sin librerías, fuentes remotas o seguimiento. La evaluación histórica mostrada es retrospectiva y exploratoria; la variante con temperatura posterior se identifica como diagnóstico no operable. El histórico utiliza la descarga disponible en 2026, no una colección de primeras publicaciones.
