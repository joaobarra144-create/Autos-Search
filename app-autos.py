import os
import json
import streamlit as st
from google import genai
from google.genai import types
from ddgs import DDGS
import time

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Agente de Automóveis e Classificados (PT)",
    page_icon="🚗",
    layout="centered"
)

st.title("🚗 Agente de Classificados & Automóveis")
st.caption("Pesquisa inteligente em portais portugueses (Standvirtual, OLX, CustoJusto) com cache local.")

# Obter a chave de API (compatível com local e Streamlit Cloud)
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key and "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

if not api_key:
    st.error("A chave GEMINI_API_KEY não foi encontrada. Configura-a nos segredos do Streamlit Cloud.")
    st.stop()

# Inicializar o cliente do Google GenAI
client = genai.Client(api_key=api_key)

# Configuração da Cache Local
CACHE_FILE = "cache_pesquisas.json"

def carregar_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def guardar_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)

# Ferramenta de pesquisa com cache
def pesquisar_com_cache(query: str) -> str:
    """Pesquisa anúncios de carros/motas em Portugal com cache local."""
    cache = carregar_cache()
    query_key = query.lower().strip()
    
    if query_key in cache:
        return f"(⚡ [Cache Local Hit])\n{cache[query_key]}"
    
    query_otimizada = f"{query} site:standvirtual.com OR site:olx.pt OR site:custojusto.pt"
    try:
        with DDGS() as ddgs:
            resultados = [
                f"Título/Link: {r.get('title')}\nDetalhes: {r.get('body')}\nURL: {r.get('href')}" 
                for r in ddgs.text(query_otimizada, max_results=4)
            ]
            if not resultados:
                resposta = "Não foram encontrados anúncios recentes com esses critérios."
            else:
                resposta = "\n---\n".join(resultados)
            
            cache[query_key] = resposta
            guardar_cache(cache)
            return resposta
    except Exception as e:
        return f"Erro ao consultar classificados: {str(e)}"

# Inicializar o estado da sessão do Streamlit para manter o chat e o cliente Gemini ativo
if "chat_session" not in st.session_state:
    modelo = 'gemini-3.8-flash'
    st.session_state.chat_session = client.chats.create(
        model=modelo,
        config=types.GenerateContentConfig(
            tools=[pesquisar_com_cache],
            system_instruction=(
	    "És um analista de mercado automóvel em Portugal. "
	    "Quando usares a ferramenta de pesquisa para consultar portais (Standvirtual, OLX, etc.), "
	    "NUNCA te limites a dar apenas links genéricos. "
	    "Deves extrair dos resultados o título do anúncio, o preço exato, o ano, os quilómetros (se disponíveis) "
	    "e apresentar obrigatoriamente uma lista ou tabela organizada com os veículos encontrados."
	    )
        )
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibir o histórico de mensagens no chat visual
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Caixa de input do utilizador na interface web
if prompt := st.chat_input("Ex: Qual o preço médio de um BMW X3 usado de 2008?"):
    # Adicionar mensagem do utilizador ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

# Gerar resposta do agente com tentativas automáticas para o erro 503
    with st.chat_message("assistant"):
        with st.spinner("A consultar classificados e a pensar..."):
            max_tentativas = 5
            sucesso = False
            resposta_texto = ""
            
            for tentativa in range(max_tentativas):
                try:
                    response = st.session_state.chat_session.send_message(prompt)
                    resposta_texto = response.text
                    sucesso = True
                    break
                except ServerError:
                    time.sleep(3)
                except Exception as e:
                    resposta_texto = f"Ocorreu um erro ao comunicar com a API: {str(e)}"
                    break
            
            if sucesso:
                st.markdown(resposta_texto)
                st.session_state.messages.append({"role": "assistant", "content": resposta_texto})
            else:
                st.error("O servidor continua sobrecarregado após várias tentativas. Por favor, tenta novamente mais tarde.")