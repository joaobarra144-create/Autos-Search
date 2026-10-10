import os
from datetime import datetime
from google import genai
from google.genai import types
from ddgs import DDGS

# Inicializar o cliente do Google GenAI
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def pesquisar_anuncios_recentes(query: str) -> str:
    """Pesquisa anúncios de carros e motas em Portugal."""
    query_otimizada = f"{query} novo site:standvirtual.com OR site:olx.pt"
    print(f"\n[Sistema] A executar pesquisa automática para: '{query}'...")
    
    try:
        with DDGS() as ddgs:
            resultados = [
                f"Título: {r.get('title')}\nResumo: {r.get('body')}\nLink: {r.get('href')}" 
                for r in ddgs.text(query_otimizada, max_results=5)
            ]
            if not resultados:
                return "Não foram encontrados novos anúncios recentes."
            return "\n---\n".join(resultados)
    except Exception as e:
        return f"Erro na pesquisa web: {str(e)}"

def main():
    print(f"\n[Execução GitHub Actions] A iniciar rotina diária às {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    veiculo_alvo = "BMW X3 2008 diesel Portugal"
    prompt = f"Pesquisa anúncios recentes de {veiculo_alvo}. Extrai os títulos, os preços exatos, o ano e os links dos anúncios encontrados. Apresenta uma lista limpa e organizada."
    
    modelo = 'gemini-3.8-flash'
    
    try:
        # Chamada direta e única (consome muito menos quota da API)
        response = client.models.generate_content(
            model=modelo,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[pesquisar_anuncios_recentes],
                system_instruction=(
                    "És um analista de mercado automóvel autónomo em Portugal. "
                    "Usa a ferramenta de pesquisa para consultar classificados e apresenta uma lista detalhada "
                    "com o título, preço, ano e link de cada veículo, sem respostas vagas."
                )
            )
        )
        
        relatorio = response.text
        
        # Guardar o relatório no ficheiro fixo
        nome_ficheiro = "relatorio_diario.md"
        data_hoje = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conteudo_ficheiro = f"# Relatório Automático de Classificados\n*Atualizado em: {data_hoje}*\n\n{relatorio}\n"
        
        with open(nome_ficheiro, "w", encoding="utf-8") as f:
            f.write(conteudo_ficheiro)
            
        print(f"[Sucesso] Relatório guardado em {nome_ficheiro}")
        
    except Exception as e:
        print(f"[Erro na Execução]: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()