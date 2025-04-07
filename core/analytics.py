import pandas as pd
import matplotlib as plt
import seaborn as sbn
import statsmodels.api as sm
from statsmodels.miscmodels.ordinal_model import OrderedModel


class correlation:
    @staticmethod
    def kendall(data: pd.DataFrame, goal_variables: list[str]) -> pd.DataFrame:
        kendall_corr = data.corr(method='kendall')[goal_variables].drop(
            goal_variables)  # Deleting selfcorrelations and correlations with goal variables
        print("-----Kendal correlation matrix-------")
        print(kendall_corr, '\n')

        return kendall_corr

    @staticmethod
    def pearson(data: pd.DataFrame, goal_variables: list[str]) -> pd.DataFrame:
        pearson_corr = data.corr(method='pearson')[goal_variables].drop(
            goal_variables)  # Deleting selfcorrelations and correlations with goal variables
        print("-----Pearson correlation matrix-------")
        print(pearson_corr, '\n')

        return pearson_corr

class regresion:
    @staticmethod
    def multiple_linear(X_variables: pd.DataFrame, Y_variable):
        X_variables_ols = sm.add_constant(X_variables)
        return sm.OLS(Y_variable, X_variables_ols).fit()

    @staticmethod
    def ordinal_logistic(X_variables: pd.DataFrame, Y_variable):
        return OrderedModel(Y_variable, X_variables, distr='logit').fit(method='bfgs')


import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt


class MultipleLinearRegression:
    def __init__(self, X: pd.DataFrame, y: pd.Series):
        """
        Створення моделі множинної лінійної регресії.
        """
        if not isinstance(X, pd.DataFrame):
            raise TypeError("X має бути DataFrame")
        if not isinstance(y, (pd.Series, pd.DataFrame)):
            raise TypeError("y має бути Series або DataFrame з одним стовпцем")

        self.X = sm.add_constant(X)
        self.y = y.squeeze()
        self.model = sm.OLS(self.y, self.X).fit()

    def summary(self):
        """
        Текстовий звіт результатів моделі.
        """
        return self.model.summary()

    def predict(self, new_X: pd.DataFrame) -> pd.Series:
        """
        Прогноз на нових даних.
        """
        new_X = sm.add_constant(new_X)
        return self.model.predict(new_X)

    def coefficients(self) -> pd.DataFrame:
        """
        Коефіцієнти + p-values + інтерпретація.
        """
        df = pd.DataFrame({
            "Coef.": self.model.params,
            "P-value": self.model.pvalues
        })

        def interpret_row(row):
            coef = abs(row["Coef."])
            pval = row["P-value"]

            # сила впливу
            if coef > 1.0:
                strength = "🔴 Дуже сильний"
            elif coef > 0.5:
                strength = "🟠 Сильний"
            elif coef > 0.2:
                strength = "🟡 Помірний"
            elif coef > 0.05:
                strength = "🔵 Слабкий"
            else:
                strength = "⚪ Майже відсутній"

            # значущість
            if pval < 0.01:
                significance = "🔥 Надійний (p < 0.01)"
            elif pval < 0.05:
                significance = "✅ Значущий (p < 0.05)"
            elif pval < 0.1:
                significance = "⚠️ На межі (p < 0.1)"
            else:
                significance = "❌ Ненадійний (p > 0.1)"

            return pd.Series([strength, significance])

        df[["Сила впливу", "Значущість"]] = df.apply(interpret_row, axis=1)
        return df.round(4)

    def plot_residuals(self):
        """
        Графік залишків.
        """
        residuals = self.model.resid
        fitted = self.model.fittedvalues
        plt.figure(figsize=(6, 4))
        plt.scatter(fitted, residuals, alpha=0.7)
        plt.axhline(0, color="red", linestyle="--")
        plt.xlabel("Прогнозовані значення")
        plt.ylabel("Залишки")
        plt.title("Графік залишків")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def r_squared(self) -> float:
        """
        R² (коефіцієнт детермінації).
        """
        return round(self.model.rsquared, 4)






