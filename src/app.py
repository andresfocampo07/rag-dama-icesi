"""Interfaz de chat del RAG de gobierno de datos.

Uso:  streamlit run src/app.py
"""
import streamlit as st

import config
import ollama_cliente
import rag

st.set_page_config(page_title="Asistente DAMA · Icesi", page_icon="📚", layout="wide")


@st.cache_resource(show_spinner=False)
def verificar_entorno():
    ollama_cliente.verificar_modelos(config.MODELO_EMBED, config.MODELO_LLM)
    return rag.coleccion().count()


# --- Barra lateral -----------------------------------------------------------
with st.sidebar:
    st.header("Configuración")
    k = st.slider("Fragmentos a recuperar (k)", 3, 15, config.K)
    min_dama = st.slider("Mínimo de fragmentos DAMA", 0, 5, config.MIN_DAMA,
                         help="Garantiza que al menos estos fragmentos vengan de los diagramas DAMA-DMBOK2.")
    opciones = {f"{c} · {n}": c for c, n in rag.ETIQUETAS_CAPA.items()}
    elegidas = st.multiselect("Buscar solo en estas capas (vacío = todas)", list(opciones))
    capas = [opciones[e] for e in elegidas] or None
    mostrar_texto = st.toggle("Mostrar el texto de cada fragmento", value=False)
    st.divider()
    st.caption(f"Modelo: `{config.MODELO_LLM}`  \nEmbeddings: `{config.MODELO_EMBED}`  \n"
               f"Colección: `{config.COLECCION}`")
    if st.button("Borrar conversación"):
        st.session_state.historial = []

st.title("Asistente de gobierno de datos (DAMA-DMBOK)")
st.caption("Oficina de Estrategia de Datos Institucionales · Universidad Icesi. "
           "Las respuestas se basan solo en el corpus documental y citan sus fuentes.")

try:
    n_fragmentos = verificar_entorno()
except Exception as e:  # Ollama apagado, modelos sin descargar o colección vacía
    st.error(str(e))
    st.stop()

st.sidebar.caption(f"Fragmentos indexados: {n_fragmentos}")

if "historial" not in st.session_state:
    st.session_state.historial = []


def mostrar_fuentes(fragmentos):
    with st.expander(f"Fuentes consultadas ({len(fragmentos)})"):
        filas = [{
            "Cita": f["cita"],
            "Documento": f["metadatos"]["titulo"][:60],
            "Emisor": f["metadatos"]["emisor"],
            "Tipo de fuente": f"{f['metadatos']['capa']} · {rag.ETIQUETAS_CAPA.get(f['metadatos']['capa'], '')}",
            "Distancia": f["distancia"],
        } for f in fragmentos]
        st.dataframe(filas, hide_index=True, width="stretch")
        if mostrar_texto:
            for f in fragmentos:
                st.markdown(f"**[{f['cita']}]**")
                st.text(f["documento"][:500] + ("…" if len(f["documento"]) > 500 else ""))


for turno in st.session_state.historial:
    with st.chat_message("user"):
        st.markdown(turno["pregunta"])
    with st.chat_message("assistant"):
        st.markdown(turno["respuesta"])
        mostrar_fuentes(turno["fragmentos"])

pregunta = st.chat_input("Escribe tu pregunta sobre gobierno de datos…")
if pregunta:
    with st.chat_message("user"):
        st.markdown(pregunta)
    with st.chat_message("assistant"):
        with st.spinner("Buscando en el corpus y redactando la respuesta…"):
            try:
                r = rag.responder(pregunta, k=k, min_dama=min_dama, capas=capas)
            except Exception as e:
                st.error(f"Ocurrió un error: {e}")
                st.stop()
        st.markdown(r["respuesta"])
        st.caption(f"{r['segundos_total']} s")
        mostrar_fuentes(r["fragmentos"])
    st.session_state.historial.append(r)
