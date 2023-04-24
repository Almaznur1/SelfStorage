from dotenv import load_dotenv
import logging
import os
import aiosqlite
import common_helper_functions as chf
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    CommandHandler, Application, filters,
    ConversationHandler, MessageHandler, ContextTypes
    )

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

CHOOSING, GET_ACTIVE_ORDERS, GET_OVERDUE_ORDERS, GET_AD_REPORT = range(4)


async def create_connection():
    db = await aiosqlite.connect(chf.user_db)
    cursor = await db.execute("SELECT name FROM sqlite_master WHERE "
                              "type='table' AND name='projects';")
    if not await cursor.fetchone():
        await cursor.execute(chf.sql_create_ssf_table)
    return cursor, db


async def close_connection(conn):
    await conn[0].close()
    await conn[1].close()


async def start(update, _):
    keyboard = [
        [
            KeyboardButton("Список активных заказов"),
            KeyboardButton("Просроченные заказы"),
        ],
        [KeyboardButton("Формирование отчета по рекламе")],
        [KeyboardButton("Выйти из бота")]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True,
        input_field_placeholder="Выберите категорию"
        )
    await update.message.reply_text('Пожалуйста, выберите:', reply_markup=reply_markup)
    return CHOOSING


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == 'Список активных заказов':
        conn = await create_connection()
        await conn[0].execute('SELECT chat_id, client_name, client_address '
                              'FROM projects WHERE delivery_by_courier = 1')
        list_ord = await conn[0].fetchall()
        await close_connection(conn)

        text = ''
        for client in list_ord:
            text += f'id клиетна: {client[0]}\nФИО: {client[1]}\nадрес: {client[2]}\n\n'
        text.encode('utf-8')
        await update.message.reply_text(text=text, parse_mode="html")

    if text == 'Просроченные заказы':
        conn = await create_connection()
        await conn[0].execute('SELECT chat_id, client_name, client_address, '
                              'end_date FROM projects WHERE end_date < DATE("now")')
        list_ord = await conn[0].fetchall()
        await close_connection(conn)

        text = ''
        for client in list_ord:
            text += (
                f'id клиетна: {client[0]}\nФИО: {client[1]}\nадрес: {client[2]}\nдата окончания договора: {client[3]}\n\n')
        text.encode('utf-8')

        await update.message.reply_text(text=text, parse_mode="html")

    if text == 'Формирование отчета по рекламе':
        await update.message.reply_text(
            text="Введите даты в формате: YYYY-MM-DD / YYYY-MM-DD"
            )
        return GET_AD_REPORT


async def get_ad_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # отчет по рекламе
    date_from = update.message.text[:10]
    date_to = update.message.text[13:]
    conn = await create_connection()
    await conn[0].execute('SELECT chat_id FROM projects WHERE start_date >= '
                          f'"{date_from}" AND start_date <= "{date_to}"')

    list_ord = await conn[0].fetchall()
    await close_connection(conn)

    await update.message.reply_text(
        text=f"За данный период было совершено {len(list_ord)} заказов"
        )
    return CHOOSING


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        text='для повторного запуска набери "/start"'
        )
    return ConversationHandler.END
 

if __name__ == '__main__':
    load_dotenv()
    telegram_token = os.environ["TELEGRAM_TOKEN"]
    application = Application.builder().token(telegram_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [MessageHandler(filters.Regex(
                "^(Список активных заказов|Просроченные заказы"
                "|Формирование отчета по рекламе)$"
                ), button)],
            GET_AD_REPORT: [MessageHandler(filters.TEXT, get_ad_report)],
        },
        fallbacks=[MessageHandler(filters.Regex("^Выйти из бота$"), done)],
    )

    application.add_handler(conv_handler)
    application.run_polling()