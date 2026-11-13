import io, os, time
import pandas as pd
import requests

URL = "https://www.datos.gov.co/resource/g4t8-zkc3.csv"
COLS = "estacion_id,nombre_est,municipio,latitud,longitud,msfl_code,med_concentracion_estandar,med_fecha_inicio"
PAGINA = 50000
VARIABLES = {"PM2.5": "pm25", "PLiquida": "lluvia", "VViento": "viento"}

os.makedirs("data", exist_ok=True)

def pedir(params):
    for intento in range(5):
        try:
            r = requests.get(URL, params=params, timeout=180)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"  reintento {intento + 1}: {e}")
            time.sleep(5)
    raise RuntimeError("No se pudo descargar la página")

for codigo, nombre in VARIABLES.items():
    destino = f"data/raw_{nombre}.csv"
    if os.path.exists(destino):
        print(f"{destino} ya existe, se omite")
        continue
    print(f"Descargando {codigo}...")
    tmp = destino + ".tmp"
    offset, total = 0, 0
    while True:
        params = {
            "$select": COLS,
            "$where": f"nombre_fgda='AMVA' AND msfl_code='{codigo}'",
            "$order": ":id",
            "$limit": PAGINA,
            "$offset": offset,
        }
        df = pd.read_csv(io.StringIO(pedir(params)))
        if df.empty:
            break
        df.to_csv(tmp, mode="a", header=(offset == 0), index=False)
        offset += PAGINA
        total += len(df)
        print(f"  {total} filas")
    os.replace(tmp, destino)
    print(f"Listo: {destino} ({total} filas)")
