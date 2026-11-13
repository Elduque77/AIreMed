# Declaración de uso de IA generativa

Proyecto final SI3003 Inteligencia Artificial, EAFIT 2026-1.

## Herramientas usadas
- **Claude (Anthropic), chat web.** Usado durante el desarrollo del proyecto para:
  - orientar el alcance del proyecto y el plan de trabajo;
  - proponer y escribir borradores de los scripts de descarga, limpieza y agregación de datos, el Naive Bayes Gaussiano (numpy), el RAG, las herramientas del agente, el loop agéntico, el dashboard de Streamlit y el script de evaluación;
  - depurar errores de instalación y ejecución (PowerShell, dependencias, Python 3.14);
  - redactar borradores del README y de este documento.
- **Modelo de lenguaje en tiempo de ejecución:** la app llama a un modelo alojado en Groq (endpoint compatible con OpenAI) como componente del agente. No es una herramienta de desarrollo.

## Qué hizo el equipo
- Eligió la idea del proyecto (agente de calidad del aire del Valle de Aburrá).
- Ejecutó y probó cada script, descargó los datos y revisó las salidas.
- Decidió usar solo 2024-2025 tras ver que 2020-2023 tenía escalas inconsistentes.
- Corrió la evaluación del agente tres veces, revisó las respuestas y ajustó el prompt y el manejo del último paso del agente.

## Transparencia sobre la evaluación del agente
- Se hicieron tres corridas de 12 preguntas (11/12, 9/12 y 12/12 en herramienta correcta). Entre ellas se cambiaron el prompt y el manejo del último paso.
- Después de ver la segunda corrida se relajó el criterio de la pregunta 12 (de "ninguna herramienta" a "no usar predict_tomorrow"), porque el agente respondió correctamente negándose a recomendar medicamentos. Los resultados de las corridas anteriores se conservan en `resultados/`.
- La regla automática de revisión de citas es sencilla; se verificó a mano.

## Origen de los datos y del código
- El identificador del conjunto de datos de datos.gov.co (`g4t8-zkc3`) se encontró citado en el repositorio público de otro grupo que trabaja en una idea similar. Solo se usó para ubicar la fuente; no se copió código de ese repositorio.
- Los documentos del RAG son públicos (SIATA y Alcaldía de Medellín).

## Limitaciones
- El código generado con asistencia de IA puede contener errores no detectados; las limitaciones conocidas están en el README.
