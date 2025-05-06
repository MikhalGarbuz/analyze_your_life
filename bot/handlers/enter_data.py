from datetime import date

from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import EnterData
from core.database.models import ParamType
import core.database.requests as rq

import bot.keyboards as kb

from . import router

@router.message(Command("enter"))
async def cmd_enter(message: Message, state: FSMContext):
    exps = await rq.get_list_experiments(message.from_user.id)
    if not exps:
        return await message.answer("You have no experiments yet. Create one with /new")

    await state.set_state(EnterData.SELECT_EXP)
    await state.update_data(entry_date=date.today(), day_values={})
    await message.answer("🔬 Select experiment:", reply_markup=await kb.user_experiments_list(exps))


@router.message(Command("enter_past"))
async def cmd_enter_past(message: Message, state: FSMContext):
    await state.set_state(EnterData.DATE)
    await message.answer("🗓 Send me the date (YYYY-MM-DD) you want to enter data for:")


@router.message(EnterData.DATE)
async def parse_manual_date(message: Message, state: FSMContext):
    try:
        chosen = date.fromisoformat(message.text.strip())
    except ValueError:
        return await message.answer("❌ Invalid format—use YYYY-MM-DD.")

    if chosen > date.today():
        return await message.answer(
            "⚠️ Ви не можете вводити майбутню дату. Вкажіть сьогодні або ранішу.",  parse_mode="Markdown")

        # now stash & proceed exactly like /enter does
    await state.set_state(EnterData.SELECT_EXP)
    await state.update_data(entry_date=chosen, day_values={})

    exps = await rq.get_list_experiments(message.from_user.id)
    await message.answer("🔬 Select experiment:", reply_markup=await kb.user_experiments_list(exps))


@router.callback_query(EnterData.SELECT_EXP, F.data.startswith("sel_exp:"))
async def select_experiment(query: CallbackQuery, state: FSMContext):
    await query.answer()
    exp_id = int(query.data.split(":", 1)[1])
    await state.update_data(exp_id=exp_id)

    params = await rq.get_list_parameters(exp_id)
    if not params:
        return await query.message.answer("No parameters defined—add one with /define", show_alert=True)

    day_values = (await state.get_data()).get("day_values", {})


    await state.set_state(EnterData.SELECT_PARAM)
    await query.message.edit_text("✏️ Select a parameter to enter:", reply_markup=await kb.enter_parameter_list(params, set(day_values.keys())))


@router.callback_query(EnterData.SELECT_PARAM, F.data.startswith("sel_param:"))
async def select_parameter(query: CallbackQuery, state: FSMContext):
    await query.answer()
    param_id = int(query.data.split(":", 1)[1])
    await state.update_data(param_id=param_id)

    p = await rq.get_parameter(param_id)
    prompt = f"Enter value for *{p.name}*"
    if p.type == ParamType.BOOLEAN:
        prompt += " — send `+` or `-`"
    elif p.type == ParamType.CLASS:
        prompt += f" — choose {p.class_min}–{p.class_max}"
    else:
        prompt += " — send a number"

    await state.set_state(EnterData.WAIT_VALUE)
    await query.message.edit_text(prompt, parse_mode="Markdown")


@router.callback_query(EnterData.SELECT_PARAM, F.data=="finish")
async def finish_entry(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    date = data.get("entry_date")
    day_values = data.get("day_values", {})
    exp_id = data.get("exp_id")

    if not day_values:
        return await query.answer("No values entered yet!", show_alert=True)

    if not exp_id:
        return await query.answer("No experiment selected!", show_alert=True)

    # one‐shot save
    await rq.add_daily_entry( user_id=query.from_user.id, experiment_id = exp_id, entry_date=date, data=day_values)
    await query.message.edit_text("✅ All saved for today!")
    await state.clear()


# Step 4: capture the user’s value and loop back
@router.message(EnterData.WAIT_VALUE)
async def receive_value(message: Message, state: FSMContext):
    data = await state.get_data()
    param_id = data["param_id"]
    text = message.text.strip()

    p = await rq.get_parameter(param_id)

    # simple validation
    if p.type == ParamType.BOOLEAN and text not in ("+", "-"):
        return await message.answer("Send `+` or `-`.")
    if p.type == ParamType.CLASS:
        try:
            iv = int(text)
        except ValueError:
            return await message.answer("Send an integer.")
        if not (p.class_min <= iv <= p.class_max):
            return await message.answer(f"Value must be {p.class_min}–{p.class_max}.")
    if p.type == ParamType.NUMERIC:
        try:
            float(text)
        except ValueError:
            return await message.answer("Send a number.")

    # stash it in the day‐values dict
    day_values = data.get("day_values", {})
    day_values[p.name] = text
    await state.update_data(day_values=day_values)

    # go back to parameter‐selection (so they can pick another or Finish)
    params = await rq.get_list_parameters(data["exp_id"])
    day_values = (await state.get_data())["day_values"]


    await state.set_state(EnterData.SELECT_PARAM)
    await message.answer("Noted! Choose next or tap Done:", reply_markup=await kb.enter_parameter_list(params, set(day_values.keys())))