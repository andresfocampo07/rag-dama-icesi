"""Ingesta del corpus: extrae texto, fragmenta, calcula embeddings y carga en Chroma.

Uso (desde la carpeta raíz del proyecto):
    python src/ingesta.py                 # carga incremental (solo documentos nuevos o modificados)
    python src/ingesta.py --reconstruir   # borra la colección y la crea desde cero
    python src/ingesta.py --solo-extraer  # no usa Ollama ni Chroma: genera una vista previa de los fragmentos

Cómo se identifica cada documento:
  - El código al inicio del nombre del archivo (B1_..., C3_..., F1_...) es su `id_doc`
    y se busca en corpus_manifest.csv para obtener título, capa, área DAMA, etc.
  - Los .md con encabezado YAML (por ejemplo, los diagramas DAMA) usan el `id_doc` del encabezado.
  - Si junto a un PDF existe <mismo nombre>.ocr.txt, se usa ese texto en las páginas
    donde el PDF no tiene texto extraíble (PDF escaneado).
"""
import argparse
import csv
import hashlib
import json
import re
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path

import config

AUTORIDAD_POR_CAPA = {
    "A": "primaria", "B": "adaptacion", "C": "normativa",
    "D": "referente", "E": "complementaria", "F": "institucional",
}
EXTENSIONES = {".pdf", ".md", ".txt"}


# ---------------------------------------------------------------------------
# Inventario
# ---------------------------------------------------------------------------
def leer_manifest():
    if not config.MANIFEST.exists():
        print(f"ADVERTENCIA: no encuentro {config.MANIFEST}; se usarán metadatos mínimos.")
        return {}
    with open(config.MANIFEST, encoding="utf-8-sig", newline="") as f:
        return {fila["id"].strip(): fila for fila in csv.DictReader(f) if fila.get("id")}


def leer_front_matter(texto):
    """Devuelve (metadatos, cuerpo) de un Markdown con encabezado YAML simple."""
    if not texto.startswith("---"):
        return {}, texto
    fin = texto.find("\n---", 3)
    if fin == -1:
        return {}, texto
    meta = {}
    for linea in texto[3:fin].splitlines():
        if ":" in linea:
            k, v = linea.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, texto[fin + 4:].lstrip("\n")


def descubrir_documentos():
    """Lista los documentos del corpus como diccionarios con sus rutas."""
    docs = []
    for carpeta in config.CARPETAS_CORPUS:
        base = config.CORPUS / carpeta
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in EXTENSIONES:
                continue
            if p.name.upper().startswith(("README", "LEEME")) or p.name.endswith(".ocr.txt"):
                continue
            ocr = p.with_name(p.stem + ".ocr.txt") if p.suffix.lower() == ".pdf" else None
            docs.append({"ruta": p, "ocr": ocr if ocr and ocr.exists() else None, "carpeta": carpeta})
    return docs


def huella(*rutas):
    h = hashlib.sha1()
    for r in rutas:
        if r:
            h.update(Path(r).read_bytes())
    return h.hexdigest()[:16]


# ---------------------------------------------------------------------------
# Extracción de texto
# ---------------------------------------------------------------------------
def paginas_ocr(ruta_ocr):
    texto = ruta_ocr.read_text(encoding="utf-8", errors="ignore")
    partes = re.split(r"^=== Página (\d+) ===\s*$", texto, flags=re.M)
    paginas = {}
    for i in range(1, len(partes) - 1, 2):
        paginas[int(partes[i])] = partes[i + 1]
    return paginas


def extraer_pdf(ruta, ruta_ocr=None):
    import pymupdf as fitz  # PyMuPDF
    ocr = paginas_ocr(ruta_ocr) if ruta_ocr else {}
    paginas = []
    with fitz.open(ruta) as pdf:
        for n, pagina in enumerate(pdf, start=1):
            texto = pagina.get_text("text")
            if len(texto.strip()) < 200 and len(ocr.get(n, "").strip()) > len(texto.strip()):
                texto = ocr[n]          # página escaneada: usar OCR
            paginas.append((n, texto))
    if not paginas and ocr:
        paginas = sorted(ocr.items())
    return paginas


def quitar_encabezados(paginas):
    """Elimina líneas que se repiten en muchas páginas (encabezados y pies de página)."""
    if len(paginas) < 4:
        return paginas
    def norm(l):
        return re.sub(r"\d+", "#", l.strip().lower())
    conteo = Counter()
    for _, t in paginas:
        conteo.update({norm(l) for l in t.splitlines() if 0 < len(l.strip()) <= 100})
    umbral = max(3, int(0.4 * len(paginas)))
    repetidas = {l for l, c in conteo.items() if c >= umbral}
    return [(n, "\n".join(l for l in t.splitlines() if norm(l) not in repetidas)) for n, t in paginas]


VIÑETA = re.compile(r"^\s*([•●▪◦\-–*]|\d{1,2}[.)]|[a-z][.)])\s+")


def unidades_de_pagina(texto):
    """Convierte el texto de una página en párrafos (une líneas cortadas por el PDF)."""
    texto = unicodedata.normalize("NFKC", texto)             # ligaduras (ﬁ -> fi) y similares
    texto = re.sub(r"(\w)-\n(\w)", r"\1\2", texto)          # palabras partidas con guion
    unidades, actual = [], []
    for linea in texto.splitlines():
        l = re.sub(r"(\s?\.){4,}|…{2,}", " ", linea).strip()   # puntos de relleno de índices
        if not l or re.fullmatch(r"(página|pág\.?|page)?\s*\d+(\s*(de|of)\s*\d+)?", l, re.I):
            if actual:
                unidades.append(" ".join(actual)); actual = []
            continue
        if actual and (VIÑETA.match(l) or re.search(r"[.:;]$", actual[-1])):
            unidades.append(" ".join(actual)); actual = []
        actual.append(l)
    if actual:
        unidades.append(" ".join(actual))
    return [re.sub(r"\s+", " ", u).strip() for u in unidades if u.strip()]


# ---------------------------------------------------------------------------
# Fragmentación
# ---------------------------------------------------------------------------
def partir_largo(texto, tam):
    oraciones = re.split(r"(?<=[.;:!?])\s+", texto)
    piezas, actual = [], ""
    for o in oraciones:
        while len(o) > tam:                       # oración enorme: cortar por espacios
            corte = o.rfind(" ", 0, tam) if " " in o[:tam] else tam
            piezas.append(o[:corte].strip()); o = o[corte:].strip()
        if actual and len(actual) + len(o) + 1 > tam:
            piezas.append(actual); actual = o
        else:
            actual = f"{actual} {o}".strip()
    if actual:
        piezas.append(actual)
    return piezas


def fragmentar(unidades, tam=None, solape=None):
    """unidades: lista de (pagina, texto). Devuelve lista de (pag_inicio, pag_fin, texto)."""
    tam = tam or config.TAM_FRAGMENTO
    solape = config.SOLAPE if solape is None else solape
    piezas = []
    for pag, t in unidades:
        piezas.extend((pag, p) for p in ([t] if len(t) <= tam else partir_largo(t, tam)))
    fragmentos, actual, largo = [], [], 0
    for pag, t in piezas:
        if actual and largo + len(t) + 1 > tam:
            fragmentos.append(actual)
            cola, l = [], 0
            for p in reversed(actual):                # solapamiento con el fragmento anterior
                if l + len(p[1]) > solape:
                    break
                cola.insert(0, p); l += len(p[1]) + 1
            actual, largo = cola, l
        actual.append((pag, t)); largo += len(t) + 1
    if actual:
        fragmentos.append(actual)
    return [(f[0][0], f[-1][0], " ".join(t for _, t in f)) for f in fragmentos]


def secciones_markdown(cuerpo):
    """Divide un Markdown en (titulo_seccion, texto) usando los encabezados ## y ###."""
    secciones, titulo, lineas, padre = [], None, [], None
    for linea in cuerpo.splitlines():
        m = re.match(r"^(#{1,3})\s+(.*)", linea)
        if m:
            if titulo is not None and any(x.strip() for x in lineas):
                secciones.append((titulo, "\n".join(lineas).strip()))
            nivel, texto = len(m.group(1)), m.group(2).strip()
            if nivel == 1:
                titulo, padre = None, None      # el título del documento ya va en el encabezado
            elif nivel == 2:
                titulo, padre = texto, texto
            else:
                titulo = f"{padre} > {texto}" if padre else texto
            lineas = []
        else:
            lineas.append(linea)
    if titulo is not None and any(x.strip() for x in lineas):
        secciones.append((titulo, "\n".join(lineas).strip()))
    if not secciones:                            # documento sin secciones: todo el cuerpo
        texto = "\n".join(l for l in cuerpo.splitlines() if not l.startswith("# ")).strip()
        secciones = [("", texto)]
    return secciones


# ---------------------------------------------------------------------------
# Procesamiento de un documento
# ---------------------------------------------------------------------------
def metadatos_documento(doc, manifest, meta_md):
    nombre = doc["ruta"].name
    id_doc = meta_md.get("id_doc") or nombre.split("_")[0]
    fila = manifest.get(id_doc) or manifest.get(id_doc.split("_")[0])
    if fila is None:
        print(f"  ADVERTENCIA: {id_doc} no está en corpus_manifest.csv; agrega una fila para mejores metadatos.")
        fila = {}
    capa = (meta_md.get("capa") or fila.get("capa") or ("F" if doc["carpeta"] == "interno" else "E")).strip()
    meta = {
        "id_doc": id_doc,
        "id_fuente": fila.get("id", id_doc),
        "titulo": meta_md.get("titulo") or fila.get("titulo") or doc["ruta"].stem,
        "emisor": fila.get("emisor", ""),
        "anio": str(fila.get("anio", "")),
        "capa": capa,
        "autoridad": meta_md.get("autoridad") or AUTORIDAD_POR_CAPA.get(capa, "otra"),
        "area_dama": meta_md.get("area_dama") or fila.get("area_dama", ""),
        "idioma": meta_md.get("idioma") or fila.get("idioma", "es"),
        "licencia": meta_md.get("licencia") or fila.get("licencia", ""),
        "url": fila.get("url", ""),
        "archivo": str(doc["ruta"].relative_to(config.RAIZ)).replace("\\", "/"),
        "carpeta": doc["carpeta"],
    }
    return {k: (v if v is not None else "") for k, v in meta.items()}


def procesar_documento(doc, manifest):
    """Devuelve (metadatos_doc, lista_de_fragmentos)."""
    ruta = doc["ruta"]
    ext = ruta.suffix.lower()
    meta_md, secciones, paginas = {}, None, None
    if ext == ".md":
        meta_md, cuerpo = leer_front_matter(ruta.read_text(encoding="utf-8", errors="ignore"))
        secciones = secciones_markdown(cuerpo)
    elif ext == ".txt":
        paginas = [(0, ruta.read_text(encoding="utf-8", errors="ignore"))]
    else:
        paginas = quitar_encabezados(extraer_pdf(ruta, doc["ocr"]))

    meta = metadatos_documento(doc, manifest, meta_md)
    meta["hash"] = huella(ruta, doc["ocr"])

    fragmentos = []
    if secciones is not None:                           # Markdown: un fragmento por sección
        etiqueta = "DAMA-DMBOK2" if meta["capa"] == "A" and "DAMA" in meta["licencia"] + meta["titulo"] else meta["titulo"]
        for titulo_sec, texto in secciones:
            texto = re.sub(r"\n{2,}", "\n", texto)
            for _, _, trozo in fragmentar([(0, texto)], tam=int(config.TAM_FRAGMENTO * 1.5), solape=0):
                encabezado = f"[{etiqueta} · {meta['area_dama'] or meta['titulo']}" + (f" · {titulo_sec}]" if titulo_sec else "]")
                fragmentos.append({"texto": trozo, "encabezado": encabezado, "seccion": titulo_sec, "pagina": 0, "pagina_fin": 0})
    else:
        unidades = [(n, u) for n, t in paginas for u in unidades_de_pagina(t)]
        for p0, p1, trozo in fragmentar(unidades):
            if len(trozo) < config.MIN_FRAGMENTO:
                continue
            pags = "" if p0 == 0 else (f" · p. {p0}" if p0 == p1 else f" · pp. {p0}-{p1}")
            encabezado = f"[{meta['titulo']} · {meta['emisor']}{pags}]"
            fragmentos.append({"texto": trozo, "encabezado": encabezado, "seccion": "", "pagina": p0, "pagina_fin": p1})

    for i, f in enumerate(fragmentos):
        f["id"] = f"{meta['id_doc']}_{i:04d}"
        f["documento"] = f"{f['encabezado']}\n{f['texto']}"
        f["metadatos"] = {**meta, "seccion": f["seccion"], "pagina": f["pagina"], "pagina_fin": f["pagina_fin"]}
    return meta, fragmentos


# ---------------------------------------------------------------------------
# Chroma
# ---------------------------------------------------------------------------
def abrir_coleccion(reconstruir=False):
    import chromadb
    config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    cliente = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    if reconstruir:
        try:
            cliente.delete_collection(config.COLECCION)
            print(f"Colección '{config.COLECCION}' eliminada.")
        except Exception:
            pass
    return cliente.get_or_create_collection(
        name=config.COLECCION,
        metadata={"hnsw:space": "cosine", "modelo_embeddings": config.MODELO_EMBED},
    )


def hashes_indexados(coleccion):
    datos = coleccion.get(include=["metadatas"])
    return {m["id_doc"]: m.get("hash") for m in datos["metadatas"]}


def exportar_fragmentos(coleccion):
    datos = coleccion.get(include=["documents", "metadatas"])
    with open(config.FRAGMENTOS_JSONL, "w", encoding="utf-8") as f:
        for i, d, m in zip(datos["ids"], datos["documents"], datos["metadatas"]):
            f.write(json.dumps({"id": i, "documento": d, "metadatos": m}, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Ingesta del corpus DAMA-Icesi en Chroma")
    ap.add_argument("--reconstruir", action="store_true", help="borra la colección y la crea desde cero")
    ap.add_argument("--solo-extraer", action="store_true", help="solo extrae y fragmenta (sin Ollama ni Chroma)")
    args = ap.parse_args()

    manifest = leer_manifest()
    docs = descubrir_documentos()
    print(f"Documentos encontrados en corpus/: {len(docs)}")

    if args.solo_extraer:
        salida = config.CHROMA_DIR / "vista_previa_fragmentos.jsonl"
        salida.parent.mkdir(parents=True, exist_ok=True)
        total = 0
        with open(salida, "w", encoding="utf-8") as f:
            for doc in docs:
                meta, frags = procesar_documento(doc, manifest)
                total += len(frags)
                print(f"  {meta['id_doc']:<8} capa {meta['capa']}  {len(frags):>4} fragmentos  {doc['ruta'].name}")
                for fr in frags:
                    f.write(json.dumps({"id": fr["id"], "documento": fr["documento"], "metadatos": fr["metadatos"]}, ensure_ascii=False) + "\n")
        print(f"Total: {total} fragmentos. Vista previa en {salida}")
        return

    import ollama_cliente
    try:
        ollama_cliente.verificar_modelos(config.MODELO_EMBED)
    except ollama_cliente.ErrorOllama as e:
        sys.exit(f"ERROR: {e}")

    print(f"Base vectorial en: {config.CHROMA_DIR}")
    coleccion = abrir_coleccion(args.reconstruir)
    previos = hashes_indexados(coleccion)
    vistos, nuevos, omitidos = set(), 0, 0
    inicio = time.time()

    for doc in docs:
        meta, frags = procesar_documento(doc, manifest)
        vistos.add(meta["id_doc"])
        if previos.get(meta["id_doc"]) == meta["hash"]:
            omitidos += 1
            continue
        if meta["id_doc"] in previos:                         # cambió: borrar versión anterior
            coleccion.delete(where={"id_doc": meta["id_doc"]})
        if not frags:
            print(f"  {meta['id_doc']:<8} sin texto extraíble; revisa el archivo {doc['ruta'].name}")
            continue
        t0 = time.time()
        vectores = ollama_cliente.embeddings([f["documento"] for f in frags])
        for i in range(0, len(frags), 200):
            lote = frags[i:i + 200]
            coleccion.upsert(
                ids=[f["id"] for f in lote],
                documents=[f["documento"] for f in lote],
                embeddings=vectores[i:i + 200],
                metadatas=[f["metadatos"] for f in lote],
            )
        nuevos += 1
        print(f"  {meta['id_doc']:<8} {len(frags):>4} fragmentos  ({time.time() - t0:.0f} s)  {doc['ruta'].name}")

    retirados = set(previos) - vistos                        # documentos que ya no están en disco
    for id_doc in retirados:
        coleccion.delete(where={"id_doc": id_doc})
        print(f"  {id_doc:<8} retirado del índice (ya no está en corpus/)")

    exportar_fragmentos(coleccion)
    print(f"\nListo en {time.time() - inicio:.0f} s: {nuevos} documentos cargados, {omitidos} sin cambios, "
          f"{len(retirados)} retirados. La colección tiene {coleccion.count()} fragmentos.")


if __name__ == "__main__":
    main()
