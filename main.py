import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import seaborn as sbn
import statsmodels.api as sm
from statsmodels.miscmodels.ordinal_model import OrderedModel


GOAL_VARIABLES = ["productivity", "mood", "work_hours"]

DAY7_FILENAME = "data/lifestyle_data_7_days.csv"
DAY14_FILENAME = "data/lifestyle_data_14_days.csv"
DAY30_FILENAME = "data/lifestyle_data_30_days.csv"
DAY45_FILENAME = "data/lifestyle_data_45_days.csv"

def load_lifestyle_data(file_path):
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Файл {file_path} не знайдено.")
        return None

# Loading data
df7 = load_lifestyle_data(DAY7_FILENAME)
df14 = load_lifestyle_data(DAY14_FILENAME)
df30 = load_lifestyle_data(DAY30_FILENAME)
df45 = load_lifestyle_data(DAY45_FILENAME)

# General statistics for 7 days
print("--------Statistics for 7 days--------")
print(df7.describe())


# Creating Kendall and Pearson correlation matrices
# Extracting correlation data for productivity, mood and work_hours
kendall_corr = df7.corr(method='kendall')[GOAL_VARIABLES].drop(GOAL_VARIABLES) # Deleting selfcorrelations and correlations
pearson_cor = df7.corr(method='pearson')[GOAL_VARIABLES].drop(GOAL_VARIABLES)  # and correlations with goal variables

print("-----Kendal correlation matrix-------")
print(kendall_corr, '\n')

print("-----Pearson correlation matrix-------")
print(pearson_cor, '\n')



plt.figure(figsize=(12, 5))
plt.subplot(1,2,1)
sbn.heatmap(kendall_corr, annot=True, cmap="coolwarm", cbar=False)
plt.title('Kendall Correlation matrix')

plt.subplot(1,2,2)
sbn.heatmap(pearson_cor, annot=True, cmap="coolwarm")
plt.title('Pearson Correlation matrix')
plt.tight_layout()
plt.show()
plt.savefig("data/correlation_heatmaps.png")
plt.close()