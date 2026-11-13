import os
import requests

URLS = [
    "https://siata.gov.co/CalidadAire/InformesDiarios/Informe_AMVA_08082026.pdf",
    "https://siata.gov.co/CalidadAire/InformesDiarios/Informe_AMVA_28072026.pdf",
    "https://siata.gov.co/CalidadAire/InformesDiarios/Informe_AMVA_24042026.pdf",
    "https://siata.gov.co/CalidadAire/InformesDiarios/Informe_AMVA_25012026.pdf",
    "https://siata.gov.co/CalidadAire/InformesDiarios/Informe_AMVA_05052025.pdf",
    "https://siata.gov.co/CalidadAire/InformesDiarios/Informe_AMVA_16022025.pdf",
    "https://siata.gov.co/CalidadAire/Informe_Procuraduria/F-GAA-RA-82_InformeProcuraduria_Octubre2024.pdf",
    "https://siata.gov.co/CalidadAire/Informe_Procuraduria/F-GAA-RA-82_InformeProcuraduria_Enero2025.pdf",
    "https://www.medellin.gov.co/es/wp-content/uploads/2026/09/Anexo-15_DiagnosticoMedioTransformado-1.pdf",
]

os.makedirs("docs", exist_ok=True)
for u in URLS:
    destino = os.path.join("docs", u.split("/")[-1])
    if os.path.exists(destino):
        print("ya existe:", destino)
        continue
    try:
        r = requests.get(u, timeout=120, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        open(destino, "wb").write(r.content)
        print("ok:", destino)
    except Exception as e:
        print("FALLO:", u, e)
