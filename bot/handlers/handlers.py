from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
#from config import info, admin_chat_id
from aiogram.fsm.context import FSMContext


import bot.keyboards as kb
#import bot.database.requests as rq

router = Router()

class Reg(StatesGroup):
    name = State()
    number = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    #await rq.set_user(message.from_user.id, str(message.from_user.username), message.chat.id)
    await message.reply("Вітаємо у нашому магазині", reply_markup=kb.main)


@router.message(F.text == 'Наші послуги')
async def catalog(message: Message):
    await message.answer("Виберіть послугу, що вас цікавить:", reply_markup=await kb.categories())

# @router.message(F.text == 'Про нас')
# async def catalog(message: Message):
#     await message.answer(info, reply_markup=await kb.back_to_main())

@router.callback_query(F.data.startswith('categories'))
async def category(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Виберіть послугу, що вас цікавить:", reply_markup=await kb.categories())

# @router.callback_query(F.data.startswith('item_'))
# async def category(callback: CallbackQuery):
#     item_id   = int(callback.data.split("_")[1])
#     item_data = await rq.get_item(item_id)
#     await callback.answer("Ви вибрали товар")
#     await callback.message.edit_text(f'{item_data.name}\nЦіна: {item_data.price}грн\nОпис: {item_data.description}', reply_markup=await kb.item(item_data.category, item_id))
#
# @router.callback_query(F.data.startswith('operation'))
# async def buy(callback: CallbackQuery):
#     item_data = await rq.get_item(int(callback.data.split("_")[1]))
#     if callback.data.startswith("operationbuy"): keyword = "покупку"
#     else: keyword = "оренду"
#     await callback.answer("Повідомлення адміну надіслано")
#     await callback.bot.send_message(chat_id=admin_chat_id, text=f"Нове замовлення на {keyword} {item_data.name}")
#     await callback.message.edit_text("Замовлення успішно виконано. Чекайте повідомлення від адміністратора", reply_markup= await kb.back_to_categories())


@router.callback_query(F.data =='back_to_main')
async def category(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("Головна:", reply_markup= kb.main)


@router.callback_query(F.data =='category_2')
async def category(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Магазин", reply_markup=await kb.items(2))


#Add in db for items new collumn(available)
@router.callback_query(F.data =='category_1')
async def category(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Доступні велосипеди для прокату:", reply_markup=await kb.items(1))