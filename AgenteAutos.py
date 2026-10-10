import os
import time
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError
from ddgs import DDGS

# Inicializar o cliente do Google GenAI
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def pesquisar_classificados_portugal(query: str) -> str:
    """Pesquisa anúncios de carros e motas em portais de classificados em Portugal (Standvirtual, OLX, etc.)."""
    # Forçamos o foco em sites portugueses relevantes na query
    query_otimizada = f"{query} site:standvirtual.com OR site:olx.pt OR site:custojusto.pt"
    print(f"\n[Sistema] A vasculhar classificados em Portugal por: '{query}'...")
    
    try:
        with DDGS() as ddgs:
            resultados = [
                f"Título/Link: {r.get('title')}\nDetalhes: {r.get('body')}\nURL: {r.get('href')}" 
                for r in ddgs.text(query_otimizada, max_results=6)
            ]
            if not resultados:
                return "Não foram encontrados anúncios recentes com esses critérios."
            return "\n---\n".join(resultados)
    except Exception as e:
        return f"Erro ao consultar classificados: {str(e)}"

def main():
    print("==========================================================")
    print("  🇵🇹🚗 Agente de Comparação de Classificados (PT)")
    print("  Exemplo: 'Compara os preços médios de um VW Golf VII usado'")
    print("==========================================================\n")
    
    modelo = 'gemini-3.8-flash'
    
    chat = client.chats.create(
        model=modelo,
        config=types.GenerateContentConfig(
            tools=[pesquisar_classificados_portugal],
            system_instruction=(
                "És um analista de mercado automóvel autónomo focado no mercado português. "
                "O teu objetivo é ajudar o utilizador a comparar preços de carros e motas em Portugal, "
                "recolhendo dados de portais como Standvirtual, OLX e CustoJusto através da ferramenta. "
                "Sempre que o utilizador pedir uma comparação ou análise de preços, extrai os valores encontrados "
                "nos anúncios, calcula estimativas de mercado e apresenta uma tabela ou resumo claro com os preços mínimos, "
                "máximos e média estimada."
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
                    print(f"[Erro do Cliente] {e}")
                    break
            
            if not sucesso:
                print("[Erro] O servidor não respondeu após várias tentativas.")
                
        except (KeyboardInterrupt, EOFError):
            print("\n[Sistema] A encerrar o agente. Até à próxima!")
            break

if __name__ == "__main__":
    main()