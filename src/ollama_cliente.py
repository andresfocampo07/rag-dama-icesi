"""Cliente mínimo para la API local de Ollama (embeddings y chat)."""
import requests

import config


class ErrorOllama(RuntimeError):
    pass


def _post(ruta, cuerpo):
    url = f"{config.OLLAMA_URL}{ruta}"
    try:
        r = requests.post(url, json=cuerpo, timeout=config.TIMEOUT_OLLAMA)
    except requests.ConnectionError as e:
        raise ErrorOllama(
            f"No me pude conectar a Ollama en {config.OLLAMA_URL}. "
            "Verifica que Ollama esté abierto (ícono en la bandeja) o ejecuta `ollama serve`."
        ) from e
    if r.status_code == 404 and "not found" in r.text.lower():
        modelo = cuerpo.get("model")
        raise ErrorOllama(f"El modelo '{modelo}' no está descargado. Ejecuta: ollama pull {modelo}")
    if r.status_code != 200:
        raise ErrorOllama(f"Ollama respondió {r.status_code}: {r.text[:300]}")
    return r.json()


def modelos_disponibles():
    try:
        r = requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=10)
        r.raise_for_status()
    except requests.RequestException as e:
        raise ErrorOllama(
            f"No me pude conectar a Ollama en {config.OLLAMA_URL}. "
            "Verifica que Ollama esté abierto o ejecuta `ollama serve`."
        ) from e
    return {m["name"] for m in r.json().get("models", [])}


def verificar_modelos(*modelos):
    """Lanza ErrorOllama si algún modelo no está descargado."""
    disponibles = modelos_disponibles()
    nombres = disponibles | {n.split(":")[0] for n in disponibles if n.endswith(":latest")}
    faltan = [m for m in modelos if m not in nombres]
    if faltan:
        cmds = "\n".join(f"  ollama pull {m}" for m in faltan)
        raise ErrorOllama(f"Faltan modelos en Ollama. Ejecuta:\n{cmds}")


def embeddings(textos, lote=16):
    """Devuelve una lista de vectores, uno por texto."""
    vectores = []
    for i in range(0, len(textos), lote):
        resp = _post("/api/embed", {"model": config.MODELO_EMBED, "input": textos[i:i + lote]})
        vectores.extend(resp["embeddings"])
    return vectores


def chat(mensajes, modelo=None, temperatura=0.1):
    resp = _post("/api/chat", {
        "model": modelo or config.MODELO_LLM,
        "messages": mensajes,
        "stream": False,
        "options": {"temperature": temperatura, "num_ctx": config.CONTEXTO_LLM},
    })
    return resp["message"]["content"].strip()
