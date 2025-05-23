import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command

API_TOKEN = '7878301618:AAG8Uw6NpnwFAL1cSyakRPviSlIlI9pjzYg'
ADMIN_CHAT_ID = -1002222107724  # Заменить на ID админского чата

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher(storage=MemoryStorage())

class Form(StatesGroup):
    age = State()
    nickname = State()
    source = State()
    plans = State()

start_inline_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📝 Пройти анкету", callback_data="start_form")]
])

links_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Discord сервер", url="https://discord.gg/MczamQxGQK")],
    [InlineKeyboardButton(text="Telegram-канал", url="https://t.me/decrafted")]
])

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Добро пожаловать на сервер DeCrafted!\nНажмите кнопку ниже, чтобы пройти анкету для вступления.",
        reply_markup=start_inline_kb
    )

@dp.callback_query(F.data == "start_form")
async def handle_start_form(callback: CallbackQuery, state: FSMContext):
    # Убираем кнопку, если она есть, иначе можно пропустить
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await state.set_state(Form.age)
    await callback.message.answer("📅 Сколько вам лет?")
    await callback.answer()

@dp.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(Form.nickname)
    await message.answer("👤 Какой у вас ник в Майнкрафте?")

@dp.message(Form.nickname)
async def process_nick(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await state.set_state(Form.source)
    await message.answer("📢 Откуда вы узнали о нашем сервере?")

@dp.message(Form.source)
async def process_source(message: Message, state: FSMContext):
    await state.update_data(source=message.text)
    await state.set_state(Form.plans)
    await message.answer("🔧 Чем вы планируете заниматься на сервере?")

@dp.message(Form.plans)
async def process_plans(message: Message, state: FSMContext):
    await state.update_data(plans=message.text)
    data = await state.get_data()
    await state.clear()

    text = (
        f"Новая анкета от @{message.from_user.username or message.from_user.full_name}:\n\n"
        f"Возраст: {data['age']}\n"
        f"Ник: {data['nickname']}\n"
        f"Источник: {data['source']}\n"
        f"Планы: {data['plans']}"
    )

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"approve_{message.from_user.id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"deny_{message.from_user.id}")
        ]
    ])

    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, reply_markup=admin_kb)
    await message.answer(
        "✅ Анкета отправлена!\nОжидайте решение в течение 10 минут."
    )

@dp.callback_query(F.data.startswith("approve_"))
async def approve(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    # Отправляем пользователю сообщение с кнопками
    await bot.send_message(
        chat_id=user_id,
        text="✅ Ваша анкета одобрена!\nВы будете добавлены в вайтлист в ближайшее время.\nА пока можете подписаться на наши социальные сети!",
        reply_markup=links_kb
    )

    new_text = callback.message.text
    if "✅ Анкета одобрена" not in new_text:
        new_text += "\n\n✅ Анкета одобрена"
        try:
            await callback.message.edit_text(new_text)
        except Exception:
            # Игнорируем ошибку, если текст не изменился
            pass
    # Ответ без предупреждений, если запрос старый — ставим cache_time=0
    await callback.answer(cache_time=0)

@dp.callback_query(F.data.startswith("deny_"))
async def deny(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await bot.send_message(
        chat_id=user_id,
        text="❌ Ваша анкета отклонена.\nВы можете пройти её заново, используя команду /start.",
        reply_markup=start_inline_kb
    )
    new_text = callback.message.text
    if "❌ Анкета отклонена" not in new_text:
        new_text += "\n\n❌ Анкета отклонена"
        try:
            await callback.message.edit_text(new_text)
        except Exception:
            pass
    await callback.answer(cache_time=0)

@dp.message(F.text == "📝 Пройти анкету заново")
async def retry_form(message: Message, state: FSMContext):
    await state.set_state(Form.age)
    await message.answer("📅 Сколько вам лет?")

if __name__ == '__main__':
    asyncio.run(dp.start_polling(bot))
