import asyncio
import os
from datetime import datetime
import pytz
from PIL import Image, ImageDraw, ImageFont
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

# === ФУНКЦИЯ: вычисляет смещение, чтобы не выходить за правый край ===
def fit_text_to_right(draw, text, font, right_x, y, max_right_x):
    text_width = draw.textlength(text, font=font)
    if right_x + text_width > max_right_x:
        right_x = max_right_x - text_width
    return right_x

# === ГЕНЕРАЦИЯ ЧЕКА ===
async def generate_receipt(bot, message, template, title, amount, contact, current_time, name):
    loop = asyncio.get_event_loop()
    img = await loop.run_in_executor(None, lambda: Image.open(template).convert("RGB"))
    d = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("Arcon.otf", 53)
        font_small = ImageFont.truetype("Arcon.otf", 52)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # === ПРАВЫЕ ГРАНИЦЫ ===
    MAX_RIGHT_AMOUNT_X = 1235
    MAX_RIGHT_NAME_X = 1235
    MAX_RIGHT_EMAIL_X = 1235

    # === НАЧАЛЬНЫЕ X ===
    AMOUNT_X, AMOUNT_Y = 1075, 1465
    NAME_X, NAME_Y = 1075, 1600
    EMAIL_X, EMAIL_Y = 1075, 1750
    TIME_X, TIME_Y = 65, 22

    # === ВРЕМЯ ===
    d.text((TIME_X, TIME_Y), current_time, fill="black", font=font_small)

    # === СУММА ===
    text = f"${amount}"
    x = fit_text_to_right(d, text, font_large, AMOUNT_X, AMOUNT_Y, MAX_RIGHT_AMOUNT_X)
    d.text((x, AMOUNT_Y), text, fill="black", font=font_large)

    # === ИМЯ ===
    x = fit_text_to_right(d, name, font_large, NAME_X, NAME_Y, MAX_RIGHT_NAME_X)
    d.text((x, NAME_Y), name, fill="black", font=font_large)

    # === EMAIL ===
    x = fit_text_to_right(d, contact, font_large, EMAIL_X, EMAIL_Y, MAX_RIGHT_EMAIL_X)
    d.text((x, EMAIL_Y), contact, fill="black", font=font_large)

    # === СОХРАНЕНИЕ ===
    temp_file = "receipt.png"
    img.save(temp_file)

    # === ОТПРАВКА В ТГ ===
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Создать новый чек", callback_data="payment")]
    ])

    await bot.send_photo(chat_id=message.chat.id, photo=FSInputFile(temp_file), reply_markup=keyboard)
    os.remove(temp_file)

# === ОБЕРТКИ ДЛЯ БОТА ===
async def draw_payment_receipt(message, bot, amount, contact, current_time, name):
    tz = pytz.timezone("America/Toronto")
    current_time = datetime.now(tz).strftime("%H:%M")
    await generate_receipt(bot, message, "tt.png", "Чек об оплате", amount, contact, current_time, name)

async def draw_error_receipt(message, bot, amount, contact, current_time):
    tz = pytz.timezone("America/Toronto")
    current_time = datetime.now(tz).strftime("%H:%M")
    await generate_receipt(bot, message, "tt.png", "Чек об ошибке", amount, contact, current_time, "Error")
