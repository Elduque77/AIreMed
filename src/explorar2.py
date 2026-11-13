import requests, pandas as pd
base = "https://www.datos.gov.co/resource/g4t8-zkc3.json"
p = {
    "$select": "nombre_fgda,msfl_code,sigla_unidad,count(*) as n",
    "$group": "nombre_fgda,msfl_code,sigla_unidad",
    "$limit": 5000,
}
df = pd.DataFrame(requests.get(base, params=p, timeout=180).json())
print(df["nombre_fgda"].unique())
print(df[df["nombre_fgda"].str.contains("AMVA|ABURR", case=False, na=False)].to_string())
