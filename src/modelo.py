"""Modelo exploratório de gravidade, avaliado na base comparável."""

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.model_selection import train_test_split

from src.metricas import base_comparavel

FEATURES_CAT = ["tipo_sinistro", "tipo_via", "dia_semana", "turno"]
FEATURES_NUM = ["hora_int", "mes", "qtd_motocicleta", "qtd_automovel", "qtd_caminhao", "qtd_pedestre", "qtd_bicicleta"]


def treinar_modelo(df: pd.DataFrame):
    """Treina e avalia o Random Forest, com conjunto de teste separado."""
    df_ml = base_comparavel(df)[FEATURES_CAT + FEATURES_NUM + ["gravidade"]].dropna().copy()
    # Classes com poucos casos impedem a divisão estratificada
    df_ml = df_ml[df_ml["gravidade"].map(df_ml["gravidade"].value_counts()) >= 10]
    if df_ml.empty:
        return None

    X = pd.get_dummies(df_ml[FEATURES_CAT + FEATURES_NUM], columns=FEATURES_CAT, drop_first=True)
    y = df_ml["gravidade"]
    X_treino, X_teste, y_treino, y_teste = train_test_split(X, y, test_size=0.30, random_state=42, stratify=y)

    # Sem class_weight, para que predict_proba reflita a frequência das classes
    clf = RandomForestClassifier(n_estimators=150, max_depth=10, min_samples_leaf=5, random_state=42)
    clf.fit(X_treino, y_treino)
    pred = clf.predict(X_teste)

    permutacao = permutation_importance(clf, X_teste, y_teste, n_repeats=10, random_state=42, scoring="neg_log_loss")
    importancias = pd.Series(permutacao.importances_mean, index=X.columns).sort_values(ascending=True)
    return {
        "modelo": clf,
        "importancias": importancias,
        "features": X.columns.tolist(),
        "n_teste": len(y_teste),
        "acuracia": accuracy_score(y_teste, pred),
        "acuracia_balanceada": balanced_accuracy_score(y_teste, pred),
        "referencia": y_teste.value_counts(normalize=True).max(),
    }
