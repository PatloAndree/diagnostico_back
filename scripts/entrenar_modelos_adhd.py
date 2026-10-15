#!/usr/bin/env python3
"""Entrena los clasificadores alternativos para el tamizaje ADHD-RS-IV.

Se conserva el mismo contrato del modelo Random Forest existente: cada archivo
pickle contiene ``modelo`` y ``features``.  Por ello los tres modelos pueden
ser consumidos por ``diagnosticar_adhd.py`` sin cambiar sus predicciones.

Uso:
    python scripts/entrenar_modelos_adhd.py
    python scripts/entrenar_modelos_adhd.py --entrenar datos/respuestas_adhd.csv

Cuando las 30 filas de la plantilla aún no tienen respuestas, se entrenan
datos demostrativos deterministas, exactamente como en enmtrenamiento.py.
No deben utilizarse esos modelos demostrativos para decisiones clínicas.
"""

from __future__ import annotations

import argparse
import csv
import pickle
import sys
from pathlib import Path

import matplotlib

# Genera PNG sin abrir una ventana de Tk; funciona igual desde PowerShell,
# VS Code y servidores sin interfaz gráfica.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, average_precision_score, balanced_accuracy_score,
    confusion_matrix, f1_score, precision_recall_curve, precision_score,
    recall_score, roc_auc_score, roc_curve, make_scorer,
)
from sklearn.calibration import calibration_curve
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


SEMILLA = 42
TOTAL_REGISTROS = 30
RAIZ = Path(__file__).resolve().parent.parent
CSV_POR_DEFECTO = RAIZ / "datos" / "respuestas_adhd.csv"
CARPETA_MODELOS = RAIZ / "modelos"
CARPETA_RESULTADOS = RAIZ / "resultados_adhd"
FEATURES = [f"item_{numero}" for numero in range(1, 19)]


def generar_datos_demostracion() -> tuple[np.ndarray, np.ndarray]:
    """Genera el mismo conjunto sintético reproducible del entrenador base."""
    generador = np.random.default_rng(SEMILLA)
    respuestas = generador.integers(0, 4, size=(TOTAL_REGISTROS, len(FEATURES)))
    inatencion = (respuestas[:, [0, 2, 4, 6, 8, 10, 12, 14, 16]] >= 2).sum(axis=1)
    hiperactividad = (respuestas[:, [1, 3, 5, 7, 9, 11, 13, 15, 17]] >= 2).sum(axis=1)
    etiquetas = ((inatencion >= 6) | (hiperactividad >= 6)).astype(int)
    ruido = generador.random(TOTAL_REGISTROS) < 0.15
    etiquetas[ruido] = 1 - etiquetas[ruido]
    return respuestas, etiquetas


def cargar_csv(ruta: Path) -> tuple[np.ndarray, np.ndarray, bool]:
    if not ruta.is_file():
        raise ValueError(f"No se encontró el archivo: {ruta}")
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        faltantes = set([*FEATURES, "tamizaje_positivo"]) - set(lector.fieldnames or [])
        if faltantes:
            raise ValueError(f"Faltan columnas: {', '.join(sorted(faltantes))}.")
        filas = list(lector)
    if len(filas) != TOTAL_REGISTROS:
        raise ValueError(f"Se requieren exactamente {TOTAL_REGISTROS} registros; se recibieron {len(filas)}.")

    columnas = [*FEATURES, "tamizaje_positivo"]
    if all(not str(fila.get(columna, "")).strip() for fila in filas for columna in columnas):
        x, y = generar_datos_demostracion()
        return x, y, True

    respuestas, etiquetas = [], []
    for numero, fila in enumerate(filas, start=2):
        try:
            items = [int(fila[item]) for item in FEATURES]
            etiqueta = int(fila["tamizaje_positivo"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Fila {numero}: complete los 18 ítems y tamizaje_positivo.") from exc
        if any(valor not in (0, 1, 2, 3) for valor in items) or etiqueta not in (0, 1):
            raise ValueError(f"Fila {numero}: ítems entre 0 y 3 y tamizaje_positivo 0 o 1.")
        respuestas.append(items)
        etiquetas.append(etiqueta)

    x, y = np.asarray(respuestas), np.asarray(etiquetas)
    if np.bincount(y, minlength=2).min() < 2:
        raise ValueError("Debe haber al menos dos registros de cada clase (0 y 1).")
    return x, y, False


def crear_modelos() -> dict[str, Pipeline | RandomForestClassifier]:
    return {
        "random_forest": RandomForestClassifier(
            n_estimators=300, max_features="sqrt", min_samples_leaf=1,
            class_weight="balanced", random_state=SEMILLA, n_jobs=1,
        ),
        "svm": Pipeline([
            ("escalador", StandardScaler()),
            ("clasificador", CalibratedClassifierCV(
                SVC(kernel="rbf", C=1.0, gamma="scale", class_weight="balanced",
                    random_state=SEMILLA),
                cv=3,
            )),
        ]),
        # La regresión logística es el modelo lineal adecuado para una salida
        # binaria; LinearRegression no produce clases ni probabilidades válidas.
        "regresion_lineal": Pipeline([
            ("escalador", StandardScaler()),
            ("clasificador", LogisticRegression(C=1.0, class_weight="balanced",
                                                 max_iter=1000, random_state=SEMILLA)),
        ]),
    }


def evaluar(nombre: str, modelo, x: np.ndarray, y: np.ndarray) -> dict:
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.20, random_state=SEMILLA, stratify=y
    )
    modelo.fit(x_train, y_train)
    prediccion = modelo.predict(x_test)
    probabilidad = modelo.predict_proba(x_test)[:, 1]
    tn, fp, fn, tp = confusion_matrix(y_test, prediccion, labels=[0, 1]).ravel()
    especificidad = tn / (tn + fp) if tn + fp else 0.0
    metricas = {
        "Accuracy": accuracy_score(y_test, prediccion),
        "Balanced accuracy": balanced_accuracy_score(y_test, prediccion),
        "Precisión": precision_score(y_test, prediccion, zero_division=0),
        "Recall": recall_score(y_test, prediccion, zero_division=0),
        "Especificidad": especificidad,
        "F1": f1_score(y_test, prediccion, zero_division=0),
        "ROC-AUC": roc_auc_score(y_test, probabilidad),
        "PR-AUC": average_precision_score(y_test, probabilidad),
    }
    print(f"{nombre}: " + " | ".join(f"{clave}={valor:.3f}" for clave, valor in metricas.items()))
    return {
        "modelo": modelo, "x_train": x_train, "y_train": y_train,
        "y_test": y_test, "prediccion": prediccion, "probabilidad": probabilidad,
        "matriz": (tn, fp, fn, tp), "metricas": metricas,
    }


def guardar_graficos(nombre: str, evaluacion: dict) -> None:
    """Guarda las siete gráficas de evaluación listas para añadir a un informe."""
    carpeta = CARPETA_RESULTADOS / nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    y_test, pred, prob = evaluacion["y_test"], evaluacion["prediccion"], evaluacion["probabilidad"]
    tn, fp, fn, tp = evaluacion["matriz"]
    metricas = evaluacion["metricas"]

    fig, ax = plt.subplots(figsize=(10, 5))
    barras = ax.bar(metricas.keys(), metricas.values(), color="#2563eb")
    ax.set(ylim=(0, 1), title=f"1. Métricas — {nombre.replace('_', ' ').title()}")
    ax.tick_params(axis="x", rotation=25)
    for barra, valor in zip(barras, metricas.values()):
        ax.text(barra.get_x() + barra.get_width() / 2, valor + .02, f"{valor:.2f}", ha="center")
    fig.tight_layout(); fig.savefig(carpeta / "01_metricas.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 5))
    imagen = ax.imshow([[tn, fp], [fn, tp]], cmap="Blues")
    fig.colorbar(imagen, ax=ax); ax.set_xticks([0, 1], ["Negativo", "Positivo"])
    ax.set_yticks([0, 1], ["Negativo", "Positivo"]); ax.set(xlabel="Predicho", ylabel="Real", title="2. Matriz de confusión")
    for fila, valores in enumerate([[tn, fp], [fn, tp]]):
        for columna, valor in enumerate(valores): ax.text(columna, fila, str(valor), ha="center", va="center")
    fig.tight_layout(); fig.savefig(carpeta / "02_matriz_confusion.png", dpi=180); plt.close(fig)

    fpr, tpr, _ = roc_curve(y_test, prob)
    fig, ax = plt.subplots(figsize=(7, 6)); ax.plot(fpr, tpr, label=f"AUC = {metricas['ROC-AUC']:.3f}", color="#2563eb")
    ax.plot([0, 1], [0, 1], "--", color="gray", label="Aleatorio")
    ax.set(xlabel="Tasa de falsos positivos", ylabel="Tasa de verdaderos positivos", title="3. Curva ROC"); ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(carpeta / "03_curva_roc.png", dpi=180); plt.close(fig)

    precision, recall, _ = precision_recall_curve(y_test, prob)
    fig, ax = plt.subplots(figsize=(7, 6)); ax.plot(recall, precision, label=f"AP = {metricas['PR-AUC']:.3f}", color="#16a34a")
    ax.set(xlabel="Recall o sensibilidad", ylabel="Precisión", title="4. Curva Precision-Recall"); ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(carpeta / "04_curva_precision_recall.png", dpi=180); plt.close(fig)

    real, predicha = calibration_curve(y_test, prob, n_bins=min(5, len(y_test)), strategy="uniform")
    fig, ax = plt.subplots(figsize=(7, 6)); ax.plot(predicha, real, "o-", label="Modelo", color="#9333ea")
    ax.plot([0, 1], [0, 1], "--", color="gray", label="Calibración perfecta")
    ax.set(xlabel="Probabilidad predicha", ylabel="Proporción real de positivos", title="5. Curva de calibración"); ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(carpeta / "05_calibracion.png", dpi=180); plt.close(fig)

    clasificador = evaluacion["modelo"]
    if nombre == "random_forest":
        valores = clasificador.feature_importances_
        etiqueta, titulo = "Importancia Gini", "6. Importancia de los ítems"
    elif nombre == "regresion_lineal":
        valores = np.abs(clasificador.named_steps["clasificador"].coef_[0])
        etiqueta, titulo = "Valor absoluto del coeficiente", "6. Peso de los ítems"
    else:
        valores = np.zeros(len(FEATURES))
        etiqueta, titulo = "No aplica", "6. SVM no ofrece importancia lineal por ítem"
    orden = np.argsort(valores)
    fig, ax = plt.subplots(figsize=(10, 7)); ax.barh([f"Ítem {i + 1}" for i in orden], valores[orden], color="#f59e0b")
    ax.set(xlabel=etiqueta, title=titulo)
    fig.tight_layout(); fig.savefig(carpeta / "06_importancia_items.png", dpi=180); plt.close(fig)

    divisiones = min(5, int(np.bincount(evaluacion["y_train"], minlength=2).min()))
    cv = StratifiedKFold(n_splits=divisiones, shuffle=True, random_state=SEMILLA)
    resultados = cross_validate(clasificador, evaluacion["x_train"], evaluacion["y_train"], cv=cv, n_jobs=1,
                                scoring={"Accuracy": "accuracy", "Precision": make_scorer(precision_score, zero_division=0),
                                         "Recall": "recall", "F1": "f1"})
    nombres = ["Accuracy", "Precision", "Recall", "F1"]
    fig, ax = plt.subplots(figsize=(9, 6)); ax.boxplot([resultados[f"test_{item}"] for item in nombres], tick_labels=nombres)
    ax.set(ylim=(0, 1), ylabel="Resultado por fold", title=f"7. Validación cruzada estratificada ({divisiones} folds)"); ax.grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig(carpeta / "07_validacion_cruzada.png", dpi=180); plt.close(fig)


def guardar_comparacion(evaluaciones: dict[str, dict]) -> None:
    nombres = list(evaluaciones)
    metricas = ["Accuracy", "F1", "ROC-AUC", "PR-AUC"]
    posiciones = np.arange(len(metricas)); ancho = .24
    fig, ax = plt.subplots(figsize=(10, 6))
    for indice, nombre in enumerate(nombres):
        valores = [evaluaciones[nombre]["metricas"][metrica] for metrica in metricas]
        barras = ax.bar(posiciones + (indice - 1) * ancho, valores, ancho, label=nombre.replace("_", " ").title())
        ax.bar_label(barras, fmt="%.2f", padding=2, fontsize=8)
    ax.set(xticks=posiciones, xticklabels=metricas, ylim=(0, 1.12), ylabel="Puntaje", title="Comparación de modelos — misma partición de prueba")
    ax.legend(); ax.grid(axis="y", alpha=.3); fig.tight_layout()
    CARPETA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    fig.savefig(CARPETA_RESULTADOS / "comparacion_modelos.png", dpi=180); plt.close(fig)


def guardar_modelo(nombre: str, modelo, x: np.ndarray, y: np.ndarray, demostracion: bool) -> Path:
    modelo.fit(x, y)
    ruta = CARPETA_MODELOS / f"adhd_{nombre}.pkl"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("wb") as archivo:
        pickle.dump({
            "modelo": modelo,
            "features": FEATURES,
            "algoritmo": {"random_forest": "Random Forest", "svm": "SVM",
                          "regresion_lineal": "Regresión logística (clasificador lineal)"}[nombre],
            "datos_demostracion": demostracion,
        }, archivo)
    return ruta


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena SVM y regresión lineal logística para ADHD-RS-IV.")
    parser.add_argument("--entrenar", type=Path, default=CSV_POR_DEFECTO, metavar="CSV")
    args = parser.parse_args()

    x, y, demostracion = cargar_csv(args.entrenar)
    print("ADVERTENCIA: apoyo de tamizaje; no constituye un diagnóstico clínico.")
    if demostracion:
        print("MODO DEMOSTRACIÓN: el CSV está vacío; se usaron datos sintéticos deterministas.")
    evaluaciones = {}
    for nombre, modelo in crear_modelos().items():
        evaluacion = evaluar(nombre.upper(), modelo, x, y)
        evaluaciones[nombre] = evaluacion
        guardar_graficos(nombre, evaluacion)
        ruta = guardar_modelo(nombre, modelo, x, y, demostracion)
        print(f"Modelo guardado: {ruta}")
    guardar_comparacion(evaluaciones)
    print(f"Gráficas guardadas en: {CARPETA_RESULTADOS}")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)
