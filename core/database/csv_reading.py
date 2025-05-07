import asyncio
from pathlib import Path


import pandas as pd
from datetime import date, timedelta

from core.database.models import ParamType
from core.database.requests import (
    add_experiment,
    add_parameter,
    add_daily_entry,
)

async def import_daily_data_from_csv(
    user_id: int,
    experiment_name: str,
    csv_path: str,
    *,
    goal_columns: list[str],
    start_date: date | None = None
):
    """
    Bulk‐import CSV rows as one-shot daily entries.

    Columns in `goal_columns` are marked is_goal=True;
    all others are treated as independent.

    Rows are assigned to consecutive dates ending today
    (or from `start_date` if given).
    """
    # 1) Load CSV
    df = pd.read_csv(csv_path)

    # 2) Create experiment
    exp = await add_experiment(user_id=user_id, name=experiment_name)

    # 3) Auto‐create parameters for every column
    for col in df.columns:
        series = df[col]
        uniques = set(series.dropna().astype(str).unique())

        # infer type
        if uniques <= {"+", "-"}:
            ptype = ParamType.BOOLEAN
            class_min = class_max = None
        elif pd.api.types.is_numeric_dtype(series):
            ints = series.dropna().astype(int)
            if ints.nunique() <= 10:
                ptype = ParamType.CLASS
                class_min, class_max = int(ints.min()), int(ints.max())
            else:
                ptype = ParamType.NUMERIC
                class_min = class_max = None
        else:
            # fallback: try parse ints
            try:
                vals = [int(v) for v in uniques]
                ptype = ParamType.CLASS
                class_min, class_max = min(vals), max(vals)
            except:
                ptype = ParamType.NUMERIC
                class_min = class_max = None

        # use your provided goal_columns list
        is_goal = col in goal_columns

        await add_parameter(
            user_id   = user_id,
            exp_id    = exp.id,
            name      = col,
            is_goal   = is_goal,
            ptype     = ptype,
            class_min = class_min,
            class_max = class_max,
        )

    # 4) Determine start date so last row is today
    n = len(df)
    if start_date is None:
        start_date = date.today() - timedelta(days=n-1)

    # 5) Iterate rows → one daily entry per row
    for idx, row in df.iterrows():
        entry_date = start_date + timedelta(days=idx)
        payload    = row.to_dict()
        await add_daily_entry(
            user_id       = user_id,
            experiment_id = exp.id,
            entry_date    = entry_date,
            data          = payload
        )

    return exp


async def main():
    BASE = Path(__file__).parent.parent.parent  # or wherever your script lives

    exp = await import_daily_data_from_csv(
        user_id=1273362631,
        experiment_name="My 45-day study",
        csv_path= BASE  / "data" / "my_data.csv",
        goal_columns=["mood", "productivity", "work_hours"]
    )
    print("Created experiment:", exp)

if __name__ == "__main__":
    asyncio.run(main())