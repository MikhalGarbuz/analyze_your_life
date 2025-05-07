from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile


from bot.states import ShowStats
import bot.keyboards as kb
import core.database.requests as rq
from core.correlations import Сorrelation  # your correlation class
import pandas as pd

from . import router
from core.database.models import ParamType

@router.message(Command("correlation"))
async def cmd_correlation(message: Message, state: FSMContext):
    # 1) list experiments
    exps = await rq.get_list_experiments(message.from_user.id)
    if not exps:
        return await message.answer("❗ You have no experiments. Create one with /new")
    await state.set_state(ShowStats.SELECT_EXP)
    await message.answer("📊 Select an experiment to correlate:", reply_markup= await kb.user_experiments_list(exps))


@router.callback_query(ShowStats.SELECT_EXP, F.data.startswith("sel_exp:"))
async def choose_experiment(query: CallbackQuery, state: FSMContext):
    await query.answer()
    exp_id = int(query.data.split(":",1)[1])

    # 2) fetch data
    entries = await rq.get_daily_entries_for_experiment(query.from_user.id, exp_id)
    if not entries:
        await state.clear()
        return await query.message.edit_text("⚠️ No daily entries for that experiment.")

    n = len(entries)

    if n < 10:
        await state.clear()
        return await query.message.edit_text(
            f"⚠️ Not enough data ({n} days). Need at least 10 entries to compute correlations."
        )

    # build DataFrame: each row is entry.data (a dict of {param_name: value})
    df = pd.DataFrame([e.data for e in entries])

    # you might need to convert strings to numeric here, e.g.
    # for col in df.columns:
    #     df[col] = pd.to_numeric(df[col], errors="ignore")

    params = await rq.get_list_parameters(exp_id)

    for p in params:
        if p.type == ParamType.BOOLEAN:
            df[p.name] = df[p.name].map({"+": 1, "-": 0})

    # extract the names of all goal‐type parameters
    goal_vars = [p.name for p in params if p.is_goal]
    if not goal_vars:
        await state.clear()
        return await query.message.edit_text(
            "⚠️ This experiment has no goal parameters defined."
        )

    if 10 <= n < 20:
        km = Сorrelation.kendall(df, goal_vars)
        Сorrelation.correlation_matrix_chart(km)  # saves to out
        caption = f"📈 Kendall correlation ({n} days)"
    elif 20 <= n < 35:
        km = Сorrelation.kendall(df, goal_vars)
        pm = Сorrelation.pearson(df, goal_vars)
        Сorrelation.two_correlation_matrices_chart(km, pm)
        caption = f"📊 Kendall & Pearson ({n} days)"
    else:  # n >= 35
        pm = Сorrelation.pearson(df, goal_vars)
        Сorrelation.correlation_matrix_chart(pm)
        caption = f"📉 Pearson correlation ({n} days)"

    img = FSInputFile(path="data/correlation_heatmaps.png")

    # 5) send the image back
    await query.message.answer_photo(photo=img, caption= caption)

    await state.clear()
