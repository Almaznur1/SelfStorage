import logging
from dotenv import load_dotenv

import aiosqlite
import qrcode
from datetime import date, datetime, timedelta
import calendar

import os
import common_helper_functions as chf
from typing import Dict
from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]
if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

OK_PD, NOT_PD, CHOOSING, TYPING_REPLY, TYPING_CHOICE, START_ROUTES, END_ROUTES, FIO, ADRESS, CHARACTERISTICS, \
COMMENT, END_DATE, OK_DE, NOT_DE, DELIVERY, SEL_QR, LOAD1, LOAD2, LOAD3, LOAD4, LOAD5, LOAD6, LOAD7, LOAD8, LOAD9, \
LOAD10 = range(26)

ORD0, ORD1, ORD2, ORD3, ORD4, ORD5, ORD6, ORD7, ORD8, ORD9, ORD10 = range(11)
ORD01, ORD11, ORD21, ORD31, ORD41, ORD51, ORD61, ORD71, ORD81, ORD91, ORD101 = range(11)

DELIVERY_BY_COURIER = 0
FINAL_DATE = (1, 1, 1)
BEGIN_DATE = date(1, 1, 1)
TEXT_COMMENT = ' '
SPACE_FLOAT = 0
WEIGHT_FLOAT = 0
TEXT_ADRESS = ' '
TEXT_FIO = ' '
CHAT_ID = ' '
COUNT_MONTH = 1

reply_keyboard = [
    ["Помощь", "Рассчитать заказ"],
    ["Мои Заказы", "Контакты"],
    ["Выйти из бота"],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                             resize_keyboard=True, input_field_placeholder="Выберите категорию")


async def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


async def create_connection():
    db = await aiosqlite.connect(chf.user_db)
    cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects';")
    if not await cursor.fetchone():
        await cursor.execute(chf.sql_create_ssf_table)
    return cursor, db


async def close_connection(conn):
    await conn[0].close()
    await conn[1].close()


async def add_event(n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13):  # Вставляем данные в таблицу
    event_ = (None, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13)
    async with aiosqlite.connect(chf.user_db) as db:
        await db.execute('INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', event_)
        await db.commit()


async def creat_qr(text_qr, name_file):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4, )
    qr.add_data(text_qr)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(name_file)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""
    await update.message.reply_text(chf.text_start, parse_mode="html", reply_markup=markup)
    return CHOOSING


async def regular_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global CHAT_ID, ORD1, ORD2, ORD3, ORD4, ORD5, ORD6, ORD7, ORD8, ORD9, ORD10, \
        ORD11, ORD21, ORD31, ORD41, ORD51, ORD61, ORD71, ORD81, ORD91, ORD101
    """Ask the user for info about the selected predefined choice."""
    """Запросите у пользователя информацию о выбранном предопределенном выборе."""
    text = update.message.text
    context.user_data["choice"] = text
    if text == 'Помощь':
        await update.message.reply_text(chf.text_help, parse_mode="html")
        return CHOOSING  # TYPING_REPLY

    if text == 'Рассчитать заказ':
        keyboard = [
            [
                InlineKeyboardButton("Да", callback_data=str(OK_PD)),
                InlineKeyboardButton("Нет", callback_data=str(NOT_PD)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "Создавая заказ вы соглашаетесь на обработку персональных данных. \n <b>" \
               "Я согласен на обработку персональных данных.</b>"
        await update.message.reply_text(text=text, parse_mode="html", reply_markup=reply_markup)
        return START_ROUTES

    if text == 'Мои Заказы':
        CHAT_ID = update.message.chat.id
        ch_id = (str(CHAT_ID), )
        conn = await create_connection()
        await conn[0].execute('SELECT * FROM projects WHERE chat_id=?', ch_id)
        list_ord = await conn[0].fetchall()  # возвращается кортеж
        await close_connection(conn)
        keyboard = []

        n = 1
        for order in list_ord:
            if n == 1:
                ORD11 = order[0]
                btn = InlineKeyboardButton('Ордер N' + str(order[0]) + '.  ' + order[10], callback_data=str(ORD1))
            if n == 2:
                ORD21 = order[0]
                btn = InlineKeyboardButton('Ордер N' + str(order[0]) + '.  ' + order[10], callback_data=str(ORD2))
            if n == 3:
                ORD31 = order[0]
                btn = InlineKeyboardButton('Ордер N' + str(order[0]) + '.  ' + order[10], callback_data=str(ORD3))
            if n == 4:
                ORD41 = order[0]
                btn = InlineKeyboardButton('Ордер N' + str(order[0]) + '.  ' + order[10], callback_data=str(ORD4))
            if n == 5:
                ORD51 = order[0]
                btn = InlineKeyboardButton('Ордер N' + str(order[0]) + '.  ' + order[10], callback_data=str(ORD5))
            if n == 6:
                ORD61 = order[0]
                btn = InlineKeyboardButton('Ордер N' + str(order[0]) + '.  ' + order[10], callback_data=str(ORD6))
            if n == 7:
                ORD71 = order[0]
                btn = InlineKeyboardButton('Ордер N' + str(order[0]) + '.  ' + order[10], callback_data=str(ORD7))
            if n == 8:
                ORD81 = order[0]
                btn = InlineKeyboardButton('Ордер N' + str(order[0]) + '.  ' + order[10], callback_data=str(ORD8))
            if n == 9:
                ORD91 = order[0]
                btn = InlineKeyboardButton('Ордер N' + str(order[0]) + '.  ' + order[10], callback_data=str(ORD9))
            if n == 10:
                ORD101 = order[0]
                btn = InlineKeyboardButton('Ордер N' + str(order[0]) + '.  ' + order[10], callback_data=str(ORD10))

            keyboard.insert(0, [btn])
            n = n + 1

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "Сформировать QR код для доступпа к ячейке хранения на основании номера ордера"
        if len(list_ord) == 0:
            text = 'У вас нет текущих заказов'
            await update.message.reply_text(text=text, parse_mode="html")
            return CHOOSING
        await update.message.reply_text(text=text, parse_mode="html", reply_markup=reply_markup)
        return SEL_QR


async def qr1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD11
    name_file = f'./{ORD11}.png'
    await creat_qr(ORD11, name_file)
    query = update.callback_query
    text = " <b>Чтобы обойти защиту Телеграмм от спама Вы должны отправить номер заказа </b>"
    await query.edit_message_text(text=text, parse_mode="html")
    return LOAD1


async def qr11(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD11
    await context.bot.send_document(chat_id=update.message['chat']['id'], document=open(
        f'{str(ORD11)}.png', 'rb'), filename=f'./{str(ORD11)}.png')
    os.remove(f'./{str(ORD11)}.png')
    return CHOOSING


async def qr2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD21
    name_file = f'./{ORD21}.png'
    await creat_qr(ORD21, name_file)
    query = update.callback_query
    text = " <b>Чтобы обойти защиту Телеграмм от спама Вы должны отправить номер заказа </b>"
    await query.edit_message_text(text=text, parse_mode="html")
    return LOAD2


async def qr21(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD21
    await context.bot.send_document(chat_id=update.message['chat']['id'], document=open(
        f'{str(ORD21)}.png', 'rb'), filename=f'./{str(ORD21)}.png')
    os.remove(f'./{str(ORD21)}.png')
    return CHOOSING


async def qr3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD31
    name_file = f'./{ORD31}.png'
    await creat_qr(ORD31, name_file)
    query = update.callback_query
    text = " <b>Чтобы обойти защиту Телеграмм от спама Вы должны отправить номер заказа </b>"
    await query.edit_message_text(text=text, parse_mode="html")
    return LOAD3


async def qr31(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD31
    await context.bot.send_document(chat_id=update.message['chat']['id'], document=open(
        f'{str(ORD31)}.png', 'rb'), filename=f'./{str(ORD31)}.png')
    os.remove(f'./{str(ORD31)}.png')
    return CHOOSING


async def qr4(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD41
    name_file = f'./{ORD41}.png'
    await creat_qr(ORD41, name_file)
    query = update.callback_query
    text = " <b>Чтобы обойти защиту Телеграмм от спама Вы должны отправить номер заказа </b>"
    await query.edit_message_text(text=text, parse_mode="html")
    return LOAD4


async def qr41(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD41
    await context.bot.send_document(chat_id=update.message['chat']['id'], document=open(
        f'{str(ORD41)}.png', 'rb'), filename=f'./{str(ORD41)}.png')
    os.remove(f'./{str(ORD41)}.png')
    return CHOOSING


async def qr5(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD51
    name_file = f'./{ORD51}.png'
    await creat_qr(ORD51, name_file)
    query = update.callback_query
    text = " <b>Чтобы обойти защиту Телеграмм от спама Вы должны отправить номер заказа </b>"
    await query.edit_message_text(text=text, parse_mode="html")
    return LOAD5


async def qr51(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD51
    await context.bot.send_document(chat_id=update.message['chat']['id'], document=open(
        f'{str(ORD51)}.png', 'rb'), filename=f'./{str(ORD51)}.png')
    os.remove(f'./{str(ORD51)}.png')
    return CHOOSING


async def qr6(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD61
    name_file = f'./{ORD61}.png'
    await creat_qr(ORD61, name_file)
    query = update.callback_query
    text = " <b>Чтобы обойти защиту Телеграмм от спама Вы должны отправить номер заказа </b>"
    await query.edit_message_text(text=text, parse_mode="html")
    return LOAD6


async def qr61(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD61
    await context.bot.send_document(chat_id=update.message['chat']['id'], document=open(
        f'{str(ORD61)}.png', 'rb'), filename=f'./{str(ORD61)}.png')
    os.remove(f'./{str(ORD61)}.png')
    return CHOOSING


async def qr7(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD71
    name_file = f'./{ORD71}.png'
    await creat_qr(ORD71, name_file)
    query = update.callback_query
    text = " <b>Чтобы обойти защиту Телеграмм от спама Вы должны отправить номер заказа </b>"
    await query.edit_message_text(text=text, parse_mode="html")
    return LOAD7


async def qr71(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD71
    await context.bot.send_document(chat_id=update.message['chat']['id'], document=open(
        f'{str(ORD71)}.png', 'rb'), filename=f'./{str(ORD71)}.png')
    os.remove(f'./{str(ORD71)}.png')
    return CHOOSING


async def qr8(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD81
    name_file = f'./{ORD81}.png'
    await creat_qr(ORD81, name_file)
    query = update.callback_query
    text = " <b>Чтобы обойти защиту Телеграмм от спама Вы должны отправить номер заказа </b>"
    await query.edit_message_text(text=text, parse_mode="html")
    return LOAD8


async def qr81(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD81
    await context.bot.send_document(chat_id=update.message['chat']['id'], document=open(
        f'{str(ORD81)}.png', 'rb'), filename=f'./{str(ORD81)}.png')
    os.remove(f'./{str(ORD81)}.png')
    return CHOOSING


async def qr9(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD91
    name_file = f'./{ORD91}.png'
    await creat_qr(ORD91, name_file)
    query = update.callback_query
    text = " <b>Чтобы обойти защиту Телеграмм от спама Вы должны отправить номер заказа </b>"
    await query.edit_message_text(text=text, parse_mode="html")
    return LOAD9


async def qr91(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD91
    await context.bot.send_document(chat_id=update.message['chat']['id'], document=open(
        f'{str(ORD91)}.png', 'rb'), filename=f'./{str(ORD91)}.png')
    os.remove(f'./{str(ORD91)}.png')
    return CHOOSING


async def qr10(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD101
    name_file = f'./{ORD101}.png'
    await creat_qr(ORD101, name_file)
    query = update.callback_query
    text = " <b>Чтобы обойти защиту Телеграмм от спама Вы должны отправить номер заказа </b>"
    await query.edit_message_text(text=text, parse_mode="html")
    return LOAD10


async def qr101(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global ORD101
    await context.bot.send_document(chat_id=update.message['chat']['id'], document=open(
        f'{str(ORD101)}.png', 'rb'), filename=f'./{str(ORD101)}.png')
    os.remove(f'./{str(ORD101)}.png')
    return CHOOSING


async def status_pd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [
            InlineKeyboardButton("Да", callback_data=str(OK_PD)),
            InlineKeyboardButton("Нет", callback_data=str(NOT_PD)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "Создавая заказ вы соглашаетесь на обработку персональных данных. \n <b>" \
           "Я согласен на обработку персональных данных.</b>"
    await update.message.reply_text(text=text, parse_mode="html", reply_markup=reply_markup)
    return START_ROUTES


async def ok_pd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    text = "Начнем заполнять анкету\n <b>" \
           "Введите полностью ваши фамилию Имя Отчество</b>"
    await query.edit_message_text(text=text, parse_mode="html")

    return FIO


async def fio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global TEXT_FIO, CHAT_ID, BEGIN_DATE
    TEXT_FIO = update.message.text
    CHAT_ID = update.message.chat.id
    BEGIN_DATE = update.message.date

    query = update.message

    text = " <b> Введите Ваш адрес и телефон для связи</b> "
    await query.reply_text(text=text, parse_mode="html")


    return ADRESS


async def adress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global TEXT_ADRESS
    TEXT_ADRESS = update.message.text

    query = update.message

    text = "  Введите примерные данные  в формате <b>объем / вес</b>.  Данные передать в метрах кубических и килограммах. " \
           "Если не можете рассчитать введите: <b> 0 / 0 </b> мы сами все измерим и скажем цену при сдаче вещей"
    await query.reply_text(text=text, parse_mode="html")
    return CHARACTERISTICS


async def characteristics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global SPACE_FLOAT, WEIGHT_FLOAT
    text_characteristics = update.message.text
    try:
        SPACE_FLOAT = int(text_characteristics.partition('/')[0].replace(' ', ''))  # объем хранимых вещей
    except:
        SPACE_FLOAT = 1
    try:
        WEIGHT_FLOAT = int(text_characteristics.partition('/')[2].replace(' ', ''))  # вес хранимых вещей
    except:
        WEIGHT_FLOAT = 1

    query = update.message
    text = " <b>  Введите комментарий - обычно список вещей, ключевое слово - чтобы понять что сдали и т.д.</b>"
    await query.reply_text(text=text, parse_mode="html")

    return COMMENT


async def comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global TEXT_COMMENT
    TEXT_COMMENT = update.message.text
    query = update.message
    text = " <b>  Введите количество месяцев хранения (максимум 12).</b>"
    await query.reply_text(text=text, parse_mode="html")
    return END_DATE


async def enddate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global FINAL_DATE, BEGIN_DATE
    try:
        COUNT_MONTH = int(update.message.text.replace(' ', ''))
        if COUNT_MONTH > 12:
            COUNT_MONTH = 12
    except:
        COUNT_MONTH = 12

    FINAL_DATE = await add_months(BEGIN_DATE, COUNT_MONTH)

    keyboard = [
        [
            InlineKeyboardButton("Да", callback_data=str(OK_DE)),
            InlineKeyboardButton("Нет", callback_data=str(NOT_DE)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = " <b> Я привезу свои вещи сам.</b>"
    await update.message.reply_text(text=text, parse_mode="html", reply_markup=reply_markup)
    # query = update.callback_query
    # await query.answer()

    return DELIVERY


async def ok_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global DELIVERY_BY_COURIER, FINAL_DATE, BEGIN_DATE, TEXT_COMMENT, SPACE_FLOAT, WEIGHT_FLOAT, TEXT_ADRESS, \
        TEXT_FIO, CHAT_ID, COUNT_MONTH
    DELIVERY_BY_COURIER = 0
    price_float = SPACE_FLOAT * COUNT_MONTH * 2000
    query = update.callback_query

    text = 'Ваши данные обрабатываются: \n\n' \
           f'ФИО: {TEXT_FIO} \n' \
           f'Адрес: {TEXT_ADRESS} \n' \
           f'Объем: {SPACE_FLOAT} м.кв. \n' \
           f'Срок хранения {COUNT_MONTH} мес. \n' \
           'Доставка Заказчиком самостоятельно \n' \
           f'Расчетная стоимость: {price_float} рублей \n\n' \
           '<b> С Вами в ближайшее время свяжется наш сотрудник для уточнения деталей </b>'
    await query.edit_message_text(text=text, parse_mode="html")

    conn = await create_connection()
    await add_event('', CHAT_ID, TEXT_FIO, TEXT_ADRESS, '', '', BEGIN_DATE, FINAL_DATE, SPACE_FLOAT, WEIGHT_FLOAT,
                    TEXT_COMMENT, price_float, DELIVERY_BY_COURIER)
    await close_connection(conn)
    return CHOOSING


async def not_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global DELIVERY_BY_COURIER, FINAL_DATE, BEGIN_DATE, TEXT_COMMENT, SPACE_FLOAT, WEIGHT_FLOAT, TEXT_ADRESS, \
        TEXT_FIO, CHAT_ID, COUNT_MONTH
    DELIVERY_BY_COURIER = 1
    price_float = SPACE_FLOAT * COUNT_MONTH * 2000
    query = update.callback_query

    text = 'Ваши данные обрабатываются: \n\n' \
           f'ФИО: {TEXT_FIO} \n' \
           f'Адрес: {TEXT_ADRESS} \n' \
           f'Объем: {SPACE_FLOAT} м.кв. \n' \
           f'Срок хранения {COUNT_MONTH} мес. \n' \
           'Доставка бесплатно курьером \n' \
           f'Расчетная стоимость: {price_float} рублей \n\n' \
           '<b> С Вами в ближайшее время свяжется наш сотрудник для уточнения деталей </b>'
    await query.edit_message_text(text=text, parse_mode="html")

    conn = await create_connection()
    await add_event('', CHAT_ID, TEXT_FIO, TEXT_ADRESS, '', '', BEGIN_DATE, FINAL_DATE, SPACE_FLOAT, WEIGHT_FLOAT,
                    TEXT_COMMENT, price_float, DELIVERY_BY_COURIER)
    await close_connection(conn)
    return CHOOSING


async def not_pd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    text = "Без вашего согласия мы не можем оказать услугу\n <b>" \
           "Попробуйте переосмыслить свою позицию</b>"
    await query.edit_message_text(text=text, parse_mode="html")
    return CHOOSING


async def custom_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for a description of a custom category."""
    """Запросите у пользователя описание пользовательской категории."""

    await update.message.reply_text(chf.text_Contacts)
    return TYPING_CHOICE


async def received_information(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store info provided by user and ask for the next category."""
    """Сохранить информацию, предоставленную пользователем, и запросить следующую категорию."""

    user_data = context.user_data
    text = update.message.text
    category = user_data["choice"]
    user_data[category] = text
    del user_data["choice"]

    await update.message.reply_text(
        "Пожалуйста, внимательнее. Скорее всего неправомерный ввод или двойной клик на меню",
        reply_markup=markup,
    )
    return CHOOSING


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the gathered info and end the conversation."""
    """Показать собранную информацию и завершить разговор."""

    user_data = context.user_data
    if "choice" in user_data:
        del user_data["choice"]

    await update.message.reply_text("Работа бота завершена. Чтобы возобновить наберите /start", reply_markup=ReplyKeyboardRemove(),)
    user_data.clear()
    return ConversationHandler.END


def main() -> None:

    """Run the bot."""
    # Create the Application and pass it your bot's token.
    load_dotenv()
    telegram_token = os.environ["TELEGRAM_TOKEN"]
    application = Application.builder().token(telegram_token).build()

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    # Добавить обработчик диалога с состояниями ВЫБОР,    ВВОД ВЫБОРА  и   ВВОД ОТВЕТА

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(ok_pd, pattern="^" + str(OK_PD) + "$"),
                CallbackQueryHandler(not_pd, pattern="^" + str(NOT_PD) + "$")
            ],
            DELIVERY: [
                CallbackQueryHandler(ok_delivery, pattern="^" + str(OK_DE) + "$"),
                CallbackQueryHandler(not_delivery, pattern="^" + str(NOT_DE) + "$"),
            ],
            CHOOSING: [MessageHandler(filters.Regex("^(Помощь|Рассчитать заказ|Мои Заказы)$"), regular_choice),
                       MessageHandler(filters.Regex("^Контакты$"), custom_choice), ],
            TYPING_CHOICE: [MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^Выйти из бота$")), regular_choice)],
            TYPING_REPLY: [MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^Выйти из бота$")), received_information, )],
            FIO: [MessageHandler(filters.TEXT, fio)],
            ADRESS: [MessageHandler(filters.TEXT, adress)],
            CHARACTERISTICS: [MessageHandler(filters.TEXT, characteristics)],
            COMMENT: [MessageHandler(filters.TEXT, comment)],
            END_DATE: [MessageHandler(filters.TEXT, enddate)],
            LOAD1: [MessageHandler(filters.TEXT, qr11)],
            LOAD2: [MessageHandler(filters.TEXT, qr21)],
            LOAD3: [MessageHandler(filters.TEXT, qr31)],
            LOAD4: [MessageHandler(filters.TEXT, qr41)],
            LOAD5: [MessageHandler(filters.TEXT, qr51)],
            LOAD6: [MessageHandler(filters.TEXT, qr61)],
            LOAD7: [MessageHandler(filters.TEXT, qr71)],
            LOAD8: [MessageHandler(filters.TEXT, qr81)],
            LOAD9: [MessageHandler(filters.TEXT, qr91)],
            LOAD10: [MessageHandler(filters.TEXT, qr101)],
            SEL_QR: [
                CallbackQueryHandler(qr1, pattern="^" + str(ORD1) + "$"),
                CallbackQueryHandler(qr2, pattern="^" + str(ORD2) + "$"),
                CallbackQueryHandler(qr3, pattern="^" + str(ORD3) + "$"),
                CallbackQueryHandler(qr4, pattern="^" + str(ORD4) + "$"),
                CallbackQueryHandler(qr5, pattern="^" + str(ORD5) + "$"),
                CallbackQueryHandler(qr6, pattern="^" + str(ORD6) + "$"),
                CallbackQueryHandler(qr7, pattern="^" + str(ORD7) + "$"),
                CallbackQueryHandler(qr8, pattern="^" + str(ORD8) + "$"),
                CallbackQueryHandler(qr9, pattern="^" + str(ORD9) + "$"),
                CallbackQueryHandler(qr10, pattern="^" + str(ORD10) + "$")
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^Выйти из бота$"), done)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()