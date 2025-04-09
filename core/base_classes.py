from abc import ABC, abstractmethod
import pandas as pd

class Regresion(ABC):
    @abstractmethod
    def predict(self, new_X: pd.DataFrame) -> pd.Series:
        pass

    @abstractmethod
    def coefficients(self) -> pd.DataFrame:
        pass

    @staticmethod
    def ordinal_logistic(X_variables: pd.DataFrame, Y_variable):
        pass