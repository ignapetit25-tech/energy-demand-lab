# Registro prospectivo: operación y auditoría

Implementado el 26/09/2026. Usa el protocolo `sector-validation-1` sin cambiarlo. La cohorte es octubre 2026–septiembre 2027; todavía no corresponde emitir ninguna señal. El registro operativo separado es `prospective/sector-alerts-ledger.json`. El JSON del protocolo conserva su estado original como documento de diseño, no como contador vivo.

## Qué hace

- Importa el ZIP oficial de CAMMESA con el XLSX diario, sin recalcular o modificar el original. Verifica estructura de columnas, fechas continuas, sumas de componentes y los seis meses completos necesarios para tasas y persistencia.
- Calcula las 14 actividades con el clasificador congelado y Aluar aparte. Una emisión por mes, sin reemplazo. Archiva originales, entradas normalizadas, código y huellas.
- Registra la observación pública de un commit de GitHub que ya contiene exactamente la señal. Usa la hora UTC real de esa comprobación, no la fecha editable de autor del commit. Es una cota conservadora de disponibilidad pública: puede excluir una señal que realmente se publicó antes pero se verificó tarde.
- Guarda el primer resultado IPI y conserva las revisiones como eventos separados. Nunca reevalúa el resultado primario usando la revisión más favorable.
- Evalúa solo pares elegibles con publicación comprobada antes del IPI, comparador archivado y períodos coincidentes. Ausencia de resultados produce métricas nulas. No hace una declaración favorable antes del cierre y resolución de los doce meses.

Las huellas encadenadas detectan cambios accidentales; no son firmas digitales ni un registro inviolable. Los commits públicos aportan evidencia externa. La descarga y el ingreso siguen siendo manuales. No hay monitor ni notificaciones.

## Flujo

1. Después del cierre del mes, descargar y conservar el ZIP CAMMESA y su hora real de captura. Preparar una extracción revisada de la última publicación IPI conocida. Su carácter de «última disponible» exige comprobación humana en la página oficial; no lo determina automáticamente el programa.
2. Ejecutar desde la raíz del repositorio:

```sh
python3 -m scripts.sector_registry issue --period AAAA-MM --electricity ARCHIVO.zip --captured-at FECHA_ISO_CON_ZONA --source-url URL_HTTPS_CAMMESA --baseline IPI_CONOCIDO.json
```

Si falta un comparador, omitir `--baseline`: la señal se conserva, pero no será elegible para la comparación primaria. No completarlo después.

3. Revisar los archivos nuevos, hacer commit y publicar el registro y los originales archivados en el repositorio público. Inmediatamente comprobar ese commit:

```sh
python3 -m scripts.sector_registry attest-publication --period AAAA-MM --commit SHA_COMPLETO_DE_40_CARACTERES
```

El comando consulta la API de GitHub con `gh`, comprueba que el repositorio sea público y que el archivo del commit contenga la misma emisión. No crea el commit ni lo envía. Registrar/publicar también este evento de comprobación. Si se llega tarde, no retrofechar: se conservará como no elegible.

4. Cuando se publique el IPI del mismo mes, preparar la extracción revisada y registrar:

```sh
python3 -m scripts.sector_registry outcome --period AAAA-MM --record IPI_RESULTADO.json
python3 -m scripts.sector_registry status
```

Repetir una observación idéntica no duplica el evento. Una nueva captura con cambios se agrega como revisión, nunca reemplaza el primer resultado. Una revisión con fecha anterior o igual a otra ya registrada es rechazada.

5. Si se perdió un mes, documentarlo con `exclude --period AAAA-MM --reason "Motivo concreto"`. No crear señales retrospectivas para llenar el vacío. Las exclusiones no borran eventos ni eliminan resultados ya evaluables.

6. Regenerar informes y sitio con `python3 scripts/build_site.py`, ejecutar pruebas y revisar antes de publicar. `status` es de solo lectura respecto del registro. Las operaciones se serializan con un bloqueo local y se guarda el JSON mediante reemplazo atómico.

## Formato de extracción IPI

El archivo JSON debe incluir `period` (AAAA-MM), `published_at` (fecha oficial o fecha-hora con zona), `captured_at` (fecha-hora real con zona), `source_url` (INDEC HTTPS), `archive` (ruta al original descargado), `sha256`, `reviewed: true`, `reviewer` y `observations`.

`observations` debe contener exactamente `construction`, `metals` y `textiles`. Cada uno contiene `code` (respectivamente `26941`, `28`, `17`), `yoy_percent` numérico y `locator` con página/cuadro/celda. Se ingresa la tasa interanual de la serie original, no la acumulada ni la variación mensual desestacionalizada. Para el comparador agregar `latest_known_attestation: true` solo después de revisar que sea la última publicación disponible.

La captura de tasas es una transcripción humana revisada: verificar hash y fechas no demuestra que la cifra corresponda a la celda del PDF. El programa lo señala explícitamente y conserva el original y la extracción para auditoría. No inventar valores faltantes ni cambiar un código por otra categoría. El esquema actual exige las tres categorías; ante una discontinuidad, detener la carga y documentar la exclusión, sin escoger una sustitución favorable.

## Fechas y límites

No existe una opción CLI para cambiar el reloj. Se rechazan cohortes ajenas, emisiones antes de cerrar el mes, capturas futuras, resultados capturados antes de emitir y cambios en reglas/código congelados. Si la publicación IPI solo tiene fecha, la comprobación pública debe ser de un día UTC anterior.

Los tests usan datos sintéticos en memoria y archivos temporales, nunca se incorporan al registro público. La evaluación sigue el bootstrap por mes, semilla y umbrales predefinidos. No mide falsas alarmas operativas, causalidad ni demanda atribuible a IA.
