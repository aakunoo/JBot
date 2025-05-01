import pytest, requests_mock
from src.core.commands import comando_clima

@pytest.mark.asyncio
async def test_comando_clima(fake_update, fake_context):
    # 1) Mock de la llamada HTTP a la API del tiempo
    with requests_mock.Mocker() as m:
        api_url = "https://api.weatherapi.com/v1/current.json"
        m.get(api_url, json={
            "current": {
                "temp_c": 20,
                "condition": {"text": "Despejado"}
            }
        })

        # 2) Capturamos lo que el bot responde
        respuesta = []
        fake_update.message.reply_text = lambda txt, **_: respuesta.append(txt)

        # 3) Ejecutamos handler
        await comando_clima(fake_update, fake_context, provincia="Valencia")

        # 4) Afirmaciones
        assert "20" in respuesta[0]
        assert "Valencia" in respuesta[0]
