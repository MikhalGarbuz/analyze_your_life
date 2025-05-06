from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.states import DeleteExp
import bot.keyboards as kb
import core.database.requests as rq

from . import router

@router.message(Command("delete"))
async def cmd_delete(message: Message, state: FSMContext):
    exps = await rq.get_list_experiments(message.from_user.id)
    if not exps:
        return await message.answer("🗑 You have no experiments to delete.")
    await state.set_state(DeleteExp.SELECT)
    await message.answer("🗑 Select an experiment to delete:", reply_markup=await kb.user_experiments_list(exps))

@router.callback_query(DeleteExp.SELECT, F.data.startswith("sel_exp:"))
async def ask_delete_confirm(query: CallbackQuery, state: FSMContext):
    await query.answer()
    exp_id = int(query.data.split(":", 1)[1])
    await state.update_data(exp_id=exp_id)
    await state.set_state(DeleteExp.CONFIRM)

    # fetch for a nicer prompt
    exp = await rq.get_experiment(exp_id)
    await query.message.edit_text(
        f"❗ Are you sure you want to permanently delete *{exp.name}*?",
        parse_mode="Markdown",
        reply_markup=kb.DELETE_CONFIRM
    )

@router.callback_query(DeleteExp.CONFIRM, F.data.startswith("del_confirm:"))
async def do_delete(query: CallbackQuery, state: FSMContext):
    await query.answer()  # dismiss the button loading
    choice = query.data.split(":",1)[1]  # "yes" or "no"
    data = await state.get_data()

    if choice == "yes":
        await rq.delete_experiment(data["exp_id"])
        await query.message.edit_text("✅ Experiment deleted.")
    else:
        await query.message.edit_text("❌ Deletion canceled.")

    await state.clear()
