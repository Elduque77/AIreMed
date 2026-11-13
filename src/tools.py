import json
import os
import sys
import unicodedata

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rag

_DF = None
_MODELO = None
CORTES = [12, 37]
NOMBRES = ["Buena", "Aceptable", "Alta"]


def _norm(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _datos():
    global _DF
    if _DF is None:
        _DF = pd.read_csv("data/processed/diario.csv", parse_dates=["fecha"])
    return _DF


def _categoria(pm):
    return NOMBRES[0] if pm <= CORTES[0] else (NOMBRES[1] if pm <= CORTES[1] else NOMBRES[2])


def listar_estaciones():
    return sorted(_datos()["nombre_est"].unique().tolist())


def _serie(estacion):
    d = _datos()
    q = _norm(estacion)
    if q in ("", "valle", "valle de aburra", "todas", "promedio"):
        sub, nombres = d, ["Valle de Aburra (promedio)"]
    else:
        m = d["nombre_est"].map(_norm).str.contains(q, regex=False)
        if not m.any():
            m = d["municipio"].map(_norm).str.contains(q, regex=False)
        if not m.any():
            return None, None
        sub = d[m]
        nombres = sorted(sub["nombre_est"].unique().tolist())
    s = sub.groupby("fecha")[["pm25", "lluvia_mm", "viento_ms"]].mean().reset_index().sort_values("fecha")
    return nombres, s


def get_pm25(estacion="valle", dias=7):
    try:
        dias = max(1, min(int(dias), 60))
        nombres, s = _serie(estacion)
        if s is None:
            return {"error": f"No encontre la estacion '{estacion}'.", "estaciones_disponibles": listar_estaciones()}
        ult = s.tail(dias)
        return {"estaciones": nombres, "ultimo_dato": str(s["fecha"].max().date()),
                "norma_diaria_ug_m3": 37,
                "dias": [{"fecha": str(r.fecha.date()), "pm25": round(float(r.pm25), 1),
                          "categoria": _categoria(r.pm25)} for r in ult.itertuples()]}
    except Exception as e:
        return {"error": str(e)}


def predict_tomorrow(estacion="valle"):
    global _MODELO
    try:
        if _MODELO is None:
            _MODELO = json.load(open("models/nb.json"))
        M = _MODELO
        nombres, s = _serie(estacion)
        if s is None:
            return {"error": f"No encontre la estacion '{estacion}'.", "estaciones_disponibles": listar_estaciones()}
        if len(s) < 2:
            return {"error": "No hay suficientes dias para predecir."}
        hoy, ayer = s.iloc[-1], s.iloc[-2]
        if (hoy["fecha"] - ayer["fecha"]).days != 1:
            return {"error": "Los ultimos dos dias de datos no son consecutivos."}
        f = {"pm25": hoy["pm25"], "pm25_ayer": ayer["pm25"], "lluvia_mm": hoy["lluvia_mm"],
             "viento_ms": hoy["viento_ms"], "delta": hoy["pm25"] - ayer["pm25"],
             "lluvia_ayer": ayer["lluvia_mm"]}
        x = np.array([f[c] if not pd.isna(f[c]) else M["relleno"][c] for c in M["features"]], dtype=float)
        prior, media, var = np.array(M["prior"]), np.array(M["media"]), np.array(M["var"])
        lp = np.log(prior) + (-0.5 * np.log(2 * np.pi * var) - (x - media) ** 2 / (2 * var)).sum(axis=1)
        p = np.exp(lp - lp.max())
        p = p / p.sum()
        probs = {NOMBRES[c]: round(float(v), 3) for c, v in zip(M["clases_idx"], p)}
        return {"estaciones": nombres, "fecha_base": str(hoy["fecha"].date()),
                "pm25_base": round(float(hoy["pm25"]), 1),
                "prediccion_dia_siguiente": max(probs, key=probs.get), "probabilidades": probs,
                "advertencia": "Modelo Naive Bayes de baja exactitud; herramienta analitica, no consejo medico."}
    except Exception as e:
        return {"error": str(e)}


def search_docs(consulta, k=4):
    try:
        return {"resultados": rag.buscar(consulta, max(1, min(int(k), 6)))}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print(json.dumps(get_pm25("valle", 3), ensure_ascii=False, indent=1))
    print(json.dumps(predict_tomorrow("valle"), ensure_ascii=False, indent=1))
    print(json.dumps(search_docs("que hacer en episodio critico de contaminacion", 2), ensure_ascii=False, indent=1)[:900])
