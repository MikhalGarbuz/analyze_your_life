import pandas as pd
import matplotlib.pyplot  as plt
import seaborn as sns

class Сorrelation:
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

    @staticmethod
    def two_correlation_matrices_chart(kendal_matrix: pd.DataFrame, pearson_martix: pd.DataFrame) -> None:
        plt.figure(figsize=(12, 5))
        plt.subplot(1, 2, 1)
        sns.heatmap(kendal_matrix, annot=True, cmap="coolwarm", cbar=False)
        plt.title('Kendall Correlation matrix')

        plt.subplot(1, 2, 2)
        sns.heatmap(pearson_martix, annot=True, cmap="coolwarm")
        plt.title('Pearson Correlation matrix')
        plt.tight_layout()
        plt.show()
        plt.savefig("data/correlation_heatmaps.png")
        plt.close()

    @staticmethod
    def correlation_matrix_chart(correlation_matrix: pd.DataFrame) -> None:
        plt.figure(figsize=(7,5))
        sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", cbar=False)
        plt.title('Correlation matrix')
        plt.tight_layout()
        plt.show()
        plt.close()







