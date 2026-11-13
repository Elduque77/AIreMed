t = open("src/agent.py", encoding="utf-8").read()
a = ("modo = 'none' if paso == T_MAX - 1 else 'auto'\n"
     "        r = cliente.chat.completions.create(model=MODELO, messages=msgs, tools=TOOLS, tool_choice=modo, temperature=0.2)")
b = ("if paso == T_MAX - 1:\n"
     "            obs = \"\\n\".join(f\"[{x['herramienta']}] \" + json.dumps(x['resultado'], ensure_ascii=False)[:1500] for x in traza)\n"
     "            msgs2 = [{\"role\": \"system\", \"content\": SYSTEM}] + list(mensajes) + [{\"role\": \"user\", \"content\": \"Resultados de herramientas ya obtenidos:\\n\" + obs + \"\\nYa no puedes usar herramientas. Responde ahora con esto, citando la fuente (archivo y pagina).\"}]\n"
     "            r = cliente.chat.completions.create(model=MODELO, messages=msgs2, temperature=0.2)\n"
     "            return (r.choices[0].message.content or \"\").strip(), traza\n"
     "        r = cliente.chat.completions.create(model=MODELO, messages=msgs, tools=TOOLS, temperature=0.2)")
assert a in t, "No encontre el bloque en agent.py"
open("src/agent.py", "w", encoding="utf-8").write(t.replace(a, b))

e = open("evaluar.py", encoding="utf-8").read()
a2 = '["get_pm25", "predict_tomorrow"], "ninguna")'
assert a2 in e, "No encontre el caso 12 en evaluar.py"
open("evaluar.py", "w", encoding="utf-8").write(e.replace(a2, '["predict_tomorrow"], "ninguna")'))
print("parches aplicados")
