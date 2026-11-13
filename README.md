# Agente de calidad del aire del Valle de Aburrá

Proyecto final de SI3003 Inteligencia Artificial (EAFIT, 2026-1). Integrantes: [INTEGRANTES].

Dashboard en Streamlit con mapa de estaciones, serie de tiempo de PM2.5, predicción de la categoría del día siguiente y un agente LLM con RAG y 3 herramientas (`get_pm25`, `predict_tomorrow`, `search_docs`).

Herramienta analítica. No es consejo médico, legal ni de seguridad.

## Datos
- PM2.5, lluvia y viento horarios de las estaciones del AMVA: datos.gov.co, conjunto `g4t8-zkc3` (SISAIRE-IDEAM, autoridad ambiental AMVA).
- Se usan solo 2024-2025. En 2020-2023 las magnitudes de PM2.5, lluvia y viento están inflados y con escalas distintas por estación (medianas de PM2.5 de 44 a 215 frente a 13-16 en 2024-2025), por lo que se descartaron.
- Corpus del RAG: informes diarios y mensuales de SIATA y un diagnóstico de calidad del aire de la Alcaldía de Medellín (carpeta `docs/`, lista en `src/descargar_docs.py`).
- Los datos procesados (`data/processed/diario.csv`) ya van en el repo; los crudos pesan unos 180 MB y no se suben.

## Cómo ejecutar
Requiere Python 3.10 o superior.

    pip install -r requirements.txt
    set LLM_API_KEY=tu_key_de_groq        (PowerShell: $env:LLM_API_KEY = "tu_key")
    streamlit run app.py

La API key es gratuita (console.groq.com) y también se puede pegar en la barra lateral de la app. Opcional: `LLM_MODEL` para cambiar de modelo y `LLM_BASE_URL` para otro proveedor compatible con OpenAI.

### Reproducir todo desde cero (opcional)

    python src/descargar.py        # datos crudos (varios minutos)
    python src/preparar.py         # limpieza y promedios diarios
    python src/modelo.py           # Naive Bayes, tabla de comparación
    python src/descargar_docs.py   # corpus
    python src/rag.py construir    # índice de búsqueda
    python evaluar.py              # evaluación del agente (12 preguntas)

## Parte 1: modelo clásico
Naive Bayes Gaussiano escrito con numpy (sin sklearn) que predice la categoría del día siguiente: Buena (<=12), Aceptable (12-37) y Alta (>37 ug/m3, norma diaria). Validación temporal en dos cortes, comparado contra persistencia ("mañana igual que hoy") y contra la clase mayoritaria. Resultados en `resultados/comparacion.csv`.

| Corte | Modelo | Accuracy | F1 macro |
|---|---|---|---|
| 2024 -> 1S 2025 | Persistencia | 0.818 | 0.557 |
| 2024 -> 1S 2025 | Naive Bayes | 0.765 | 0.522 |
| hasta 1S 2025 -> 2S 2025 | Persistencia | 0.753 | 0.744 |
| hasta 1S 2025 -> 2S 2025 | Naive Bayes | 0.725 | 0.725 |

Naive Bayes no supera a la persistencia en ningún corte. La clase Alta tiene muy pocos días en la validación (6 y 0), así que su recall no es interpretable.

## Agente y RAG
Loop agéntico manual con máximo de 5 pasos; los errores de las herramientas se devuelven como observación. RAG con búsqueda TF-IDF (numpy) sobre fichas de PDFs, que cita archivo y página. Evaluación con 12 preguntas fijas en `resultados/` (tres corridas; v1 11/12, v2 9/12, v3 12/12 en herramienta correcta).

## Limitaciones
- Los datos medidos terminan el 31 de diciembre de 2025, así que "mañana" es el día siguiente a esa fecha, no el día actual.
- El modelo no supera a la línea base de persistencia.
- La revisión de citas se hizo con una regla automática sencilla y se revisó a mano.

## Uso de IA generativa
Ver `DECLARACION_IA.md`.
