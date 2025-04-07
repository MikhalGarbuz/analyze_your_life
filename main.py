import pandas as pd
import numpy as np  # додай на початку, якщо ще не імпортував
import matplotlib
matplotlib.use('TkAgg')
from core.analytics import correlation as corr, regresion as regr
from  core.database import load_lifestyle_data
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.miscmodels.ordinal_model import OrderedModel


goal_variables = ["productivity", "mood", "work_hours"]
INDEPENDENT_VARIABLES = ["sleep_hours", "sleep_quality", "water_liters", "sport_hours", "food_quality", "vitamins"]


DAY7_FILENAME = "data/lifestyle_data_7_days.csv"
DAY14_FILENAME = "data/lifestyle_data_14_days.csv"
DAY30_FILENAME = "data/lifestyle_data_30_days.csv"
DAY45_FILENAME = "data/lifestyle_data_45_days.csv"

# Loading data
df7 = load_lifestyle_data(DAY7_FILENAME)
#df_14 = load_lifestyle_data(DAY14_FILENAME)
df30 = load_lifestyle_data(DAY30_FILENAME)
df_45 = load_lifestyle_data(DAY45_FILENAME)

# General statistics for 7 days
#print("--------Statistics for 7 days--------")
#print(df7.describe())

print(corr.kendall(df_45, goal_variables))

features = ["sleep_hours", "sleep_quality", "water_liters", "sport_hours", "food_quality", "vitamins"]
X_14 = df_45[features]

# --- Лінійна регресія для work_hours ---
X_ols_14 = sm.add_constant(X_14)
y_work_14 = df_45["work_hours"]
ols_model_14 = sm.OLS(y_work_14, X_ols_14).fit()

# --- Порядкова логістична регресія для productivity ---
ord_model_14 = OrderedModel(df_45["productivity"], X_14, distr='logit').fit(method='bfgs')

# --- Прогноз ---
# Створення 2 випадків: sleep_hours = 6.0 та sleep_hours = 8.0
test_data_low_sleep = pd.DataFrame([{
    "sleep_hours": 6.0,
    "sleep_quality": 3,
    "water_liters": 2.0,
    "sport_hours": 1,
    "food_quality": 4,
    "vitamins": 1
}])
test_data_high_sleep = test_data_low_sleep.copy()
test_data_high_sleep["sleep_hours"] = 8.0

# Додаємо константу для OLS
test_data_low_sleep["const"] = 1.0
test_data_high_sleep["const"] = 1.0
test_data_low_sleep = test_data_low_sleep[["const"] + features]
test_data_high_sleep = test_data_high_sleep[["const"] + features]

# Прогнози по OLS-моделі work_hours
pred_hours_low = ols_model_14.predict(test_data_low_sleep)[0]
pred_hours_high = ols_model_14.predict(test_data_high_sleep)[0]

# Прогнози по логістичній моделі productivity
pred_prod_low = ord_model_14.predict(test_data_low_sleep[features]).idxmax(axis=1).values[0]
pred_prod_high = ord_model_14.predict(test_data_high_sleep[features]).idxmax(axis=1).values[0]

# Вивід результатів
results = {
    "ols_summary_14_days": ols_model_14.summary2().tables[1],
    "ord_summary_14_days": pd.DataFrame({"Coef.": ord_model_14.params, "P>|z|": ord_model_14.pvalues}),
    "predicted_hours_sleep_6": round(pred_hours_low, 2),
    "predicted_hours_sleep_8": round(pred_hours_high, 2),
    "predicted_productivity_sleep_6": int(pred_prod_low),
    "predicted_productivity_sleep_8": int(pred_prod_high)
}

# Зручне форматоване виведення результатів
print("\n--- РЕЗУЛЬТАТИ ЛІНІЙНОЇ РЕГРЕСІЇ (work_hours) ---\n")
print(results["ols_summary_14_days"][["Coef.", "P>|t|"]])

print("\n--- РЕЗУЛЬТАТИ ПОРЯДКОВОЇ ЛОГІСТИЧНОЇ РЕГРЕСІЇ (productivity) ---\n")
print(results["ord_summary_14_days"][["Coef.", "P>|z|"]])

print("\n--- ПРОГНОЗИ ---")
print(f"\nПри 6 год сну: work_hours ≈ {results['predicted_hours_sleep_6']} год, продуктивність ≈ {results['predicted_productivity_sleep_6']}")
print(f"При 8 год сну: work_hours ≈ {results['predicted_hours_sleep_8']} год, продуктивність ≈ {results['predicted_productivity_sleep_8']}")

# --- Побудова графіків для лінійної регресії ---
plt.figure(figsize=(6, 4))
sns.regplot(x=df_45["sleep_hours"], y=df_45["work_hours"], line_kws={"color": "red"})
plt.title("Лінійна регресія: сон → робочі години")
plt.xlabel("Кількість годин сну")
plt.ylabel("Робочі години")
plt.tight_layout()
plt.savefig("data/linear_regression_plot.png")
plt.close()

# --- Побудова логістичної ймовірності для найвищого рівня productivity ---
sleep_range = pd.Series([5.0 + 0.1 * i for i in range(30)])
probs_by_class = {}

for val in sleep_range:
    tmp = pd.DataFrame([{
        "sleep_hours": val,
        "sleep_quality": 3,
        "water_liters": 2.0,
        "sport_hours": 1,
        "food_quality": 4,
        "vitamins": 1
    }])

    probs = ord_model_14.predict(tmp)
    probs.columns = probs.columns.astype(str)  # Усі назви колонок — строки

    for col in probs.columns:
        if col not in probs_by_class:
            probs_by_class[col] = []
        probs_by_class[col].append(probs.loc[0, col])

# Побудова графіка
plt.figure(figsize=(7, 5))
for cls, values in probs_by_class.items():
    plt.plot(sleep_range, values, label=f"Клас {cls}")

plt.title("Логістична регресія: сон → ймовірності рівнів продуктивності")
plt.xlabel("Кількість годин сну")
plt.ylabel("Ймовірність")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("data/logistic_all_levels_plot.png")
plt.close()
