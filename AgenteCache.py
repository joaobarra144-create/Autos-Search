import os
import json
import time
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError
from ddgs import DDGS

# Inicializar o cliente do Google GenAI
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Ficheiro onde a cache será guardada persistentemente no disco
CACHE_FILE = "cache_pesquisas.json"

def carregar_cache():
    """Carrega a cache do disco se existir."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def guardar_cache(cache):
    """Guarda a cache atualizada no disco."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)

def pesquisar_com_cache(query: str) -> str:
    """Pesquisa anúncios com verificação prévia numa cache local em JSON."""
    cache = carregar_cache()
    
    # Normalizar a chave da pesquisa para evitar duplicados por maiúsculas/espaços
    query_key = query.lower().strip()
    
    # Verificar se já existe na cache
    if query_key in cache:
        print(f"\n[Sistema] ⚡ [CACHE HIT] A recuperar dados locais para: '{query}' (Sem custo de rede!)")
        return cache[query_key]
    
    # Se não existir, faz a pesquisa real na web
    query_otimizada = f"{query} site:standvirtual.com OR site:olx.pt OR site:custojusto.pt"
    print(f"\n[Sistema] 🌐 [CACHE MISS] A pesquisar na web por: '{query}'...")
    
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
            
            # Guardar na cache e persistir no ficheiro JSON
            cache[query_key] = resposta
            guardar_cache(cache)
            return resposta
            
    except Exception as e:
        return f"Erro ao consultar classificados: {str(e)}"

def main():
    print("==========================================================")
    print("  💾🚗 Agente com Cache Local Ativa (Poupança de API)")
    print("==========================================================\n")
    
    modelo = 'gemini-3.8-flash'
    
    chat = client.chats.create(
        model=modelo,
        config=types.GenerateContentConfig(
            tools=[pesquisar_com_cache],
            system_instruction=(
                "És um analista de mercado automóvel em Portugal. "
                "Usa sempre a ferramenta de pesquisa para consultar dados de classificados. "
                "Sê direto, analisa os preços e apresenta respostas claras."
            )
        )
    )
    
    while True:
        try:
            pergunta = input("\n[Utilizador]: ").strip()
            if not pergunta:
                continue
            if pergunta.lower() in ["sair", "exit", "quit"]:
                print("[Sistema] A encerrar o agente.")
                break
            
            max_tentativas = 5
            sucesso = False
            
            for tentativa in range(max_tentativas):
                try:
                    response = chat.send_message(pergunta)
                    print(f"\n[Agente]:\n{response.text}")
                    sucesso = True
                    break
                except ServerError:
                    print(f"[Aviso] Servidor sobrecarregado (503). Tentativa {tentativa + 1}/{max_tentativas}...")
                    time.sleep(3)
                except ClientError as e:
                    print(f"[Erro do Cliente/Quota Excedida] {e}")
                    break
            
            if not sucesso:
                print("[Erro] O servidor não respondeu após várias tentativas.")
                
        except (KeyboardInterrupt, EOFError):
            print("\n[Sistema] A encerrar o agente. Até à próxima!")
            break

if __name__ == "__main__":
    main()