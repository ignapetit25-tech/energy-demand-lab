# Ramas argentinas e infraestructura de IA

Revisión documental: 24 de septiembre de 2026. La prioridad es describir la demanda argentina y documentar infraestructura sin atribuir variaciones agregadas a la IA.

## Tres universos distintos

1. La serie nacional histórica en GWh mantiene sus categorías, fuentes y archivos originales. Alimenta el informe principal, CSV y Excel.
2. La apertura de CAMMESA de agosto de 2026 cubre más de 8.000 empresas GUMA, GUME y GUDI, aproximadamente 90% de la gran demanda mayor según su introducción. Se transcribió y cotejó visualmente la tabla de la página 4; la cobertura está en la página 2. Conserva la unidad publicada, MW, sin convertir a GWh ni suponer que se trata de un pico instantáneo. Los porcentajes son los publicados: los niveles redondeados no permiten reproducirlos exactamente. Componentes, subtotales y total están identificados para evitar dobles sumas.
3. La utilización de capacidad instalada del INDEC mide otro universo productivo. La observación incorporada es julio de 2026 (58,2%, frente a 58,4% en julio de 2025). En el informe de agosto se muestra explícitamente como contexto del mes anterior; no es una observación eléctrica ni una comparación causal.

La apertura CAMMESA muestra +3,4% interanual en el total de su muestra y −1,2% sin Aluar. La rama industrias presenta −0,7%. Esto advierte que el aumento agregado no es uniforme. No identifica cargas de IA y no debe empalmarse con la categoría grandes usuarios de Datos Argentina, que tiene otra delimitación.

## Fuentes y trazabilidad

- [CAMMESA: gran demanda](https://cammesaweb.cammesa.com/gran-demanda/). Original conservado en `data/reference/cammesa-ramas-2026-08.pdf`; captura y SHA-256 en `data/sector_deep_dive.json`. La fecha de captura no reemplaza la fecha de publicación.
- [INDEC: capacidad instalada](https://www.indec.gob.ar/Nivel4/Tema/3/6/15). Publicación del 15/09/2026. El dato de agosto estaba anunciado para el 15/10/2026; no se anticipa ni se imputa.
- `data/infrastructure_registry.json` contiene las fuentes, fechas, actores y limitaciones de cada caso. Son comunicaciones de promotores, organismos y partes litigantes; no todas tienen la misma función probatoria.

## Registro inicial, no censo

Argentina: Stargate / Sur Energy y Clementina XXI. Referencias estadounidenses: Project Camellia y Colossus 2 / planta de Southaven. El filtro inicial muestra Argentina; los indicadores superiores abarcan los cuatro casos. Los casos extranjeros no se incluyen en la demanda argentina.

El estado está documentado a la fecha de cada fuente, no verificado en tiempo real. Una carta de intención no es obra iniciada, una operación informada no es una lectura de medidor y potencia de cómputo no es potencia eléctrica. Los MW anunciados de suministro tampoco son GWh consumidos. No se convierten usando horas supuestas ni un factor de utilización inventado.

Un valor `null` significa no documentado en las fuentes incorporadas, no cero ni inexistencia universal de datos. Ninguno de los cuatro casos cuenta aquí con GWh medidos y un período. La proporción atribuible específicamente a IA también queda nula. Clementina admite otras aplicaciones de supercómputo: no es una instalación exclusivamente de IA.

Los eventos judiciales distinguen quién afirma qué y cuándo. Demanda, intervención solicitada y fallo son etapas diferentes. No se verificó sentencia definitiva en los casos incorporados ni retraso cuantificado atribuible a ellos. Se muestran como contexto regulatorio y de plazos, nunca como medición eléctrica. No incorporar un litigio local tampoco certifica su ausencia.

## Actualizar sin contaminar el diagnóstico

1. Obtener la publicación original y registrar período, publicación cuando esté acreditada, captura y cobertura. Archivar el PDF sin modificar y calcular su SHA-256.
2. Cotejar visualmente tabla y unidad. Revisar cambios de muestra antes de comparar. No trasladar una observación a meses sin datos.
3. Actualizar los JSON de fuente. Para infraestructura exigir fuente de estado; si hay potencia, su fuente específica; si hay energía medida, fuente y período. Registrar litigios aparte con atribución de parte.
4. Ejecutar `python3 scripts/build_site.py`, `python3 scripts/verify_release.py` y la prueba de navegador `scripts/check_research.cjs` con Playwright disponible. Revisar informe, filtro, descarga y móvil antes de publicar.
5. Revisar el diff y publicar. No modificar el pronóstico prospectivo ya emitido.

Los nuevos módulos alimentan web y TXT, con JSON independientes descargables. CSV y XLSX conservan la serie nacional y no incluyen esta nueva tabla de MW. La actualización documental es manual: publicar automáticamente el sitio no descarga ni verifica nuevas fuentes.

## Interfaz y verificación

Se mantienen los colores, tarjetas y puntos de adaptación del sitio existente, siguiendo la guía `frontend-designer`. Los filtros usan `select` nativo y el contexto documental usa `details`: conservan navegación por teclado y foco del navegador sin introducir controles personalizados o dependencias nuevas. Se descartaron un framework adicional y un mapa de instalaciones: el primero añade migración sin necesidad; el segundo sugeriría precisión geográfica que no acreditan todas las fuentes.

Las pruebas cubren 390 y 1440 píxeles, meses sin cobertura, cambio de país por teclado, descarga JSON y distinción entre alegaciones y fallos. Se revisaron capturas de pantalla. Se conserva el modo de movimiento reducido existente y no se agregan animaciones. El registro necesita JavaScript para las tarjetas; sin él permanece disponible el enlace al JSON. La tabla por ramas permite desplazamiento horizontal en pantallas estrechas. Estas comprobaciones en Chromium no equivalen a una auditoría completa de accesibilidad o compatibilidad en todos los navegadores.
