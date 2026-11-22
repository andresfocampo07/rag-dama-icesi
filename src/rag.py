"""Recuperación y generación: el núcleo del RAG.

Uso desde la terminal:
    python src/rag.py "¿Qué es un data steward según DAMA?"
    python src/rag.py "¿Qué dice la Ley 1581 sobre la autorización?" --min-dama 0
"""
import argparse
import time

import config
import ollama_cliente

ETIQUETAS_CAPA = {
    "A": "DAMA-DMBOK2",
    "B": "Guía colombiana (MinTIC/DANE)",
    "C": "Normativa colombiana",
    "D": "Referente de otra institución",
    "E": "Marco complementario",
    "F": "Documento de la Universidad Icesi",
}

PROMPT_SISTEMA = f"""Eres el asistente del equipo de gobierno de datos de la Universidad Icesi.
Respondes preguntas sobre gobierno y gestión de datos según la metodología DAMA-DMBOK2
y los documentos relacionados, usando SOLO los fragmentos de contexto que se te entregan.

Reglas:
1. Usa únicamente la información de los fragmentos. No agregues conocimiento propio.
2. Cita cada afirmación con la etiqueta del fragmento entre corchetes, por ejemplo [A2_12] o [C1, p. 3].
3. Indica de qué tipo de fuente viene cada idea: DAMA-DMBOK2, guías colombianas (MinTIC, DANE),
   normativa (leyes, decretos, SIC), otras instituciones o documentos de la Universidad Icesi.
   Si la pregunta es sobre DAMA, prioriza los fragmentos de DAMA-DMBOK2 y no presentes como
   DAMA lo que dice otra fuente.
4. Los fragmentos de DAMA-DMBOK2 están en inglés. Responde siempre en español; puedes poner
   entre paréntesis el término original en inglés.
5. Si los fragmentos no contienen la respuesta, responde exactamente:
   "{config.FRASE_ABSTENCION}"
   y no agregues nada más.
6. Sé concreto: máximo 250 palabras. Usa viñetas cuando enumeres."""

_coleccion = None


def coleccion():
    global _coleccion
    if _coleccion is None:
        import chromadb
        cliente = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
        try:
            _coleccion = cliente.get_collection(config.COLECCION)
        except Exception as e:
            raise RuntimeError(
                f"No existe la colección '{config.COLECCION}' en {config.CHROMA_DIR}. "
                "Ejecuta primero: python src/ingesta.py"
            ) from e
    return _coleccion


def cita(meta):
    if meta.get("pagina"):
        return f"{meta['id_doc']}, p. {meta['pagina']}"
    return meta["id_doc"]


def _consultar(vector, n, where=None):
    col = coleccion()
    n = min(n, col.count())
    if n <= 0:
        return []
    res = col.query(query_embeddings=[vector], n_results=n, where=where,
                    include=["documents", "metadatas", "distances"])
    return [
        {"id": i, "documento": d, "metadatos": m, "distancia": round(dist, 4), "cita": cita(m)}
        for i, d, m, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]


def recuperar(pregunta, k=None, min_dama=None, capas=None):
    """Devuelve los k fragmentos más parecidos, garantizando al menos `min_dama` de la capa A."""
    k = k or config.K
    min_dama = config.MIN_DAMA if min_dama is None else min_dama
    vector = ollama_cliente.embeddings([pregunta])[0]
    where = None
    if capas:
        where = {"capa": capas[0]} if len(capas) == 1 else {"capa": {"$in": list(capas)}}
    fragmentos = _consultar(vector, k, where)

    if min_dama > 0 and (not capas or "A" in capas):
        n_dama = sum(f["metadatos"]["capa"] == "A" for f in fragmentos)
        if n_dama < min_dama:
            ids = {f["id"] for f in fragmentos}
            extra = [f for f in _consultar(vector, min_dama, {"capa": "A"}) if f["id"] not in ids]
            extra = extra[:min_dama - n_dama]
            if extra:
                # se reemplazan los fragmentos no-DAMA menos parecidos
                no_dama = [f for f in fragmentos if f["metadatos"]["capa"] != "A"]
                quitar = {f["id"] for f in no_dama[-len(extra):]} if len(fragmentos) >= k else set()
                fragmentos = [f for f in fragmentos if f["id"] not in quitar] + extra
                fragmentos.sort(key=lambda f: f["distancia"])
    return fragmentos


def construir_contexto(fragmentos):
    bloques = []
    for f in fragmentos:
        tipo = ETIQUETAS_CAPA.get(f["metadatos"]["capa"], "Otra fuente")
        bloques.append(f"[{f['cita']}] (Tipo de fuente: {tipo})\n{f['documento']}")
    return "\n\n---\n\n".join(bloques)


def generar(pregunta, fragmentos):
    if not fragmentos:
        return config.FRASE_ABSTENCION
    mensajes = [
        {"role": "system", "content": PROMPT_SISTEMA},
        {"role": "user", "content": f"Fragmentos de contexto:\n\n{construir_contexto(fragmentos)}\n\n"
                                    f"Pregunta: {pregunta}"},
    ]
    return ollama_cliente.chat(mensajes)


def responder(pregunta, k=None, min_dama=None, capas=None):
    inicio = time.time()
    fragmentos = recuperar(pregunta, k=k, min_dama=min_dama, capas=capas)
    t_rec = time.time() - inicio
    respuesta = generar(pregunta, fragmentos)
    return {
        "pregunta": pregunta,
        "respuesta": respuesta,
        "fragmentos": fragmentos,
        "segundos_recuperacion": round(t_rec, 2),
        "segundos_total": round(time.time() - inicio, 2),
    }


def main():
    ap = argparse.ArgumentParser(description="Pregunta al RAG de gobierno de datos")
    ap.add_argument("pregunta")
    ap.add_argument("--k", type=int, default=config.K)
    ap.add_argument("--min-dama", type=int, default=config.MIN_DAMA)
    args = ap.parse_args()
    r = responder(args.pregunta, k=args.k, min_dama=args.min_dama)
    print("\n" + r["respuesta"] + "\n")
    print(f"Fuentes ({r['segundos_total']} s):")
    for f in r["fragmentos"]:
        m = f["metadatos"]
        print(f"  [{f['cita']}] capa {m['capa']} · distancia {f['distancia']} · {m['titulo'][:70]}")


if __name__ == "__main__":
    main()
