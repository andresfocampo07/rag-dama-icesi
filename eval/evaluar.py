"""Evaluación del RAG: métricas de recuperación, abstención, citas y RAGAS con juez local (Ollama).

Uso (desde la carpeta raíz del proyecto):
    python eval/evaluar.py --etiqueta base                 # corre todo (respuestas + métricas + RAGAS)
    python eval/evaluar.py --etiqueta sin_dama --min-dama 0
    python eval/evaluar.py --etiqueta prueba --limite 5    # prueba rápida con 5 preguntas
    python eval/evaluar.py --etiqueta piloto --muestra 12  # piloto: 12 preguntas repartidas por tema
    python eval/evaluar.py --etiqueta base --sin-ragas     # solo métricas que no usan LLM juez
    python eval/evaluar.py --solo-ragas eval/resultados/base_20261116-1530_respuestas.jsonl

Velocidad (valores por defecto pensados para una corrida rápida):
    --paralelo 4        preguntas que se procesan al mismo tiempo (configura también
                        OLLAMA_NUM_PARALLEL=4 en Ollama para que las atienda en paralelo)
    --muestra-ragas 20  RAGAS sobre una muestra estratificada por categoría (0 = todas);
                        las métricas sin juez siempre usan todas las preguntas
    --k-precision 5     context precision se juzga sobre los 5 primeros fragmentos
    Las respuestas del juez se guardan en caché (eval/.cache_ragas): repetir una
    evaluación sobre las mismas respuestas no vuelve a llamar al modelo.

Resultados en eval/resultados/:
    <etiqueta>_<fecha>_respuestas.jsonl  respuestas y fragmentos recuperados
    <etiqueta>_<fecha>_detalle.csv       métricas por pregunta
    <etiqueta>_<fecha>_metricas.json     promedios de la corrida
    resumen.csv                          una fila por corrida, para comparar configuraciones
"""
import argparse
import asyncio
import csv
import json
import math
import os
import random
import re
import sys
import time
import unicodedata
import warnings
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

# Desactiva la telemetría de RAGAS: además de no enviar datos de uso, evita que cada
# llamada al juez espere el envío de la telemetría (lo que anulaba el paralelismo).
os.environ.setdefault("RAGAS_DO_NOT_TRACK", "true")
# Avisos de deprecación de las librerías: no afectan el resultado y en PowerShell se ven como errores.
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

import config          # noqa: E402
import ollama_cliente  # noqa: E402

RESULTADOS = config.EVAL_DIR / "resultados"
METRICAS_RAGAS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
CACHE_RAGAS = config.EVAL_DIR / ".cache_ragas"


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def normalizar(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", t).strip()


def leer_preguntas(ruta):
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        filas = list(csv.DictReader(f))
    for fila in filas:
        fila["fuentes_esperadas"] = [s.strip() for s in fila.get("fuentes_esperadas", "").split(";") if s.strip()]
    return filas


def es_abstencion(respuesta):
    return normalizar(config.FRASE_ABSTENCION).rstrip(".") in normalizar(respuesta)


def coincide(id_doc, esperadas):
    """A2_12 coincide con 'A2_12' y con 'A2'; B7a coincide con 'B7a'."""
    return any(id_doc == e or id_doc.startswith(e + "_") for e in esperadas)


def media(valores):
    v = [x for x in valores if x is not None and not (isinstance(x, float) and math.isnan(x))]
    return round(sum(v) / len(v), 4) if v else None


# ---------------------------------------------------------------------------
# 1. Generar respuestas
# ---------------------------------------------------------------------------
def generar_respuestas(preguntas, k, min_dama, salida, paralelo=1):
    import rag
    rag.coleccion()   # abre Chroma una sola vez antes de lanzar los hilos

    def una(p):
        r = rag.responder(p["pregunta"], k=k, min_dama=min_dama)
        print(f"  {p['id']} ({r['segundos_total']} s) {p['pregunta'][:70]}", flush=True)
        return {
            "id": p["id"], "categoria": p["categoria"], "tipo": p["tipo"],
            "pregunta": p["pregunta"], "referencia": p["respuesta_referencia"],
            "fuentes_esperadas": p["fuentes_esperadas"], "respuesta": r["respuesta"],
            "ids_recuperados": [fr["metadatos"]["id_doc"] for fr in r["fragmentos"]],
            "citas_recuperadas": [fr["cita"] for fr in r["fragmentos"]],
            "contextos": [fr["documento"] for fr in r["fragmentos"]],
            "segundos": r["segundos_total"],
        }

    with ThreadPoolExecutor(max_workers=max(1, paralelo)) as ex:
        registros = list(ex.map(una, preguntas))          # conserva el orden original
    with open(salida, "w", encoding="utf-8") as f:
        for reg in registros:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    return registros


# ---------------------------------------------------------------------------
# 2. Métricas sin LLM juez
# ---------------------------------------------------------------------------
def metricas_basicas(reg):
    m = {}
    abst = es_abstencion(reg["respuesta"])
    m["abstencion"] = int(abst)
    if reg["tipo"] == "fuera_de_alcance":
        m["abstencion_correcta"] = int(abst)
        return m
    esperadas = reg["fuentes_esperadas"]
    rango = next((i for i, d in enumerate(reg["ids_recuperados"]) if coincide(d, esperadas)), None)
    m["hit_at_k"] = int(rango is not None)
    m["hit_at_3"] = int(rango is not None and rango < 3)
    m["rr"] = round(1 / (rango + 1), 4) if rango is not None else 0.0
    m["falsa_abstencion"] = int(abst)
    # citas: ¿la respuesta cita al menos un fragmento que realmente se recuperó?
    citas = re.findall(r"\[([^\[\]]{1,40})\]", reg["respuesta"])
    validos = {c.split(",")[0].strip() for c in reg["citas_recuperadas"]}
    m["cita_valida"] = int(any(c.split(",")[0].strip() in validos for c in citas))
    return m


# ---------------------------------------------------------------------------
# 3. RAGAS con juez local
# ---------------------------------------------------------------------------
def preparar_ragas():
    from openai import AsyncOpenAI
    from ragas.cache import DiskCacheBackend
    from ragas.embeddings.base import embedding_factory
    from ragas.llms import llm_factory
    from ragas.metrics.collections import (AnswerRelevancy, ContextPrecisionWithReference,
                                           ContextRecall, Faithfulness)

    cliente = AsyncOpenAI(base_url=f"{config.OLLAMA_URL}/v1", api_key="ollama",
                          timeout=config.TIMEOUT_OLLAMA, max_retries=2)
    cache = DiskCacheBackend(cache_dir=str(CACHE_RAGAS))
    llm = llm_factory(config.MODELO_JUEZ, provider="openai", client=cliente, cache=cache,
                      temperature=0.0, max_tokens=1024)
    emb = embedding_factory("openai", model=config.MODELO_EMBED, client=cliente)
    return {
        "faithfulness": Faithfulness(llm=llm),
        "answer_relevancy": AnswerRelevancy(llm=llm, embeddings=emb, strictness=1),
        "context_precision": ContextPrecisionWithReference(llm=llm),
        "context_recall": ContextRecall(llm=llm),
    }


async def puntuar(metricas, reg, k_precision):
    entradas = {
        "faithfulness": dict(user_input=reg["pregunta"], response=reg["respuesta"], retrieved_contexts=reg["contextos"]),
        "answer_relevancy": dict(user_input=reg["pregunta"], response=reg["respuesta"]),
        "context_precision": dict(user_input=reg["pregunta"], reference=reg["referencia"],
                                  retrieved_contexts=reg["contextos"][:k_precision]),
        "context_recall": dict(user_input=reg["pregunta"], retrieved_contexts=reg["contextos"], reference=reg["referencia"]),
    }

    async def una(nombre, metrica):
        try:
            res = await metrica.ascore(**entradas[nombre])
            valor = getattr(res, "value", res)
            return nombre, (round(float(valor), 4) if valor is not None else None), None
        except Exception as e:   # el juez local a veces no devuelve JSON válido
            return nombre, None, f"{type(e).__name__}: {str(e)[:200]}"

    # las cuatro métricas de una pregunta se piden al mismo tiempo
    resultados = await asyncio.gather(*(una(n, m) for n, m in metricas.items()))
    salida = {n: v for n, v, _ in resultados}
    errores = {n: e for n, _, e in resultados if e}
    return salida, errores


def muestra_estratificada(registros, n, semilla=42, solo_en_alcance=True):
    """Elige n preguntas repartidas proporcionalmente por categoría (mínimo 1 por categoría)."""
    en = [r for r in registros if r["tipo"] == "en_alcance"] if solo_en_alcance else list(registros)
    if not n or n >= len(en):
        return en
    grupos = {}
    for r in en:
        grupos.setdefault(r["categoria"], []).append(r)
    azar = random.Random(semilla)
    cupos = {c: max(1, round(n * len(g) / len(en))) for c, g in grupos.items()}
    while sum(cupos.values()) > n:                     # ajustar redondeos
        mayor = max(cupos, key=lambda c: cupos[c]); cupos[mayor] -= 1
    while sum(cupos.values()) < n:
        c = max(grupos, key=lambda c: len(grupos[c]) - cupos[c]); cupos[c] += 1
    elegidas = set()
    for c, g in grupos.items():
        elegidas.update(r["id"] for r in azar.sample(g, min(cupos[c], len(g))))
    return [r for r in en if r["id"] in elegidas]


def correr_ragas(registros, muestra=20, paralelo=4, k_precision=5):
    try:
        ollama_cliente.verificar_modelos(config.MODELO_JUEZ, config.MODELO_EMBED)
        metricas = preparar_ragas()
    except Exception as e:
        print(f"No se pudo preparar RAGAS: {e}")
        return {}
    evaluables = muestra_estratificada(registros, muestra)
    print(f"\nRAGAS con juez local '{config.MODELO_JUEZ}' sobre {len(evaluables)} preguntas "
          f"({paralelo} en paralelo, context precision sobre {k_precision} fragmentos)…")
    resultados = {}
    hechas = 0
    inicio = time.time()

    async def todo():
        semaforo = asyncio.Semaphore(max(1, paralelo))

        async def una(reg):
            nonlocal hechas
            async with semaforo:
                t0 = time.time()
                puntajes, errores = await puntuar(metricas, reg, k_precision)
                resultados[reg["id"]] = {**puntajes, "errores_ragas": "; ".join(f"{k}: {v}" for k, v in errores.items())}
                hechas += 1
                txt = ", ".join(f"{k}={v}" for k, v in puntajes.items())
                print(f"  [{hechas}/{len(evaluables)}] {reg['id']} ({time.time() - t0:.0f} s) {txt}", flush=True)

        await asyncio.gather(*(una(r) for r in evaluables))

    asyncio.run(todo())
    print(f"RAGAS terminó en {(time.time() - inicio) / 60:.1f} min")
    return resultados


# ---------------------------------------------------------------------------
# 4. Reporte
# ---------------------------------------------------------------------------
def reportar(registros, basicas, ragas, etiqueta, prefijo, parametros):
    en = [r for r in registros if r["tipo"] == "en_alcance"]
    fuera = [r for r in registros if r["tipo"] == "fuera_de_alcance"]
    resumen = {
        "etiqueta": etiqueta, "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), **parametros,
        "n_preguntas": len(registros), "n_en_alcance": len(en), "n_fuera_alcance": len(fuera),
        "hit_rate_at_k": media([basicas[r["id"]]["hit_at_k"] for r in en]),
        "hit_rate_at_3": media([basicas[r["id"]]["hit_at_3"] for r in en]),
        "mrr": media([basicas[r["id"]]["rr"] for r in en]),
        "tasa_citas_validas": media([basicas[r["id"]]["cita_valida"] for r in en]),
        "falsa_abstencion": media([basicas[r["id"]]["falsa_abstencion"] for r in en]),
        "abstencion_correcta_fuera_alcance": media([basicas[r["id"]]["abstencion_correcta"] for r in fuera]),
        "segundos_promedio_respuesta": media([r["segundos"] for r in registros]),
    }
    con_ragas = [r for r in en if r["id"] in ragas]
    resumen["n_evaluadas_ragas"] = len(con_ragas)
    for m in METRICAS_RAGAS:
        resumen[m] = media([ragas[r["id"]].get(m) for r in con_ragas]) if ragas else None
    resumen["ragas_fallos"] = sum(1 for r in con_ragas for m in METRICAS_RAGAS if ragas[r["id"]].get(m) is None)

    # por categoría (útil para la presentación)
    categorias = sorted({r["categoria"] for r in en})
    resumen["por_categoria"] = {
        c: {"n": sum(r["categoria"] == c for r in en),
            "hit_rate_at_k": media([basicas[r["id"]]["hit_at_k"] for r in en if r["categoria"] == c]),
            **({m: media([ragas[r["id"]].get(m) for r in en if r["categoria"] == c and r["id"] in ragas]) for m in METRICAS_RAGAS} if ragas else {})}
        for c in categorias
    }

    with open(f"{prefijo}_metricas.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)

    campos = ["id", "categoria", "tipo", "pregunta", "respuesta", "fuentes_esperadas", "ids_recuperados",
              "hit_at_k", "hit_at_3", "rr", "cita_valida", "abstencion", "abstencion_correcta",
              "falsa_abstencion", *METRICAS_RAGAS, "errores_ragas", "segundos"]
    with open(f"{prefijo}_detalle.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        for r in registros:
            fila = {**r, **basicas[r["id"]], **ragas.get(r["id"], {})}
            fila["fuentes_esperadas"] = ";".join(r["fuentes_esperadas"])
            fila["ids_recuperados"] = ";".join(r["ids_recuperados"])
            w.writerow(fila)

    ruta_resumen = RESULTADOS / "resumen.csv"
    plano = {k: v for k, v in resumen.items() if k != "por_categoria"}
    existe = ruta_resumen.exists()
    with open(ruta_resumen, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(plano))
        if not existe:
            w.writeheader()
        w.writerow(plano)

    print("\n=== Resultados:", etiqueta, "===")
    for k, v in plano.items():
        print(f"  {k:<36} {v}")
    print(f"\nArchivos: {prefijo}_metricas.json, {prefijo}_detalle.csv y {ruta_resumen}")
    return resumen


def main():
    ap = argparse.ArgumentParser(description="Evaluación del RAG DAMA-Icesi")
    ap.add_argument("--etiqueta", default="base", help="nombre de la configuración evaluada")
    ap.add_argument("--preguntas", default=str(config.EVAL_DIR / "preguntas.csv"))
    ap.add_argument("--k", type=int, default=config.K)
    ap.add_argument("--min-dama", type=int, default=config.MIN_DAMA)
    ap.add_argument("--limite", type=int, default=0, help="usar solo las primeras N preguntas")
    ap.add_argument("--muestra", type=int, default=0,
                    help="evaluar solo N preguntas, muestra estratificada por categoría (siempre la misma)")
    ap.add_argument("--sin-ragas", action="store_true", help="omitir RAGAS (solo métricas sin juez)")
    ap.add_argument("--solo-ragas", help="archivo *_respuestas.jsonl ya generado: recalcula métricas y RAGAS")
    ap.add_argument("--paralelo", type=int, default=4, help="preguntas simultáneas (respuestas y RAGAS)")
    ap.add_argument("--muestra-ragas", type=int, default=20,
                    help="preguntas para RAGAS, muestra estratificada por categoría (0 = todas)")
    ap.add_argument("--k-precision", type=int, default=5, help="fragmentos juzgados en context precision")
    args = ap.parse_args()

    RESULTADOS.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d-%H%M")

    if args.solo_ragas:
        with open(args.solo_ragas, encoding="utf-8") as f:
            registros = [json.loads(l) for l in f if l.strip()]
        prefijo = args.solo_ragas.replace("_respuestas.jsonl", "")
        etiqueta = Path(prefijo).name.rsplit("_", 1)[0]
    else:
        try:
            ollama_cliente.verificar_modelos(config.MODELO_EMBED, config.MODELO_LLM)
        except ollama_cliente.ErrorOllama as e:
            sys.exit(f"ERROR: {e}")
        preguntas = leer_preguntas(args.preguntas)
        if args.muestra:
            preguntas = muestra_estratificada(preguntas, args.muestra, solo_en_alcance=False)
        elif args.limite:
            preguntas = preguntas[:args.limite]
        etiqueta = args.etiqueta
        prefijo = str(RESULTADOS / f"{etiqueta}_{marca}")
        print(f"Generando respuestas para {len(preguntas)} preguntas (k={args.k}, min_dama={args.min_dama})…")
        registros = generar_respuestas(preguntas, args.k, args.min_dama, f"{prefijo}_respuestas.jsonl", args.paralelo)

    basicas = {r["id"]: metricas_basicas(r) for r in registros}
    ragas = {} if args.sin_ragas else correr_ragas(registros, args.muestra_ragas, args.paralelo, args.k_precision)
    parametros = {"k": args.k, "min_dama": args.min_dama, "modelo_llm": config.MODELO_LLM,
                  "modelo_juez": config.MODELO_JUEZ, "modelo_embeddings": config.MODELO_EMBED,
                  "tam_fragmento": config.TAM_FRAGMENTO, "muestra_ragas": args.muestra_ragas,
                  "k_precision": args.k_precision, "paralelo": args.paralelo}
    reportar(registros, basicas, ragas, etiqueta, prefijo, parametros)


if __name__ == "__main__":
    main()
