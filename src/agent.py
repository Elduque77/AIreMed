import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tools
from openai import OpenAI

BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
MODELO = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
T_MAX = 5

SYSTEM = """Eres un asistente de calidad del aire del Valle de Aburra (Colombia).
Reglas:
1. Para datos de PM2.5 usa la herramienta get_pm25. Para el dia siguiente usa predict_tomorrow.
   Para normativa, protocolos, significado de las categorias y recomendaciones usa search_docs.
   No inventes cifras ni normas: si no lo obtuviste de una herramienta, dilo.
2. Cita siempre la fuente: para documentos, el archivo y la pagina; para datos, la estacion y la fecha.
3. Para cualquier pregunta sobre normas, limites o categorias, usa search_docs y cita el documento y la pagina; el campo norma_diaria_ug_m3 de get_pm25 es solo de apoyo. Usa como maximo 2 busquedas con search_docs por pregunta y luego responde con lo que tengas.
4. Si una herramienta devuelve un error, explicalo y prueba otra opcion (por ejemplo, otro nombre de estacion).
5. La prediccion viene de un modelo Naive Bayes de baja exactitud (no supera a 'manana igual que hoy'); mencionalo.
6. Los datos medidos terminan en la fecha 'ultimo_dato' que devuelven las herramientas (31 de diciembre de 2025). Aclara siempre esa fecha: 'dia siguiente' significa el dia despues de la fecha base de los datos, no el dia de hoy.
7. Eres una herramienta analitica, no das consejo medico, legal ni de seguridad. Para temas de salud, remite a fuentes oficiales.
8. Responde en espanol, claro y breve."""

TOOLS = [
    {"type": "function", "function": {
        "name": "get_pm25",
        "description": "Devuelve el PM2.5 diario reciente (ug/m3) y su categoria para una estacion, municipio o el valle completo.",
        "parameters": {"type": "object", "properties": {
            "estacion": {"type": "string", "description": "Nombre de estacion o municipio; 'valle' para el promedio de todas."},
            "dias": {"type": "integer", "description": "Cantidad de dias recientes (1 a 60)."}},
            "required": []}}},
    {"type": "function", "function": {
        "name": "predict_tomorrow",
        "description": "Predice la categoria de calidad del aire del dia siguiente a la fecha base (Buena, Aceptable, Alta) con probabilidades.",
        "parameters": {"type": "object", "properties": {
            "estacion": {"type": "string", "description": "Nombre de estacion o municipio; 'valle' para el promedio."}},
            "required": []}}},
    {"type": "function", "function": {
        "name": "search_docs",
        "description": "Busca en los documentos oficiales (informes de SIATA, normativa) y devuelve fragmentos con archivo y pagina.",
        "parameters": {"type": "object", "properties": {
            "consulta": {"type": "string"},
            "k": {"type": "integer", "description": "Numero de fragmentos (1 a 6)."}},
            "required": ["consulta"]}}},
]

FUNCS = {"get_pm25": tools.get_pm25, "predict_tomorrow": tools.predict_tomorrow, "search_docs": tools.search_docs}


def _cliente():
    key = os.getenv("LLM_API_KEY")
    if not key:
        raise RuntimeError("Falta la variable de entorno LLM_API_KEY")
    return OpenAI(api_key=key, base_url=BASE_URL)


def responder(mensajes, cliente=None):
    """mensajes: lista de {'role': 'user'|'assistant', 'content': str}. Devuelve (texto, traza)."""
    cliente = cliente or _cliente()
    msgs = [{"role": "system", "content": SYSTEM}] + list(mensajes)
    traza = []
    for paso in range(T_MAX):
        if paso == T_MAX - 1:
            obs = "\n".join(f"[{x['herramienta']}] " + json.dumps(x['resultado'], ensure_ascii=False)[:1500] for x in traza)
            msgs2 = [{"role": "system", "content": SYSTEM}] + list(mensajes) + [{"role": "user", "content": "Resultados de herramientas ya obtenidos:\n" + obs + "\nYa no puedes usar herramientas. Responde ahora con esto, citando la fuente (archivo y pagina)."}]
            r = cliente.chat.completions.create(model=MODELO, messages=msgs2, temperature=0.2)
            return (r.choices[0].message.content or "").strip(), traza
        r = cliente.chat.completions.create(model=MODELO, messages=msgs, tools=TOOLS, temperature=0.2)
        m = r.choices[0].message
        if not m.tool_calls:
            return (m.content or "").strip(), traza
        msgs.append({"role": "assistant", "content": m.content or "",
                     "tool_calls": [{"id": tc.id, "type": "function",
                                     "function": {"name": tc.function.name,
                                                  "arguments": tc.function.arguments}} for tc in m.tool_calls]})
        for tc in m.tool_calls:
            nombre = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
                fn = FUNCS.get(nombre)
                res = fn(**args) if fn else {"error": f"Herramienta desconocida: {nombre}"}
            except Exception as e:
                args, res = {}, {"error": str(e)}
            traza.append({"herramienta": nombre, "args": args, "resultado": res})
            msgs.append({"role": "tool", "tool_call_id": tc.id,
                         "content": json.dumps(res, ensure_ascii=False)[:6000]})
    return "Llegue al maximo de pasos sin una respuesta final. Intenta reformular la pregunta.", traza


if __name__ == "__main__":
    pregunta = " ".join(sys.argv[1:]) or "Como estuvo el PM2.5 en el valle esta semana y que pasara manana?"
    texto, traza = responder([{"role": "user", "content": pregunta}])
    print("Herramientas usadas:", [t["herramienta"] for t in traza])
    print(texto)
