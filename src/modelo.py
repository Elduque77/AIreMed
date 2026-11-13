import json
import os
import numpy as np
import pandas as pd

CLASES = ["Buena", "Aceptable", "Alta"]


def etiquetar(pm):
    pm = np.asarray(pm, dtype=float)
    return np.where(pm <= 12, 0, np.where(pm <= 37, 1, 2))


class GaussianNB:
    def fit(self, X, y):
        self.clases = np.unique(y)
        self.prior = np.array([np.mean(y == c) for c in self.clases])
        self.media = np.array([X[y == c].mean(axis=0) for c in self.clases])
        self.var = np.array([X[y == c].var(axis=0) for c in self.clases]) + 1e-3
        return self

    def log_posterior(self, X):
        out = []
        for k in range(len(self.clases)):
            ll = -0.5 * np.log(2 * np.pi * self.var[k]) - (X - self.media[k]) ** 2 / (2 * self.var[k])
            out.append(np.log(self.prior[k]) + ll.sum(axis=1))
        return np.array(out).T

    def predict(self, X):
        return self.clases[np.argmax(self.log_posterior(X), axis=1)]


def resumen(y, p):
    m = np.zeros((3, 3), dtype=int)
    for a, b in zip(y, p):
        m[a, b] += 1
    acc = np.trace(m) / m.sum()
    f1s = []
    rec_alta = None
    for k in range(3):
        tp = m[k, k]
        fp = m[:, k].sum() - tp
        fn = m[k, :].sum() - tp
        prec = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * r / (prec + r) if prec + r else 0.0
        if m[k, :].sum() > 0:
            f1s.append(f1)
        if k == 2 and m[k, :].sum() > 0:
            rec_alta = round(float(r), 3)
    return {"accuracy": round(float(acc), 4), "f1_macro": round(float(np.mean(f1s)), 4),
            "recall_alta": rec_alta}


df = pd.read_csv("data/processed/diario.csv", parse_dates=["fecha"])
df = df.sort_values(["estacion_id", "fecha"])
g = df.groupby("estacion_id")
df["pm25_ayer"] = g["pm25"].shift(1)
df["lluvia_ayer"] = g["lluvia_mm"].shift(1)
df["fecha_ayer"] = g["fecha"].shift(1)
df["pm25_manana"] = g["pm25"].shift(-1)
df["fecha_manana"] = g["fecha"].shift(-1)
un_dia = pd.Timedelta(days=1)
ok = ((df["fecha"] - df["fecha_ayer"]) == un_dia) & ((df["fecha_manana"] - df["fecha"]) == un_dia)
df = df[ok].copy()
df["delta"] = df["pm25"] - df["pm25_ayer"]
df["y"] = etiquetar(df["pm25_manana"])
df["y_hoy"] = etiquetar(df["pm25"])

SETS = {
    "A": ["pm25", "pm25_ayer", "lluvia_mm", "viento_ms"],
    "B": ["pm25", "delta", "lluvia_mm", "lluvia_ayer", "viento_ms"],
    "C": ["pm25", "delta", "lluvia_mm", "lluvia_ayer", "viento_ms", "rel_estacion"],
}

FOLDS = [
    ("2024 -> 1S2025", df["fecha"] < "2024-12-31",
     (df["fecha"] >= "2025-01-01") & (df["fecha"] < "2025-06-30")),
    ("hasta 1S2025 -> 2S2025", df["fecha"] < "2025-06-30", df["fecha"] >= "2025-07-01"),
]


def preparar(train, test, feats):
    tr, te = train.copy(), test.copy()
    if "rel_estacion" in feats:
        me = tr.groupby("estacion_id")["pm25"].mean()
        for d in (tr, te):
            d["rel_estacion"] = (d["pm25"] - d["estacion_id"].map(me)).fillna(0.0)
    relleno = {c: float(tr[c].median()) for c in feats}
    tr[feats] = tr[feats].fillna(relleno)
    te[feats] = te[feats].fillna(relleno)
    return tr, te, relleno


filas = []
for nombre_fold, m_tr, m_te in FOLDS:
    train, test = df[m_tr], df[m_te]
    y = test["y"].values
    base = {"fold": nombre_fold, "n_test": len(test), "n_alta_test": int((y == 2).sum())}
    filas.append({**base, "modelo": "persistencia", **resumen(y, test["y_hoy"].values)})
    mayoria = np.full(len(test), int(train["y"].mode()[0]))
    filas.append({**base, "modelo": "mayoria", **resumen(y, mayoria)})
    for clave, feats in SETS.items():
        tr, te, _ = preparar(train, test, feats)
        nb = GaussianNB().fit(tr[feats].values, tr["y"].values)
        filas.append({**base, "modelo": "NB_" + clave, **resumen(y, nb.predict(te[feats].values))})

tabla = pd.DataFrame(filas)
print(tabla.to_string(index=False))

nb_tabla = tabla[tabla["modelo"].str.startswith("NB_")]
mejor = nb_tabla.groupby("modelo")["f1_macro"].mean().idxmax()
feats = SETS[mejor[3:]]
print("\nMejor conjunto (F1 macro promedio):", mejor, feats)

tr, _, relleno = preparar(df, df.head(5), feats)
nb = GaussianNB().fit(tr[feats].values, tr["y"].values)
modelo = {"features": feats, "clases": CLASES, "cortes": [12, 37],
          "clases_idx": [int(c) for c in nb.clases],
          "prior": nb.prior.tolist(), "media": nb.media.tolist(), "var": nb.var.tolist(),
          "relleno": relleno}
if "rel_estacion" in feats:
    modelo["media_estacion"] = {str(k): float(v) for k, v in df.groupby("estacion_id")["pm25"].mean().items()}
os.makedirs("models", exist_ok=True)
os.makedirs("resultados", exist_ok=True)
json.dump(modelo, open("models/nb.json", "w"), indent=2)
tabla.to_csv("resultados/comparacion.csv", index=False)
print("Guardado: models/nb.json y resultados/comparacion.csv")
