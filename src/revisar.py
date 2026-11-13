import pandas as pd

for nombre in ["pm25", "lluvia", "viento"]:
    df = pd.read_csv(f"data/raw_{nombre}.csv", parse_dates=["med_fecha_inicio"])
    df["anio"] = df["med_fecha_inicio"].dt.year
    v = df["med_concentracion_estandar"]
    print(f"\n=== {nombre.upper()} ===")
    print("nulos:", v.isna().sum(), "| negativos:", (v < 0).sum())
    print(df.groupby("anio")["med_concentracion_estandar"]
            .describe(percentiles=[0.5, 0.99])[["count", "50%", "99%", "max"]]
            .round(2).to_string())
