import os
import pandas as pd

os.makedirs("data/processed", exist_ok=True)
DESDE = "2024-01-01"
MIN_HORAS = 18  # un dia cuenta solo si tiene al menos 18 horas validas

def cargar(nombre):
    df = pd.read_csv(f"data/raw_{nombre}.csv", parse_dates=["med_fecha_inicio"])
    df = df[df["med_fecha_inicio"] >= DESDE].copy()
    df = df.drop_duplicates(["estacion_id", "med_fecha_inicio"])
    df["fecha"] = df["med_fecha_inicio"].dt.normalize()
    return df.rename(columns={"med_concentracion_estandar": "valor"})

# PM2.5 por estacion y dia
pm = cargar("pm25")
pm = pm[(pm["valor"] >= 0) & (pm["valor"] <= 500)]
est = pm.groupby("estacion_id").agg(
    nombre_est=("nombre_est", "first"), municipio=("municipio", "first"),
    latitud=("latitud", "first"), longitud=("longitud", "first")).reset_index()
d = pm.groupby(["estacion_id", "fecha"]).agg(
    pm25=("valor", "mean"), horas=("valor", "size")).reset_index()
d = d[d["horas"] >= MIN_HORAS].drop(columns="horas")

# Lluvia y viento: diario por estacion, luego promedio del valle por dia
llu = cargar("lluvia")
llu = llu[(llu["valor"] >= 0) & (llu["valor"] <= 200)]
llu = llu.groupby(["estacion_id", "fecha"]).agg(v=("valor", "sum"), h=("valor", "size")).reset_index()
lluvia = llu[llu["h"] >= MIN_HORAS].groupby("fecha")["v"].mean().rename("lluvia_mm")

vie = cargar("viento")
vie = vie[(vie["valor"] >= 0) & (vie["valor"] <= 40)]
vie = vie.groupby(["estacion_id", "fecha"]).agg(v=("valor", "mean"), h=("valor", "size")).reset_index()
viento = vie[vie["h"] >= MIN_HORAS].groupby("fecha")["v"].mean().rename("viento_ms")

d = d.merge(est, on="estacion_id").merge(lluvia, on="fecha", how="left").merge(viento, on="fecha", how="left")

# Categoria segun el limite de 37 ug/m3 de la norma diaria; verifica los demas cortes con la Resolucion 2254 de 2017
CORTES = [-1, 12, 37, 55, 10000]
NOMBRES = ["Buena", "Aceptable", "Danina_sensibles", "Danina"]
d["categoria"] = pd.cut(d["pm25"], bins=CORTES, labels=NOMBRES)

d = d.sort_values(["estacion_id", "fecha"])
d.to_csv("data/processed/diario.csv", index=False)

print("filas:", len(d), "| estaciones:", d["estacion_id"].nunique())
print("fechas:", d["fecha"].min().date(), "a", d["fecha"].max().date())
print("dias sin lluvia/viento:", d["lluvia_mm"].isna().sum(), "/", d["viento_ms"].isna().sum())
print(d["categoria"].value_counts())
print(d[["pm25", "lluvia_mm", "viento_ms"]].describe().round(2).to_string())
