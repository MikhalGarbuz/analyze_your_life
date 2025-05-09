from statsmodels.miscmodels.ordinal_model import OrderedModel
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from core.base_classes import Regresion


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
        num_exog = self.result.model.exog.shape[1]  # Отримуємо кількість пояснюючих змінних
        df = pd.DataFrame({
            "Threshold": self.result.params[num_exog:],
            "P-value": self.result.pvalues[num_exog:]
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
        x_range = pd.Series(np.linspace(self.X[feature_name].min(), self.X[feature_name].max(), num=40))
        probs = []

        for val in x_range:
            obs = fixed_values.copy()
            obs[feature_name] = val
            # Обгортаємо в DataFrame з одним рядком
            pred = self.result.predict(pd.DataFrame([obs]))
            # Вибираємо перший рядок (якщо predict повертає DataFrame з індексом)
            probs.append(pred.iloc[0])

        # Якщо class_labels не передано, використовуємо унікальні значення цільової змінної
        if class_labels is None:
            class_labels = sorted(self.result.model.endog.unique())


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

