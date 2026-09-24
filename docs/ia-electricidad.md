# IA y electricidad: alcance de la revisión

Revisión: 24 de septiembre de 2026. Registro reproducible: `data/ai_energy_evidence.json`.

La pregunta es si la adopción de IA elevó el consumo industrial argentino. La evidencia incorporada **no identifica ese efecto**. Las categorías locales agregan actividades distintas, no contienen una variable de adopción ni separan la carga eléctrica de IA. No se calcula una correlación espuria entre dos cifras mundiales anuales y una serie argentina mensual.

La AIE documenta expansión del consumo en centros de datos orientados a IA a escala mundial. Esto respalda la relevancia energética del cómputo, pero no prueba un aumento en fábricas argentinas. El uso de servicios en la nube puede desplazar el consumo a otra jurisdicción; las mejoras de eficiencia y los cambios de producción también deben medirse.

Los 485 TWh de 2025 son una estimación de todos los centros de datos. El 50% es una tasa de crecimiento de centros orientados a IA: no una fracción de esos TWh. Los 950 TWh de 2030 son una proyección. El cociente 70/800, calculado en Excel, es un aporte aproximado de todos los centros de datos al incremento mundial de 2025, no el consumo exclusivo de IA. Las fuentes y limitaciones de cada dato acompañan el registro y la hoja de evidencia.

La carta de intención OpenAI/Sur Energy de octubre de 2025 acredita una iniciativa empresarial, no consumo realizado ni puesta en servicio. No inferimos la situación operativa actual a partir de ese anuncio.

## Próxima evidencia necesaria

1. Series mensuales de medidores de centros de datos y establecimientos, con localización y fechas de operación.
2. Adopción de IA y fracción de cómputo atribuible a sus cargas; separar infraestructura general de IA.
3. Producción, clima, calendario, tarifas y cambios de equipamiento de establecimientos comparables.
4. Diseño de comparación antes/después con grupo comparable y revisión de tendencias previas. Aun así, explicitar supuestos y factores de confusión.

## Descargas

- CSV: UTF-8 con BOM, delimitador `;`, coma decimal, seis decimales sin separador de miles. Filas: tres sectores y total. No sumar el total otra vez. `ia_gwh` vacío expresa falta de identificación, no cero. Tasas en porcentaje y contribuciones en puntos porcentuales. Acumulados: enero al mes seleccionado en ambos años; campos vacíos si falta cobertura.
- TXT: diagnóstico del mes, acumulados, evidencia y fuentes, sin depender del sitio web.
- XLSX: conserva Informe y Datos; añade IA y energía. El mes se cambia en Informe!B4. El contexto internacional es estático a la fecha de revisión, no una serie mensual ni evidencia disponible en cada fecha histórica.

No se alteró el pronóstico prospectivo ni se añadieron regresores o conclusiones causales al modelo.
