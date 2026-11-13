import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import pandas as pd
import plotly.express as px
import streamlit as st

import agent
import tools

st.set_page_config(page_title="Calidad del aire - Valle de Aburrá", layout="wide")


@st.cache_data
def cargar():
    return pd.read_csv("data/processed/diario.csv", parse_dates=["fecha"])


df = cargar()
VALLE = "Valle de Aburrá (promedio)"

st.title("Calidad del aire en el Valle de Aburrá")
st.caption("Datos reales: SISAIRE-IDEAM vía datos.gov.co (autoridad AMVA), 2024-2025. "
           "Herramienta analítica: no es consejo médico, legal ni de seguridad.")

# ---------- Barra lateral: parámetros ----------
with st.sidebar:
    st.header("Parámetros")
    estaciones = [VALLE] + sorted(df["nombre_est"].unique().tolist())
    estacion = st.selectbox("Estación", estaciones)
    fmin, fmax = df["fecha"].min().date(), df["fecha"].max().date()
    fecha = st.date_input("Fecha (para el mapa)", value=fmax, min_value=fmin, max_value=fmax)
    dias = st.slider("Días en la serie de tiempo", 7, 180, 60)
    st.divider()
    key = st.text_input("API key del LLM (Groq)", type="password",
                        value=os.getenv("LLM_API_KEY", ""))
    if key:
        os.environ["LLM_API_KEY"] = key

fecha = pd.Timestamp(fecha)

# ---------- Mapa y serie ----------
c1, c2 = st.columns(2)

with c1:
    st.subheader(f"Mapa de estaciones: {fecha.date()}")
    dia = df[df["fecha"] == fecha]
    if dia.empty:
        st.info("No hay mediciones para esa fecha.")
    else:
        args = dict(lat="latitud", lon="longitud", color="pm25", hover_name="nombre_est",
                    hover_data={"municipio": True, "pm25": ":.1f", "latitud": False, "longitud": False},
                    color_continuous_scale="RdYlGn_r", range_color=(0, 40), zoom=10, height=430)
        if hasattr(px, "scatter_map"):
            fig = px.scatter_map(dia, **args)
        else:
            fig = px.scatter_mapbox(dia, mapbox_style="open-street-map", **args)
        fig.update_traces(marker=dict(size=14))
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), coloraxis_colorbar_title="PM2.5")
        st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader(f"PM2.5 diario: {estacion}")
    sub = df if estacion == VALLE else df[df["nombre_est"] == estacion]
    s = sub.groupby("fecha")["pm25"].mean().reset_index()
    s = s[s["fecha"] <= fecha].tail(dias)
    fig2 = px.line(s, x="fecha", y="pm25", labels={"pm25": "PM2.5 (µg/m³)", "fecha": ""}, height=430)
    fig2.add_hline(y=37, line_dash="dash", line_color="red", annotation_text="Norma diaria 37")
    fig2.add_hline(y=12, line_dash="dot", line_color="green", annotation_text="Límite Buena 12")
    st.plotly_chart(fig2, use_container_width=True)

# ---------- Predicción ----------
st.subheader("Predicción del día siguiente a la última fecha con datos")
p = tools.predict_tomorrow("valle" if estacion == VALLE else estacion)
if "error" in p:
    st.warning(p["error"])
else:
    a, b, c = st.columns(3)
    a.metric("Fecha base de los datos", p["fecha_base"])
    b.metric("PM2.5 base (µg/m³)", p["pm25_base"])
    c.metric("Categoría prevista", p["prediccion_dia_siguiente"])
    st.write("Probabilidades:", p["probabilidades"])
    st.caption("Modelo Naive Bayes hecho a mano. No supera a la línea base 'mañana igual que hoy'; "
               "úsalo como apoyo, no como pronóstico oficial. Los datos terminan en 2025.")

# ---------- Chat con el agente ----------
st.divider()
st.subheader("Pregúntale al agente")
st.caption("Ejemplos: ¿Qué significa que el PM2.5 sea 'Aceptable'? · ¿Cómo estuvo Itagüí? · ¿Qué dice la norma?")

if "msgs" not in st.session_state:
    st.session_state.msgs = []

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("traza"):
            with st.expander("Herramientas usadas"):
                for t in m["traza"]:
                    st.write(f"**{t['herramienta']}**", t["args"])

pregunta = st.chat_input("Escribe tu pregunta")
if pregunta:
    st.session_state.msgs.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)
    with st.chat_message("assistant"):
        try:
            hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.msgs[-10:]]
            with st.spinner("Consultando..."):
                texto, traza = agent.responder(hist)
        except Exception as e:
            texto, traza = f"No pude responder: {e}", []
        st.markdown(texto)
        if traza:
            with st.expander("Herramientas usadas"):
                for t in traza:
                    st.write(f"**{t['herramienta']}**", t["args"])
    st.session_state.msgs.append({"role": "assistant", "content": texto, "traza": traza})
