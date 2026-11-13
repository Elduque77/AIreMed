import re

ruta = "src/agent.py"
t = open(ruta, encoding="utf-8").read()

a1 = "for _ in range(T_MAX):"
b1 = "for paso in range(T_MAX):"
a2 = "r = cliente.chat.completions.create(model=MODELO, messages=msgs, tools=TOOLS, temperature=0.2)"
b2 = ("modo = 'none' if paso == T_MAX - 1 else 'auto'\n"
      "        r = cliente.chat.completions.create(model=MODELO, messages=msgs, tools=TOOLS, tool_choice=modo, temperature=0.2)")
a3 = "3. La norma diaria nacional de PM2.5 es 37 ug/m3 solo si lo confirmas con search_docs o get_pm25."
b3 = ("3. Para cualquier pregunta sobre normas, limites o categorias, usa search_docs y cita el documento y la pagina; "
      "el campo norma_diaria_ug_m3 de get_pm25 es solo de apoyo. "
      "Usa como maximo 2 busquedas con search_docs por pregunta y luego responde con lo que tengas.")

for a, b in [(a1, b1), (a2, b2), (a3, b3)]:
    assert a in t, "No encontre este texto en agent.py: " + a
    t = t.replace(a, b)

open(ruta, "w", encoding="utf-8").write(t)
print("agent.py actualizado")
