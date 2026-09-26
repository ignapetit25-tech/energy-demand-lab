# Solicitudes de datos: Aluar y CAMMESA

Preparadas el 26/09/2026. **Borradores no enviados.** Completar nombre, apellido y correo del remitente antes de utilizar. No se presume afiliación institucional, derecho de acceso a datos privados ni obligación de respuesta.

## 1. Aluar: balance eléctrico mensual

Canal verificado: [contacto oficial de Aluar](https://www.aluar.com.ar/contacto). La empresa publica `secretariadirectorio@aluar.com.ar` para inversores y ofrece Secretaría del Directorio en su formulario. Se propone pedir derivación al área que gestione información energética pública, no afirmar que ese contacto sea el responsable técnico.

**Asunto:** Consulta de información pública: balance eléctrico mensual de Puerto Madryn

Estimados/as:

Estoy desarrollando Energy Demand Evidence Lab, un proyecto independiente de análisis de demanda eléctrica argentina basado en fuentes públicas. El proyecto está disponible en https://ignapetit25-tech.github.io/energy-demand-lab/.

Quisiera consultar si pueden compartir información pública, o indicarme dónde encontrarla, para interpretar la demanda neta de red de Aluar en agosto de 2025 y agosto de 2026. A partir de la base diaria operativa de CAMMESA obtuvimos aproximadamente 279,5 y 407,1 GWh, respectivamente. Son cálculos propios, no cifras que presentemos como consumo bruto de planta ni como datos definitivos de Aluar.

¿Sería posible conocer, para esos dos meses y con un mismo perímetro de medición:

1. Producción de aluminio líquido, en toneladas, e identificación de la planta cubierta.
2. Consumo eléctrico de la planta, especificando si incluye servicios auxiliares y otras instalaciones.
3. Importaciones y exportaciones físicas de electricidad en sus puntos de conexión a la red, en MWh, o la definición exacta de la medición neta disponible.
4. Generación propia dentro de ese perímetro, separando generación bruta, auxiliares y energía efectivamente utilizada por la planta, si se cuenta con ese detalle.
5. Inyecciones o ventas a terceros, pérdidas y otros ajustes necesarios para conciliar el balance, sin duplicarlos con las exportaciones físicas.

Nos interesa distinguir generación instalada en planta de energía renovable o hidroeléctrica suministrada desde instalaciones externas mediante contratos. Una venta de energía o generación de un parque no equivale necesariamente a autoconsumo físico en Puerto Madryn.

Si existe una serie mensual pública desde enero de 2022, agradecería el enlace o archivo. Para una primera respuesta, los dos meses indicados y sus definiciones serían suficientes. No solicitamos información de clientes, contratos comerciales confidenciales ni detalle individual no publicable.

Publicaríamos los datos únicamente con su fuente, período, unidad y condición provisoria o definitiva. Agradecería también indicar condiciones de reutilización y si una respuesta técnica puede citarse públicamente; no publicaríamos correspondencia ni datos personales sin autorización.

Si esta consulta corresponde a otra área, agradecería la derivación o un contacto institucional apropiado.

Saludos cordiales,

[Nombre y apellido]

Energy Demand Evidence Lab, proyecto independiente
[Correo de respuesta]

## 2. CAMMESA: conciliación de publicaciones

Canal verificado: [formulario oficial de contacto](https://cammesaweb.cammesa.com/contacto/). Seleccionar el asunto disponible más apropiado y solicitar derivación al equipo de estadísticas de demanda. No se identificó ni se inventó un correo técnico específico.

**Asunto:** Consulta metodológica: conciliación de demanda GUMAs + AUTO de agosto de 2026

Estimados/as:

Estoy desarrollando Energy Demand Evidence Lab, un proyecto independiente que utiliza publicaciones de CAMMESA y conserva sus fechas y versiones. Quisiera consultar una diferencia entre la tabla «Perfil principales ramas / actividades», página 7, y la base diaria publicada.

Para agosto de 2026, ambos PDF indican 31 días:

| Fuente | Total MW medios |
| --- | ---: |
| PDF actualizado al 17/09/2026 | 2.293,1 |
| PDF actualizado al 24/09/2026 | 2.295,2 |
| Promedio de los 31 días de la base diaria capturada el 26/09/2026 | 2.292,0401 |

La base procede del ZIP «Base de datos GU Semanal.xlsx», enlazado en la publicación del 25/09/2026. Calculamos el promedio de todos los días de agosto en «Base Detalle diaria GUMAs ACT», columna H, y lo cotejamos con «Base diaria» y «Base Detalle diaria GUMAS Rama». Los tres resultados coinciden. El promedio de los 20 días hábiles es 2.363,2214 MW, por lo que esa selección no reproduce el total del PDF.

Entendemos que las mediciones operativas son provisorias. Para documentar correctamente la diferencia, ¿podrían aclarar:

1. Qué fecha y hora de corte, versión de base y regla de promedio alimentaron la columna de agosto de cada PDF.
2. Si el cambio del total entre ediciones y la diferencia respecto del XLSX se deben a revisiones de registros, cobertura de usuarios, reglas de medición u otra causa identificada.
3. Si existe un archivo público de conciliación o un valor definitivo del DTE comparable con ese mismo universo GUMAs + AUTO, separado de otros grupos de grandes usuarios.
4. Si es posible obtener el número de usuarios por actividad y mes, y altas, bajas o reclasificaciones agregadas, sin identificar establecimientos privados.
5. Cuál es la definición exacta de Aluar en la base: puntos de medición comprendidos, neteo de inyecciones y tratamiento de autogeneración. ¿Existe una serie pública mensual de importación, exportación y consumo bruto bajo ese perímetro?

No interpretamos esta diferencia como crecimiento de demanda ni afirmamos que alguna publicación sea errónea. Mantendremos ambas versiones hasta conocer su conciliación.

Podemos remitir los hashes y el cálculo reproducible. Agradecería indicar si la respuesta metodológica puede citarse públicamente o, preferentemente, facilitar un enlace a documentación publicada.

Saludos cordiales,

[Nombre y apellido]

Energy Demand Evidence Lab, proyecto independiente
[Correo de respuesta]

## Anexo técnico para adjuntar solo si lo solicitan

La solicitud mínima comprende agosto de 2025 y agosto de 2026; la extensión deseada es enero de 2022 a agosto de 2026. Formato preferido: CSV o XLSX con una fila por mes y variable. Un PDF o enlace público también sirve si identifica período y definiciones.

| Campo | Información requerida |
| --- | --- |
| Período y cobertura | Mes calendario, planta o agregado, puntos de conexión, días u horas cubiertos |
| Variable y unidad | Nombre original, MW medios / MWh / toneladas; no intercambiarlos |
| Definición | Bruto/neto, importación/exportación, generación/autoconsumo/contrato |
| Valor y estado | Número observado; faltante explícito, no cero; provisorio o definitivo |
| Revisión | Fecha de publicación y de corte, versión, razón de revisión si existe |
| Fuente | Documento, tabla/página o enlace reutilizable |
| Conciliación | Identidad contable utilizada y partidas de ajuste, sin doble conteo |

No imponer una suma de energía física y contractual: primero se debe acordar un perímetro y separar ambos conceptos. Tampoco dividir producción trimestral por tres. En ausencia de algún campo, pedir qué parte sí es publicable.

La tabla de diferencias y los hashes están en el [informe de discrepancias](../reports/research/discrepancias-cammesa.md). Antes de enviar: revisar la firma, elegir el canal, quitar campos no necesarios y confirmar que no se adjunta información privada. El envío requerirá una instrucción expresa del usuario; estos borradores no constituyen un envío.
