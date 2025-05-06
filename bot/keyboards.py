from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.database.models import Experiment, Parameter


main = ReplyKeyboardMarkup(keyboard = [[KeyboardButton(text = "Наші послуги")],
                                        [KeyboardButton(text = "Про нас")]] ,
                                        #[KeyboardButton(text = "Наш канал")]],
                            resize_keyboard = True,
                           input_field_placeholder="Вітаю!!! Виберіть пункт меню")

BOOLEAN_CLASS_NUMERIC = InlineKeyboardMarkup(inline_keyboard=[
    [
      InlineKeyboardButton(text="Boolean", callback_data="type_boolean"),
      InlineKeyboardButton(text="Class",   callback_data="type_class"),
      InlineKeyboardButton(text="Numeric", callback_data="type_numeric"),
    ]
])

ADD_PARAMETER = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Add parameter", callback_data="add_parameter")]])

ROLE = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Independent", callback_data="role_independent"),
        InlineKeyboardButton(text="Goal", callback_data="role_goal"),
    ]
])

CREATE = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Create", callback_data="exp_confirm")]])

CANCEL_CONFIRM = InlineKeyboardMarkup(inline_keyboard=
[
    [InlineKeyboardButton(text="✅ Confirm", callback_data="confirm")],
    [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
])

CREATE_FINISH = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Create another parameter", callback_data="add_parameter")],
    [InlineKeyboardButton(text="Finish", callback_data="finish")]
])

DELETE_CONFIRM = InlineKeyboardMarkup(inline_keyboard=[
    [
      InlineKeyboardButton(text="✅ Yes, delete", callback_data="del_confirm:yes"),
      InlineKeyboardButton(text="❌ No, cancel", callback_data="del_confirm:no"),
    ]
])

async def back_to_main():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))

    return keyboard.as_markup()

async def back_to_categories():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="categories"))

    return keyboard.as_markup()
async def item(category_id, item_id):
    keyboard = InlineKeyboardBuilder()
    if category_id == 1:
        keyboard.add(InlineKeyboardButton(text="Орендувати", callback_data=f"operationrent_{item_id}"))
    else:
        keyboard.add(InlineKeyboardButton(text="Купити", callback_data=f"operationbuy_{item_id}"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data=f"category_{category_id}"))
    return keyboard.as_markup()

async def user_experiments_list(experiments: list[Experiment]):
    keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [ InlineKeyboardButton(text=exp.name, callback_data=f"sel_exp:{exp.id}") ]
                for exp in experiments
            ]
        )
    return keyboard

async def parameter_list(params: list[Parameter]):
    keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=p.name, callback_data=f"sel_param:{p.id}")]
                for p in params
            ] + [[InlineKeyboardButton(text="✅ Done", callback_data="finish")]]
        )
    return keyboard

async def enter_parameter_list(params: list[Parameter], entered_keys: set[str]):
    buttons = []
    for p in params:
        prefix = "✅" if p.name in entered_keys else "❓"
        text = f"{prefix} {p.name}"
        buttons.append([InlineKeyboardButton(text=text,
                                             callback_data=f"sel_param:{p.id}")])
        # finally the Done button
    buttons.append([InlineKeyboardButton(text="🏁 Done", callback_data="finish")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
