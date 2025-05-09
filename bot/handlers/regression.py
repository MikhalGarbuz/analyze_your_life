from io import BytesIO
import matplotlib.pyplot as plt
import pandas as pd

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile

from bot.states import Analyze
import bot.keyboards as kb
import core.database.requests as rq
from core.logistic_regression import OrdinalLogisticRegression
from core.linear_regression import MultipleLinearRegression
from core.database.models import ParamType

from . import router
@router.message(Command("analyze"))
async def cmd_analyze(message: Message, state: FSMContext):
    exps = await rq.get_list_experiments(message.from_user.id)
    if not exps:
        return await message.answer("❗ No experiments found. Use /new to create one.")
    await state.set_state(Analyze.SELECT_EXP)
    await message.answer("📈 Select an experiment to analyze:", reply_markup=await kb.user_experiments_list(exps))


@router.callback_query(Analyze.SELECT_EXP, F.data.startswith("sel_exp:"))
async def choose_experiment(query: CallbackQuery, state: FSMContext):
    await query.answer()
    exp_id = int(query.data.split(':',1)[1])
    await state.update_data(exp_id=exp_id)

    # list only goal parameters
    params = await rq.get_list_parameters(exp_id)
    goals = [p for p in params if p.is_goal]
    if not goals:
        await state.clear()
        return await query.message.edit_text("⚠️ No goal parameters defined for this experiment.")

    await state.set_state(Analyze.SELECT_TARGET)
    await query.message.edit_text("🎯 Select a target variable:", reply_markup=await kb.parameter_list(goals))


@router.callback_query(Analyze.SELECT_TARGET, F.data.startswith("sel_param:"))
async def run_analysis(query: CallbackQuery, state: FSMContext):
    await query.answer()
    data = await state.get_data()
    exp_id = data['exp_id']
    target_id = int(query.data.split(':',1)[1])

    params = await rq.get_list_parameters(exp_id)

    # Find the one with matching id
    p = next(p for p in params if p.id == target_id)
    col = p.name   # the actual DataFrame column

    # fetch entries
    entries = await rq.get_daily_entries_for_experiment(query.from_user.id, exp_id)
    df = pd.DataFrame([e.data for e in entries])

    for p in params:
        if p.type == ParamType.BOOLEAN:
            df[p.name] = df[p.name].map({"+": 1, "-": 0})

    X = df.drop(columns=[col])
    y = df[col]



    # choose model by type
    p = next(p for p in params if p.name == col)
    if p.type == ParamType.NUMERIC:
        model = MultipleLinearRegression(X, y, add_polynomial_terms=False)
        # Summary text
        summary = model.summary().as_text()
        await query.message.answer(f"<pre>{summary}</pre>", parse_mode="HTML")
        # Coefficients table
        coef_df = model.coefficients()
        await query.message.answer(f"<pre>{coef_df.to_markdown()}</pre>", parse_mode="HTML")
        # R-squared
        await query.message.answer(f"R² = {model.r_squared()}")
        # Residuals plot
        resid = model.model.resid
        fit   = model.model.fittedvalues
        buf = BytesIO()
        plt.figure(figsize=(6,4))
        plt.scatter(fit, resid, alpha=0.7)
        plt.axhline(0, color='red', linestyle='--')
        plt.xlabel('Fitted')
        plt.ylabel('Residuals')
        plt.tight_layout()
        plt.savefig(buf, format='PNG')
        plt.close()
        buf.seek(0)
        await query.message.answer_photo(BufferedInputFile(buf, filename='residuals.png'))
    else:
        model = OrdinalLogisticRegression(X, y)
        summary = model.summary().as_text()
        await query.message.answer(f"<pre>{summary}</pre>", parse_mode="HTML")
        coef_df = model.coefficients()
        await query.message.answer(f"<pre>{coef_df.to_markdown()}</pre>", parse_mode="HTML")
        thresh_df = model.thresholds()
        await query.message.answer(f"<pre>{thresh_df.to_markdown()}</pre>", parse_mode="HTML")
        await query.message.answer(f"McFadden pseudo-R² = {model.pseudo_r2()}")
        # class probs plot for first param
        fixed = {col: X[col].mean() for col in X.columns}
        buf = BytesIO()
        # generate probabilities image
        # reuse internal plotting but redirect to buf
        model.plot_class_probabilities(query.message, fixed_values=fixed, class_labels=sorted(y.unique()))
    await state.clear()
