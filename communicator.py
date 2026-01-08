import asyncio
import pytz
from datetime import datetime
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from drawer_configurator import draw_payment_receipt, draw_error_receipt

# === НАСТРОЙКИ ===
BOT_TOKEN = ":"
ALLOWED_USER_IDS = {, }

# === ИНИЦИАЛИЗАЦИЯ ===
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# === СОСТОЯНИЯ ===
class PaymentStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_name = State()
    waiting_for_contact = State()

class ErrorStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_contact = State()

# === МЕНЮ ===
async def show_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Создать чек об оплате", callback_data="payment")],
    ])
    await message.answer("Выберите действие:", reply_markup=keyboard)

# === /start и /menu ===
@router.message(F.text.in_({"/start", "/menu"}))
async def start_menu_handler(message: Message):
    if message.from_user.id not in ALLOWED_USER_IDS:
        return await message.answer("⛔ Доступ ограничен.")
    await show_menu(message)

# === КНОПКИ ===
@router.callback_query()
async def process_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id not in ALLOWED_USER_IDS:
        return await callback.answer("⛔ Доступ ограничен.", show_alert=True)

    if callback.data == "payment":
        await state.set_state(PaymentStates.waiting_for_amount)
        await callback.message.answer("Введите сумму (в CAD):")
    await callback.answer()

# === ЧЕК ОБ ОПЛАТЕ ===
@router.message(PaymentStates.waiting_for_amount)
async def payment_amount_entered(message: Message, state: FSMContext):
    try:
        float(message.text)
    except ValueError:
        return await message.answer("❌ Введите корректную сумму (например, 250.50)")
    await state.update_data(amount=message.text)
    await message.answer("Введите имя получателя:")
    await state.set_state(PaymentStates.waiting_for_name)

@router.message(PaymentStates.waiting_for_name)
async def payment_name_entered(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Теперь введите почту или телефон получателя:")
    await state.set_state(PaymentStates.waiting_for_contact)

@router.message(PaymentStates.waiting_for_contact)
async def payment_contact_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get("amount")
    name = data.get("name")
    contact = message.text
    tz = pytz.timezone("America/Toronto")
    current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    await message.answer("⏳ Генерация чека...")
    await draw_payment_receipt(message, bot, amount, contact, current_time, name)
    await state.clear()

# === СТАРТ БОТА ===
async def main():
    print("✅ SYMPATICO BITCH")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
