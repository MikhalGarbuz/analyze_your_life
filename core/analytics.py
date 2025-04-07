from abc import ABC, abstractmethod
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

class Regresion(ABC):
    @abstractmethod
    def predict(self, new_X: pd.DataFrame) -> pd.Series:
        pass

    @abstractmethod
    def coefficients(self) -> pd.DataFrame:
        pass


    @staticmethod
    def ordinal_logistic(X_variables: pd.DataFrame, Y_variable):
        return OrderedModel(Y_variable, X_variables, distr='logit').fit(method='bfgs')


class MultipleLinearRegression(Regresion):
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

    def plot_feature_relationship(self, feature_name: str):
        """
        Графік: значення ознаки → цільова змінна (розсіювання + лінія регресії).
        """
        if feature_name not in self.X.columns:
            raise ValueError(f"Ознака '{feature_name}' не знайдена в X")

        # Видаляємо константу, якщо є
        X_plot = self.X.drop(columns="const", errors="ignore")

        plt.figure(figsize=(6, 4))
        sbn.regplot(x=X_plot[feature_name], y=self.y, line_kws={"color": "red"})
        plt.title(f"Зв'язок: {feature_name} → {self.y.name or 'Цільова змінна'}")
        plt.xlabel(feature_name)
        plt.ylabel(self.y.name or "Цільова змінна")
        plt.grid(True)
        plt.tight_layout()
        plt.show()


class OrdinalLogisticRegression(Regresion):
    def __init__(self, X: pd.DataFrame, y: pd.Series):
        """
        Створення моделі порядкової логістичної регресії.
        """
        self.X = X
        self.y = y
        self.model = OrderedModel(self.y, self.X, distr='logit')
        self.result = self.model.fit(method='bfgs', disp=False)  # suppress output

    def summary(self):
        """Повертає текстове зведення результатів."""
        return self.result.summary()

    def predict(self, new_X: pd.DataFrame) -> pd.DataFrame:
        """Повертає ймовірності належності до кожного класу."""
        return self.result.predict(new_X)

    def coefficients(self) -> pd.DataFrame:
        """Коефіцієнти + P-values + інтерпретація впливу."""
        df = pd.DataFrame({
            "Coef.": self.result.params,
            "P-value": self.result.pvalues
        })

        def interpret(row):
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

        df[["Сила впливу", "Значущість"]] = df.apply(interpret, axis=1)
        return df.round(4)

    def thresholds(self) -> pd.DataFrame:
        """Окремо повертає порогові значення між класами."""
        df = pd.DataFrame({
            "Threshold": self.result.params[self.result.model.k_exog:],
            "P-value": self.result.pvalues[self.result.model.k_exog:]
        })

        df = df.reset_index().rename(columns={"index": "Клас переходу"})
        return df.round(4)

    def pseudo_r2(self) -> float:
        """Аналог R² — McFadden Pseudo R-squared."""
        return round(self.result.prsquared, 4)

    def plot_class_probabilities(self, feature_name: str, fixed_values: dict, class_labels: list = None):
        """
        Графік: зміна ймовірності класу залежно від однієї ознаки.
        feature_name: змінна, яку будемо змінювати (x-вісь)
        fixed_values: інші змінні — значення по замовчуванню
        class_labels: необов’язково — перелік значень цільової змінної
        """
        x_range = pd.Series([i * 0.1 for i in range(40)])  # від 0 до 4
        probs = []

        for val in x_range:
            obs = fixed_values.copy()
            obs[feature_name] = val
            probs.append(self.result.predict(pd.DataFrame([obs])).iloc[0])

        probs_df = pd.DataFrame(probs, columns=class_labels if class_labels else self.result.model.endog.unique())
        plt.figure(figsize=(8, 5))
        for label in probs_df.columns:
            plt.plot(x_range, probs_df[label], label=f"Клас {label}")
        plt.title(f"Ймовірність класу залежно від {feature_name}")
        plt.xlabel(feature_name)
        plt.ylabel("Ймовірність")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()



