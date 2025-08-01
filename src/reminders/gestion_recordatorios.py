from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from src.database import get_user, obtener_recordatorios, eliminar_recordatorio_por_id
from src.reminders.mensaje_recordatorios import cancelar_job_por_record_id

'''
---------------------------------------------------------------------------
Muestra todos los recordatorios del usuario con el chat_id que corresponde
---------------------------------------------------------------------------
'''
async def mostrar_recordatorios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    mensaje = update.message if update.message else update.callback_query.message
    if not get_user(user_id):
        await mensaje.reply_text("Primero debes registrarte con /register.")
        return

    lista = obtener_recordatorios(user_id)
    if not lista:
        await mensaje.reply_text("No tienes recordatorios.")
        return

    texto = "Tus recordatorios:\n\n"
    for indice, recordatorio in enumerate(lista, start=1):
        titulo = recordatorio.get("titulo", "Sin título")
        descripcion = recordatorio.get("descripcion", "Sin descripción")
        fecha_inicio = recordatorio.get("fecha_hora_inicio")
        if fecha_inicio and isinstance(fecha_inicio, datetime):
            fecha_str = fecha_inicio.strftime("%Y-%m-%d %H:%M")
        else:
            fecha_str = "Sin fecha"
        texto += f"{indice}) {titulo} - {descripcion} (Inicio: {fecha_str})\n"

    await mensaje.reply_text(texto)

'''
---------------------------------------------------------------------------
Función para iniciar la eliminación de recordatorios
---------------------------------------------------------------------------
'''
async def eliminar_recordatorios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    mensaje = update.message if update.message else update.callback_query.message
    if not get_user(user_id):
        await mensaje.reply_text("Primero debes registrarte con /register.")
        return

    lista = obtener_recordatorios(user_id)
    if not lista:
        await mensaje.reply_text("No tienes recordatorios para eliminar.")
        return

    teclado = []
    for indice, recordatorio in enumerate(lista, start=1):
        titulo = recordatorio.get("titulo", "Sin título")
        # Aquí formamos el callback_data para identificar
        # cuál recordatorio se elimina
        callback_data = f"eliminar_{str(recordatorio['_id'])}"
        teclado.append([InlineKeyboardButton(f"{indice}) {titulo}", callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(teclado)
    await mensaje.reply_text("Selecciona el recordatorio que deseas eliminar:", reply_markup=reply_markup)

'''
---------------------------------------------------------------------------
Callback para procesar la eliminación de un recordatorio
---------------------------------------------------------------------------
'''
async def procesar_eliminar_recordatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    usuario = get_user(user_id)

    if data.startswith("eliminar_"):
        recordatorio_id = data[len("eliminar_"):]
        # 1) Eliminar en la BD
        resultado = eliminar_recordatorio_por_id(recordatorio_id)
        if resultado.deleted_count > 0:
            # 2) Cancelar job en job_queue
            cancelar_job_por_record_id(context, recordatorio_id)

            await query.edit_message_text("Recordatorio eliminado.")
            print(f"El usuario {usuario} ha eliminado su recordatorio con ID {recordatorio_id}.")
        else:
            await query.edit_message_text("No se pudo eliminar el recordatorio.")
    else:
        await query.edit_message_text("Opción no reconocida.")
