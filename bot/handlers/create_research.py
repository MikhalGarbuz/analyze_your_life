from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from core.database.requests import add_parameter, add_experiment, get_list_parameters
from core.database.models import ParamType
from handlers import router
from bot.states import DefineParam, DefineExp
from bot.keyboards import BOOLEAN_CLASS_NUMERIC, ROLE, CREATE, CANCEL_CONFIRM, CREATE_FINISH


@router.message(Command("new"))
async def cmd_new(message, state: FSMContext):
    await message.answer("🆕 Enter a name for your new experiment:")
    await state.set_state(DefineExp.NAME)

@router.message(DefineExp.NAME)
async def exp_name(message, state):
    await state.update_data(exp_name=message.text)
    await message.answer(f"Create experiment “{message.text}”?", reply_markup=CREATE)
    await state.set_state(DefineExp.CONFIRM)

@router.callback_query(DefineExp.CONFIRM, F.data=="exp_confirm")
async def exp_confirm(query, state):
    data = await state.get_data()
    exp = await add_experiment(query.from_user.id, data["exp_name"])
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Add parameter", callback_data="add_parameter")]])
    await query.edit_message_text(f"Experiment “{exp.name}” created (ID={exp.id})", reply_markup=kb)
    # save current experiment in user_data
    await state.update_data(exp_id=exp.id)
    await state.clear()  # we’ll keep exp_id in user_data

@router.message(F.data=="add_parameter")
async def cmd_define(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if "exp_id" not in data:
        return await query.message.answer("❗ You need to create an experiment first. Use /new")
    await state.set_state(DefineParam.NAME)
    await query.edit_message_text("📐 What is the **name** of your new parameter?", parse_mode="Markdown")

@router.message(DefineParam.NAME)
async def define_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(DefineParam.ROLE)
    await message.answer("Is it an independent or goal parameter?", reply_markup=ROLE)

@router.callback_query(DefineParam.ROLE, F.data.startswith("role_"))
async def define_role(query: CallbackQuery, state: FSMContext):
    role = query.data.split("_")[1]
    await state.update_data(is_goal=(role == "goal"))
    await query.answer()
    await state.set_state(DefineParam.TYPE)
    await query.message.edit_text("Choose the parameter type:", reply_markup=BOOLEAN_CLASS_NUMERIC)

@router.callback_query(DefineParam.TYPE, F.data.startswith("type_"))
async def define_type(query: CallbackQuery, state: FSMContext):
    t = query.data.split("_")[1]
    ptype = ParamType[t.upper()]
    await state.update_data(ptype=ptype)
    await query.answer()
    if ptype == ParamType.CLASS:
        await state.set_state(DefineParam.CLASS_MIN)
        await query.message.edit_text("Enter **minimum** class value:", parse_mode="Markdown")
    else:
        # skip straight to confirmation
        await _confirm_param(query.message, state)

@router.message(DefineParam.CLASS_MIN)
async def define_class_min(message: Message, state: FSMContext):
    await state.update_data(class_min=int(message.text))
    await state.set_state(DefineParam.CLASS_MAX)
    await message.answer("Enter **maximum** class value:", parse_mode="Markdown")

@router.message(DefineParam.CLASS_MAX)
async def define_class_max(message: Message, state: FSMContext):
    await state.update_data(class_max=int(message.text))
    # move to confirmation
    await _confirm_param(message, state)

async def _confirm_param(target, state: FSMContext):
    data = await state.get_data()
    text = (
        f"Please confirm:\n"
        f"• Name: `{data['name']}`\n"
        f"• Role:  {'Goal' if data['is_goal'] else 'Independent'}\n"
        f"• Type:  `{data['ptype'].value}`\n"
    )
    if data['ptype'] == ParamType.CLASS:
        text += f"• Range: `{data['class_min']}–{data['class_max']}`\n"
    await state.set_state(DefineParam.CONFIRM)
    await target.answer(text, parse_mode="Markdown", reply_markup=CANCEL_CONFIRM)

@router.callback_query(DefineParam.CONFIRM, F.data.in_("confirm", "cancel"))
async def define_done(query: CallbackQuery, state: FSMContext):
    if query.data == "confirm":
        data = await state.get_data()
        user_id = query.from_user.id
        await add_parameter(
            user_id=user_id,
            exp_id=data["exp_id"],
            name=data["name"],
            is_goal=data["is_goal"],
            ptype=data["ptype"],
            class_min=data.get("class_min"),
            class_max=data.get("class_max")
        )
        await query.message.edit_text("✅ Parameter saved!", reply_markup=CREATE_FINISH)
    else:
        await query.message.edit_text("❌ Creation canceled.")
    await state.clear()

@router.callback_query(DefineParam.CONFIRM, F.data.in_("finish"))
async def param_done(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    params = await get_list_parameters(data["exp_id"])
    has_goal = any(p.is_goal for p in params)
    has_indep = any(not p.is_goal for p in params)

    if not (has_goal and has_indep):
        await query.message.answer(
            "⚠️ You need at least one *goal* and one *independent* parameter.\n"
            "Keep defining more with /define."
        )
    else:
        await query.message.answer("✅ You now have a valid experiment. Use /enter to log daily data.")

    await state.clear()