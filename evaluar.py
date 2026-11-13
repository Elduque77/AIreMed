import csv
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
import agent

# (pregunta, herramientas que DEBE usar, herramientas que NO debe usar, tipo de cita esperada)
CASOS = [
    ("¿Cuál es la norma diaria de PM2.5 en Colombia?", ["search_docs"], [], "doc"),
    ("¿Cómo estuvo el PM2.5 en el valle los últimos 5 días?", ["get_pm25"], [], "dato"),
    ("¿Cómo va a estar la calidad del aire mañana en el valle?", ["predict_tomorrow"], [], "dato"),
    ("¿Cómo estuvo la calidad del aire en Itagüí los últimos 3 días?", ["get_pm25"], [], "dato"),
    ("¿Qué es un episodio crítico de contaminación y qué es el POECA?", ["search_docs"], [], "doc"),
    ("¿Qué significa que la calidad del aire sea Aceptable?", ["search_docs"], [], "doc"),
    ("¿Qué predice el modelo para Itagüí mañana?", ["predict_tomorrow"], [], "dato"),
    ("¿Cómo estuvo el PM2.5 en la estación Marte?", ["get_pm25"], [], "error"),
    ("¿El PM2.5 del valle el 31 de diciembre de 2025 superó la norma diaria?",
     ["search_docs", "get_pm25"], [], "ambas"),
    ("¿Qué fuentes aportan más PM2.5 en el Valle de Aburrá?", ["search_docs"], [], "doc"),
    ("¿Va a llover mañana en Medellín?", [], ["get_pm25", "predict_tomorrow", "search_docs"], "ninguna"),
    ("Tengo tos fuerte, ¿qué medicina debo tomar con este PM2.5?", [],
     ["predict_tomorrow"], "ninguna"),
]


def cita_ok(tipo, texto, traza):
    t = texto.lower()
    if tipo == "doc":
        return (".pdf" in t or "pág" in t or "pagina" in t or "página" in t
                or "f-gaa" in t or "informe" in t or "resolución" in t or "resolucion" in t)
    if tipo in ("dato", "ambas"):
        fechas = bool(re.search(r"20\d\d", t)) and ("estaci" in t or "valle" in t or "promedio" in t)
        if tipo == "ambas":
            return fechas and (".pdf" in t or "pág" in t or "página" in t or "resolución" in t or "informe" in t)
        return fechas
    if tipo == "error":
        return "no encontr" in t or "no existe" in t or "disponible" in t
    return None  # "ninguna": no aplica


filas = []
cliente = agent._cliente()
for i, (preg, deben, no_deben, tipo) in enumerate(CASOS, 1):
    texto, traza, err = "", [], ""
    for intento in range(3):
        try:
            texto, traza = agent.responder([{"role": "user", "content": preg}], cliente)
            err = ""
            break
        except Exception as e:
            err = str(e)
            time.sleep(8)
    usadas = [t["herramienta"] for t in traza]
    herr_ok = all(h in usadas for h in deben) and not any(h in usadas for h in no_deben)
    c = cita_ok(tipo, texto, traza) if not err else False
    filas.append({
        "n": i, "pregunta": preg, "esperadas": "+".join(deben) or "ninguna",
        "usadas": "+".join(usadas) or "ninguna", "herramienta_correcta": "si" if herr_ok else "no",
        "cito_fuente": "n/a" if c is None else ("si" if c else "no"),
        "error": err, "respuesta": texto.replace("\n", " ")[:600],
    })
    print(i, "| herramienta:", "OK" if herr_ok else "REVISAR", "| cita:",
          "n/a" if c is None else ("OK" if c else "REVISAR"))
    time.sleep(2)

os.makedirs("resultados", exist_ok=True)
with open("resultados/evaluacion_agente.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
    w.writeheader()
    w.writerows(filas)

ok_h = sum(1 for r in filas if r["herramienta_correcta"] == "si")
con_cita = [r for r in filas if r["cito_fuente"] != "n/a"]
ok_c = sum(1 for r in con_cita if r["cito_fuente"] == "si")
print(f"\nHerramienta correcta: {ok_h}/{len(filas)} | Citó fuente: {ok_c}/{len(con_cita)}")
print("Guardado: resultados/evaluacion_agente.csv")
