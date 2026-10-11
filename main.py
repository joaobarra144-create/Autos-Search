import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.parse import urlencode


def enviar_mensagem(texto):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise RuntimeError(
            "Faltam TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID."
        )

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    dados = urlencode({
        "chat_id": chat_id,
        "text": texto,
    }).encode("utf-8")

    pedido = Request(url, data=dados, method="POST")

    with urlopen(pedido, timeout=20) as resposta:
        resultado = json.loads(resposta.read().decode("utf-8"))

    if not resultado.get("ok"):
        raise RuntimeError("O Telegram não confirmou o envio.")

    print("Mensagem enviada com sucesso.")


def main():
    if "--test" in sys.argv:
        enviar_mensagem(
            "✅ Aveiro Auto & Moto Radar\n\n"
            "Ligação à cloud confirmada!\n"
            "O sistema está preparado para a próxima fase."
        )
    else:
        print(
            "O motor de pesquisa ainda não está implementado."
        )


if __name__ == "__main__":
    main()