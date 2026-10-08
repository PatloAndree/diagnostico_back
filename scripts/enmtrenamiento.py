import os
import numpy as np
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    balanced_accuracy_score, confusion_matrix, ConfusionMatrixDisplay,
    roc_curve, roc_auc_score, precision_recall_curve,
    average_precision_score
)
from sklearn.model_selection import (
    train_test_split, StratifiedKFold, cross_validate
)

# -------------------------------------------------
# CONFIGURACIÓN
# -------------------------------------------------
SEMILLA = 42
MUESTRAS = 10_000
RUIDO_ETIQUETA = 0.12
CARPETA_SALIDA = "resultados_adhd"

ITEMS = [
    "1. Atención a detalles",
    "2. Mueve manos/pies",
    "3. Mantiene atención",
    "4. Permanece sentado",
    "5. Parece no escuchar",
    "6. Corre o trepa",
    "7. Sigue instrucciones",
    "8. Juega calladamente",
    "9. Organiza tareas",
    "10. Activado por motor",
    "11. Evita esfuerzo mental",
    "12. Habla excesivamente",
    "13. Pierde cosas",
    "14. Responde impulsivamente",
    "15. Se distrae",
    "16. Espera su turno",
    "17. Es olvidadizo",
    "18. Interrumpe",
]

INATENCION = [1, 3, 5, 7, 9, 11, 13, 15, 17]
HIPERACTIVIDAD = [2, 4, 6, 8, 10, 12, 14, 16, 18]


def generar_datos():
    rng = np.random.default_rng(SEMILLA)

    # Respuestas aleatorias: 0 Nunca, 1 Rara vez, 2 Algunas veces, 3 A menudo.
    x = rng.integers(0, 4, size=(MUESTRAS, 18))

    # Etiqueta sintética de tamizaje.
    sintomas_inatencion = (x[:, np.array(INATENCION) - 1] >= 2).sum(axis=1)
    sintomas_hiperactividad = (x[:, np.array(HIPERACTIVIDAD) - 1] >= 2).sum(axis=1)

    y = (
        (sintomas_inatencion >= 6)
        | (sintomas_hiperactividad >= 6)
    ).astype(int)

    # Ruido para que la evaluación no sea artificialmente perfecta.
    ruido = rng.random(MUESTRAS) < RUIDO_ETIQUETA
    y[ruido] = 1 - y[ruido]

    return x, y


def guardar(nombre):
    plt.tight_layout()
    plt.savefig(
        os.path.join(CARPETA_SALIDA, nombre),
        dpi=180,
        bbox_inches="tight"
    )


def main():
    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    x, y = generar_datos()

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.20,
        random_state=SEMILLA,
        stratify=y
    )

    modelo = RandomForestClassifier(
        n_estimators=500,
        max_features="sqrt",
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=SEMILLA,
        n_jobs=-1
    )

    modelo.fit(x_train, y_train)

    y_pred = modelo.predict(x_test)
    y_prob = modelo.predict_proba(x_test)[:, 1]

    # 1. Métricas principales
    metricas = {
        "Accuracy": accuracy_score(y_test, y_pred),
        "Balanced accuracy": balanced_accuracy_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred),
        "Recall": recall_score(y_test, y_pred),
        "F1-score": f1_score(y_test, y_pred),
        "ROC-AUC": roc_auc_score(y_test, y_prob),
        "PR-AUC": average_precision_score(y_test, y_prob),
    }

    plt.figure(figsize=(10, 5))
    barras = plt.bar(metricas.keys(), metricas.values(), color="#2563eb")
    plt.ylim(0, 1)
    plt.title("Métricas del Random Forest")
    plt.ylabel("Valor")
    plt.xticks(rotation=25, ha="right")

    for barra, valor in zip(barras, metricas.values()):
        plt.text(
            barra.get_x() + barra.get_width() / 2,
            valor + 0.02,
            f"{valor:.3f}",
            ha="center"
        )

    guardar("01_metricas.png")

    # 2. Matriz de confusión
    matriz = confusion_matrix(y_test, y_pred)

    fig, ax = plt.subplots(figsize=(6, 5))
    ConfusionMatrixDisplay(
        confusion_matrix=matriz,
        display_labels=["Negativo", "Positivo"]
    ).plot(ax=ax, cmap="Blues", colorbar=False)

    plt.title("Matriz de confusión")
    guardar("02_matriz_confusion.png")

    # 3. Curva ROC
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    auc = roc_auc_score(y_test, y_prob)

    plt.figure(figsize=(7, 6))
    plt.plot(fpr, tpr, label=f"Random Forest (AUC = {auc:.3f})", color="#2563eb")
    plt.plot([0, 1], [0, 1], "--", color="gray", label="Clasificador aleatorio")
    plt.xlabel("Tasa de falsos positivos")
    plt.ylabel("Tasa de verdaderos positivos")
    plt.title("Curva ROC")
    plt.legend()
    plt.grid(alpha=0.3)
    guardar("03_curva_roc.png")

    # 4. Curva Precision-Recall
    precision, recall, _ = precision_recall_curve(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)

    plt.figure(figsize=(7, 6))
    plt.plot(
        recall,
        precision,
        color="#16a34a",
        label=f"Random Forest (AP = {pr_auc:.3f})"
    )
    plt.xlabel("Recall / sensibilidad")
    plt.ylabel("Precisión")
    plt.title("Curva Precision-Recall")
    plt.legend()
    plt.grid(alpha=0.3)
    guardar("04_curva_precision_recall.png")

    # 5. Curva de calibración
    prob_real, prob_predicha = calibration_curve(
        y_test,
        y_prob,
        n_bins=10,
        strategy="uniform"
    )

    plt.figure(figsize=(7, 6))
    plt.plot(prob_predicha, prob_real, "o-", color="#9333ea", label="Modelo")
    plt.plot([0, 1], [0, 1], "--", color="gray", label="Calibración perfecta")
    plt.xlabel("Probabilidad predicha")
    plt.ylabel("Proporción real de positivos")
    plt.title("Curva de calibración")
    plt.legend()
    plt.grid(alpha=0.3)
    guardar("05_calibracion.png")

    # 6. Importancia de los ítems
    importancias = modelo.feature_importances_
    orden = np.argsort(importancias)

    plt.figure(figsize=(11, 8))
    plt.barh(
        [ITEMS[i] for i in orden],
        importancias[orden],
        color="#f59e0b"
    )
    plt.xlabel("Importancia Gini")
    plt.title("Importancia de cada ítem ADHD Rating Scale-IV")
    guardar("06_importancia_items.png")

    # 7. Validación cruzada
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMILLA)

    resultados_cv = cross_validate(
        modelo,
        x_train,
        y_train,
        cv=cv,
        n_jobs=-1,
        scoring={
            "Accuracy": "accuracy",
            "Precision": "precision",
            "Recall": "recall",
            "F1": "f1",
            "ROC-AUC": "roc_auc",
        }
    )

    nombres = ["Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]
    valores = [resultados_cv[f"test_{nombre}"] for nombre in nombres]

    plt.figure(figsize=(10, 6))
    plt.boxplot(valores, tick_labels=nombres)
    plt.ylim(0, 1)
    plt.ylabel("Resultado por fold")
    plt.title("Validación cruzada estratificada: 5 folds")
    plt.grid(axis="y", alpha=0.3)
    guardar("07_validacion_cruzada.png")

    print("\nMÉTRICAS:")
    for nombre, valor in metricas.items():
        print(f"{nombre}: {valor:.4f}")

    print("\nMatriz de confusión:")
    print(matriz)

    print(f"\nGráficos guardados en: {CARPETA_SALIDA}")
    plt.show()


if __name__ == "__main__":
    main()