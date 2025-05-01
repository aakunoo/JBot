import pytest, requests_mock
from src.clima.clima_bot import comando_clima
from src.database import models


@pytest.mark.asyncio
async def test_comando_clima(fake_update, fake_context, db):
    # Registro un usuario ficticio para que get_user() devuelva datos
    models.register_user(
        chat_id=fake_update.message.chat.id,
        username="tester",
        apodo="tester",
    )

    # Mensaje de entrada
    fake_update.message.text = "/clima Salamanca"
    fake_context.args = ["Salamanca"] 

    # Mock de la API meteorológica
    with requests_mock.Mocker() as m:
        m.get(requests_mock.ANY, json={
            "main": {"temp": 20},
            "weather": [{"description": "Despejado"}],
            "wind": {"speed": 3},
        })

        # Captura de la respuesta del bot
        respuestas = []

        async def _capture(txt, **_):
            respuestas.append(txt)

        fake_update.message.reply_text = _capture

        # Ejecutar el handler
        await comando_clima(fake_update, fake_context)

        # Comprobar salida
        assert respuestas
        assert "Salamanca" in respuestas[0] and "20" in respuestas[0]
