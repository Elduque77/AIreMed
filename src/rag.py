import glob
import json
import os
import re
import sys
import unicodedata

import numpy as np

MODELO = "paraphrase-multilingual-MiniLM-L12-v2"
_modelo = None
_chunks = None
_modo = None
_M = None
_vocab = None
_idf = None


def _emb(textos):
    global _modelo
    from sentence_transformers import SentenceTransformer
    if _modelo is None:
        _modelo = SentenceTransformer(MODELO)
        _modelo.max_seq_length = 256
    v = _modelo.encode(textos, normalize_embeddings=True, show_progress_bar=False, batch_size=32)
    return np.asarray(v, dtype="float32")


def _tokens(t):
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return [w for w in re.findall(r"[a-z0-9]+", t) if len(w) >= 2]


def _trozos(texto, tam=700, solape=120):
    texto = " ".join(texto.split())
    out, i = [], 0
    while i < len(texto):
        out.append(texto[i:i + tam])
        i += tam - solape
    return [t for t in out if len(t) > 80]


def _tfidf_matriz(chunks):
    global _vocab, _idf
    docs = [_tokens(c["texto"]) for c in chunks]
    df = {}
    for d in docs:
        for w in set(d):
            df[w] = df.get(w, 0) + 1
    _vocab = {w: i for i, w in enumerate(df)}
    n = len(docs)
    _idf = np.array([np.log((1 + n) / (1 + df[w])) + 1 for w in _vocab], dtype="float32")
    M = np.zeros((n, len(_vocab)), dtype="float32")
    for i, d in enumerate(docs):
        for w in d:
            M[i, _vocab[w]] += 1
    M = np.log1p(M) * _idf
    M /= (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)
    return M


def construir():
    from pypdf import PdfReader
    chunks = []
    for ruta in sorted(glob.glob("docs/*")):
        nombre = os.path.basename(ruta)
        if ruta.lower().endswith(".pdf"):
            try:
                lector = PdfReader(ruta)
            except Exception as e:
                print("omitido", nombre, e)
                continue
            for n, pag in enumerate(lector.pages, 1):
                try:
                    txt = pag.extract_text() or ""
                except Exception:
                    txt = ""
                for t in _trozos(txt):
                    chunks.append({"fuente": nombre, "pagina": n, "texto": t})
        elif ruta.lower().endswith((".txt", ".md")):
            txt = open(ruta, encoding="utf-8").read()
            for t in _trozos(txt):
                chunks.append({"fuente": nombre, "pagina": None, "texto": t})
    print("fichas:", len(chunks))
    os.makedirs("index", exist_ok=True)
    json.dump(chunks, open("index/chunks.json", "w", encoding="utf-8"), ensure_ascii=False)
    if os.path.exists("index/emb.npy"):
        os.remove("index/emb.npy")
    try:
        np.save("index/emb.npy", _emb([c["texto"] for c in chunks]))
        print("indice semantico guardado en index/")
    except Exception as e:
        print("sin embeddings (", type(e).__name__, "); se usara busqueda TF-IDF")


def _cargar():
    global _chunks, _modo, _M
    _chunks = json.load(open("index/chunks.json", encoding="utf-8"))
    if os.path.exists("index/emb.npy"):
        try:
            _M = np.load("index/emb.npy")
            _emb(["prueba"])
            _modo = "semantico"
            return
        except Exception:
            pass
    _M = _tfidf_matriz(_chunks)
    _modo = "tfidf"


def buscar(consulta, k=4):
    if _modo is None:
        _cargar()
    if _modo == "semantico":
        scores = _M @ _emb([consulta])[0]
    else:
        q = np.zeros(len(_vocab), dtype="float32")
        for w in _tokens(consulta):
            if w in _vocab:
                q[_vocab[w]] += 1
        q = np.log1p(q) * _idf
        q /= (np.linalg.norm(q) + 1e-9)
        scores = _M @ q
    top = np.argsort(-scores)[:k]
    return [{"fuente": _chunks[i]["fuente"], "pagina": _chunks[i]["pagina"],
             "texto": _chunks[i]["texto"], "score": round(float(scores[i]), 3)} for i in top]


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "construir":
        construir()
    else:
        for r in buscar("norma diaria de PM2.5 en Colombia"):
            print(r["fuente"], r["pagina"], r["score"])
            print(r["texto"][:200], "\n")
        print("modo:", _modo)
