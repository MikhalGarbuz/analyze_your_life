import pandas as pd
import matplotlib.pyplot  as plt
import seaborn as sns
import statsmodels.api as sm
import numpy as  np
from base_classes import Regresion

class MultipleLinearRegression(Regresion):
    def __init__(self, X: pd.DataFrame, y: pd.Series, add_polynomial_terms: bool = False):
        """
        Створює та тренує модель множинної лінійної регресії.
        Якщо add_polynomial_terms = True — додає квадратичні ознаки.
        """
        if not isinstance(X, pd.DataFrame):
            raise TypeError("X має бути DataFrame")
        if not isinstance(y, (pd.Series, pd.DataFrame)):
            raise TypeError("y має бути Series або DataFrame з одним стовпцем")

        self.y = y.squeeze()
        self.feature_names = list(X.columns)

        # Додамо квадратичні ознаки, якщо вказано
        if add_polynomial_terms:
            for col in self.feature_names:
                X[f"{col}_squared"] = X[col] ** 2

        self.X = sm.add_constant(X)
        self.model = sm.OLS(self.y, self.X).fit()
        self.used_poly = add_polynomial_terms

    def summary(self):
        return self.model.summary()

    def predict(self, new_X: pd.DataFrame) -> pd.Series:
        if self.used_poly:
            for col in self.feature_names:
                new_X[f"{col}_squared"] = new_X[col] ** 2
        new_X = sm.add_constant(new_X)
        return self.model.predict(new_X)

    def coefficients(self) -> pd.DataFrame:
        df = pd.DataFrame({
            "Coef.": self.model.params,
            "P-value": self.model.pvalues
        })

        def interpret_row(row):
            coef = abs(row["Coef."])
            pval = row["P-value"]

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

            if pval < 0.01:
                significance = "🔥 Надійний"
            elif pval < 0.05:
                significance = "✅ Значущий"
            elif pval < 0.1:
                significance = "⚠️ На межі"
            else:
                significance = "❌ Ненадійний"

            return pd.Series([strength, significance])

        df[["Сила впливу", "Значущість"]] = df.apply(interpret_row, axis=1)
        return df.round(4)

    def r_squared(self) -> float:
        return round(self.model.rsquared, 4)

    def plot_residuals(self):
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

    def plot_feature_relationship(self, feature_names):
        # Якщо передано окремий рядок, перетворимо його в список
        if isinstance(feature_names, str):
            feature_names = [feature_names]

        # Перевіримо, чи всі ознаки знаходяться в даних
        for feature in feature_names:
            if feature not in self.X.columns:
                raise ValueError(f"Ознака '{feature}' не знайдена в X")

            # Виключаємо константу з даних для графіку
            X_plot = self.X.drop(columns="const", errors="ignore")

            plt.figure(figsize=(6, 4))
            sns.regplot(x=X_plot[feature], y=self.y, line_kws={"color": "red"})
            plt.title(f"Зв'язок: {feature} → {self.y.name or 'Цільова змінна'}")
            plt.xlabel(feature)
            plt.ylabel(self.y.name or "Цільова змінна")
            plt.grid(True)
            plt.tight_layout()
            plt.show()
