#!/usr/bin/env python3
# %%
"""Random Forest para 30 registros de ADHD Rating Scale-IV.

Todo el resultado se imprime en la consola: no se generan PNG, ventanas,
modelos serializados ni archivos auxiliares.

Uso:
    python scripts/enmtrenamiento.py --crear-plantilla > datos_adhd.csv
    python scripts/enmtrenamiento.py --entrenar datos_adhd.csv
    python scripts/enmtrenamiento.py --entrenar datos_adhd.csv --predecir 0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2

El CSV debe tener exactamente 30 filas y las columnas item_1 ... item_18,
tamizaje_positivo. Cada item vale de 0 a 3; tamizaje_positivo vale 0 o 1.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import pickle
import sys

import matplotlib.pyplot as plt
import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, average_precision_score, balanced_accuracy_score,
    confusion_matrix, f1_score, make_scorer, precision_score, precision_recall_curve,
    recall_score, roc_auc_score, roc_curve,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split


SEMILLA = 42
TOTAL_REGISTROS = 30
RAIZ = Path(__file__).resolve().parent.parent
CSV_POR_DEFECTO = RAIZ / "datos" / "respuestas_adhd.csv"
MODELO_POR_DEFECTO = RAIZ / "modelos" / "adhd_random_forest.pkl"
FEATURES = [f"item_{numero}" for numero in range(1, 19)]
NOMBRES_ITEMS = [
    "Atención a detalles", "Mueve manos o pies", "Mantiene atención",
    "Permanece sentado", "Parece no escuchar", "Corre o trepa",
    "Sigue instrucciones", "Juega calladamente", "Organiza tareas",
    "Activado por motor", "Evita esfuerzo mental", "Habla excesivamente",
    "Pierde cosas", "Responde impulsivamente", "Se distrae",
    "Espera su turno", "Es olvidadizo", "Interrumpe",
]


def plantilla() -> None:
    """Imprime una plantilla CSV vacía de 30 registros en la consola."""
    columnas = [*FEATURES, "tamizaje_positivo"]
    escritor = csv.DictWriter(sys.stdout, fieldnames=columnas, lineterminator="\n")
    escritor.writeheader()
    for _ in range(TOTAL_REGISTROS):
        escritor.writerow({columna: "" for columna in columnas})


def generar_datos_demostracion() -> tuple[np.ndarray, np.ndarray]:
    """Genera 30 registros simulados solo para visualizar la salida en consola."""
    generador = np.random.default_rng(SEMILLA)
    respuestas = generador.integers(0, 4, size=(TOTAL_REGISTROS, len(FEATURES)))
    inatencion = (respuestas[:, [0, 2, 4, 6, 8, 10, 12, 14, 16]] >= 2).sum(axis=1)
    hiperactividad = (respuestas[:, [1, 3, 5, 7, 9, 11, 13, 15, 17]] >= 2).sum(axis=1)
    etiquetas = ((inatencion >= 6) | (hiperactividad >= 6)).astype(int)
    # Evita una separación perfecta; no representa un diagnóstico real.
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

    columnas_modelo = [*FEATURES, "tamizaje_positivo"]
    if all(not str(fila.get(columna, "")).strip() for fila in filas for columna in columnas_modelo):
        x, y = generar_datos_demostracion()
        return x, y, True

    respuestas, etiquetas = [], []
    for numero, fila in enumerate(filas, start=2):
        try:
            items = [int(fila[item]) for item in FEATURES]
            etiqueta = int(fila["tamizaje_positivo"])
        except (TypeError, ValueError) as error:
            raise ValueError(f"Fila {numero}: complete los 18 ítems y tamizaje_positivo.") from error
        if any(valor not in (0, 1, 2, 3) for valor in items):
            raise ValueError(f"Fila {numero}: cada ítem debe estar entre 0 y 3.")
        if etiqueta not in (0, 1):
            raise ValueError(f"Fila {numero}: tamizaje_positivo debe ser 0 o 1.")
        respuestas.append(items)
        etiquetas.append(etiqueta)

    x, y = np.asarray(respuestas), np.asarray(etiquetas)
    if np.bincount(y, minlength=2).min() < 2:
        raise ValueError("Debe haber al menos dos registros de cada clase (0 y 1).")
    return x, y, False


def barra(valor: float, ancho: int = 30) -> str:
    llenos = round(max(0.0, min(1.0, valor)) * ancho)
    return "#" * llenos + "-" * (ancho - llenos)


def imprimir_metricas(y_real: np.ndarray, pred: np.ndarray, prob: np.ndarray) -> None:
    tn, fp, fn, tp = confusion_matrix(y_real, pred, labels=[0, 1]).ravel()
    especificidad = tn / (tn + fp) if tn + fp else 0.0
    metricas = [
        ("Accuracy", accuracy_score(y_real, pred)),
        ("Balanced accuracy", balanced_accuracy_score(y_real, pred)),
        ("Precisión", precision_score(y_real, pred, zero_division=0)),
        ("Recall / sensibilidad", recall_score(y_real, pred, zero_division=0)),
        ("Especificidad", especificidad),
        ("F1-score", f1_score(y_real, pred, zero_division=0)),
    ]
    if len(np.unique(y_real)) == 2:
        metricas += [("ROC-AUC", roc_auc_score(y_real, prob)), ("PR-AUC", average_precision_score(y_real, prob))]

    print("\nMÉTRICAS DE EVALUACIÓN (gráfico en consola)")
    for nombre, valor in metricas:
        print(f"{nombre:24} {valor:6.3f} |{barra(valor)}|")
    print("\nMATRIZ DE CONFUSIÓN")
    print("                    Predicho")
    print("                 Negativo  Positivo")
    print(f"Real negativo    {tn:8d}  {fp:8d}")
    print(f"Real positivo    {fn:8d}  {tp:8d}")

    if len(np.unique(y_real)) == 2:
        fpr, tpr, _ = roc_curve(y_real, prob)
        precision, recall, _ = precision_recall_curve(y_real, prob)
        print("\nCURVA ROC (puntos: FPR, TPR)")
        print("  " + " | ".join(f"{a:.2f}, {b:.2f}" for a, b in zip(fpr, tpr)))
        print("CURVA PRECISIÓN-RECALL (puntos: recall, precisión)")
        print("  " + " | ".join(f"{a:.2f}, {b:.2f}" for a, b in zip(recall, precision)))


def imprimir_importancias(modelo: RandomForestClassifier) -> None:
    print("\nIMPORTANCIA DE LOS ÍTEMS (gráfico en consola)")
    for indice in np.argsort(modelo.feature_importances_)[::-1]:
        valor = modelo.feature_importances_[indice]
        print(f"{indice + 1:02d}. {NOMBRES_ITEMS[indice]:27.27} {valor:6.3f} |{barra(valor * 5)}|")


def mostrar_graficos(modelo: RandomForestClassifier, x_entrenamiento: np.ndarray,
                      y_entrenamiento: np.ndarray, y_real: np.ndarray,
                      pred: np.ndarray, prob: np.ndarray) -> None:
    """Muestra las siete figuras de Matplotlib en VS Code/Jupyter o ventanas."""
    tn, fp, fn, tp = confusion_matrix(y_real, pred, labels=[0, 1]).ravel()
    especificidad = tn / (tn + fp) if tn + fp else 0.0
    metricas = {
        "Accuracy": accuracy_score(y_real, pred),
        "Balanced\naccuracy": balanced_accuracy_score(y_real, pred),
        "Precisión": precision_score(y_real, pred, zero_division=0),
        "Recall": recall_score(y_real, pred, zero_division=0),
        "Especificidad": especificidad,
        "F1": f1_score(y_real, pred, zero_division=0),
    }
    if len(np.unique(y_real)) == 2:
        metricas["ROC-AUC"] = roc_auc_score(y_real, prob)
        metricas["PR-AUC"] = average_precision_score(y_real, prob)

    fig, ax = plt.subplots(figsize=(10, 5))
    barras = ax.bar(metricas.keys(), metricas.values(), color="#2563eb")
    ax.set_ylim(0, 1)
    ax.set_title("1. Métricas del Random Forest")
    ax.tick_params(axis="x", rotation=25)
    for barra_actual, valor in zip(barras, metricas.values()):
        ax.text(barra_actual.get_x() + barra_actual.get_width() / 2, valor + .02, f"{valor:.2f}", ha="center")

    fig, ax = plt.subplots(figsize=(6, 5))
    imagen = ax.imshow([[tn, fp], [fn, tp]], cmap="Blues")
    fig.colorbar(imagen, ax=ax)
    ax.set_xticks([0, 1], ["Negativo", "Positivo"])
    ax.set_yticks([0, 1], ["Negativo", "Positivo"])
    ax.set_xlabel("Predicho")
    ax.set_ylabel("Real")
    ax.set_title("2. Matriz de confusión")
    for fila in range(2):
        for columna in range(2):
            ax.text(columna, fila, str([[tn, fp], [fn, tp]][fila][columna]), ha="center", va="center")

    if len(np.unique(y_real)) == 2:
        fpr, tpr, _ = roc_curve(y_real, prob)
        fig, ax = plt.subplots(figsize=(7, 6))
        ax.plot(fpr, tpr, color="#2563eb", label=f"Random Forest (AUC = {roc_auc_score(y_real, prob):.3f})")
        ax.plot([0, 1], [0, 1], "--", color="gray", label="Aleatorio")
        ax.set(xlabel="Tasa de falsos positivos", ylabel="Tasa de verdaderos positivos", title="3. Curva ROC")
        ax.legend(); ax.grid(alpha=.3)

        precision, recall, _ = precision_recall_curve(y_real, prob)
        fig, ax = plt.subplots(figsize=(7, 6))
        ax.plot(recall, precision, color="#16a34a", label=f"Random Forest (AP = {average_precision_score(y_real, prob):.3f})")
        ax.set(xlabel="Recall o sensibilidad", ylabel="Precisión", title="4. Curva Precision Recall")
        ax.legend(); ax.grid(alpha=.3)

        real, predicha = calibration_curve(y_real, prob, n_bins=min(5, len(y_real)), strategy="uniform")
        fig, ax = plt.subplots(figsize=(7, 6))
        ax.plot(predicha, real, "o-", color="#9333ea", label="Modelo")
        ax.plot([0, 1], [0, 1], "--", color="gray", label="Calibración perfecta")
        ax.set(xlabel="Probabilidad predicha", ylabel="Proporción real de positivos", title="5. Curva de calibración")
        ax.legend(); ax.grid(alpha=.3)

    orden = np.argsort(modelo.feature_importances_)
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.barh([f"{i + 1}. {NOMBRES_ITEMS[i]}" for i in orden], modelo.feature_importances_[orden], color="#f59e0b")
    ax.set(xlabel="Importancia Gini", title="6. Importancia de los 18 ítems")

    clases_minimas = np.bincount(y_entrenamiento, minlength=2).min()
    divisiones = min(5, int(clases_minimas))
    if divisiones >= 2:
        cv = StratifiedKFold(n_splits=divisiones, shuffle=True, random_state=SEMILLA)
        resultados = cross_validate(modelo, x_entrenamiento, y_entrenamiento, cv=cv, n_jobs=-1,
                                    scoring={"Accuracy": "accuracy", "Precision": make_scorer(precision_score, zero_division=0),
                                             "Recall": "recall", "F1": "f1"})
        fig, ax = plt.subplots(figsize=(9, 6))
        nombres = ["Accuracy", "Precision", "Recall", "F1"]
        ax.boxplot([resultados[f"test_{nombre}"] for nombre in nombres], tick_labels=nombres)
        ax.set(ylim=(0, 1), ylabel="Resultado por fold", title=f"7. Validación cruzada estratificada ({divisiones} folds)")
        ax.grid(axis="y", alpha=.3)
    plt.tight_layout()
    plt.show()


def leer_prediccion(texto: str) -> np.ndarray:
    try:
        valores = [int(valor.strip()) for valor in texto.split(",")]
    except ValueError as error:
        raise ValueError("--predecir debe contener 18 números separados por comas.") from error
    if len(valores) != 18 or any(valor not in (0, 1, 2, 3) for valor in valores):
        raise ValueError("--predecir requiere exactamente 18 valores enteros entre 0 y 3.")
    return np.asarray([valores])


def entrenar(ruta: Path, prediccion: str | None, modelo_salida: Path | None) -> None:
    x, y, es_demostracion = cargar_csv(ruta)
    x_entrenamiento, x_prueba, y_entrenamiento, y_prueba = train_test_split(
        x, y, test_size=0.20, random_state=SEMILLA, stratify=y
    )
    modelo = RandomForestClassifier(
        n_estimators=300, max_features="sqrt", min_samples_leaf=1,
        class_weight="balanced", random_state=SEMILLA, n_jobs=-1,
    )
    modelo.fit(x_entrenamiento, y_entrenamiento)
    pred = modelo.predict(x_prueba)
    prob = modelo.predict_proba(x_prueba)[:, 1]

    print("RANDOM FOREST — ADHD RATING SCALE-IV")
    print("Registros totales: 30 | Entrenamiento: 24 | Prueba: 6")
    print("Todo se muestra en consola. No se generan imágenes ni archivos de salida.")
    if es_demostracion:
        print("MODO DEMOSTRACIÓN: el CSV está vacío; se usaron 30 registros sintéticos en memoria.")
    print("Aviso: es un apoyo de tamizaje y no un diagnóstico clínico.")
    imprimir_metricas(y_prueba, pred, prob)
    imprimir_importancias(modelo)
    mostrar_graficos(modelo, x_entrenamiento, y_entrenamiento, y_prueba, pred, prob)

    if modelo_salida is not None:
        # Se reentrena con todos los registros antes de publicarlo para que la
        # API use toda la información disponible, no solo los 24 del split.
        modelo.fit(x, y)
        modelo_salida.parent.mkdir(parents=True, exist_ok=True)
        with modelo_salida.open("wb") as archivo:
            pickle.dump({"modelo": modelo, "features": FEATURES}, archivo)
        print(f"\nModelo entrenado guardado en: {modelo_salida}")

    if prediccion is not None:
        caso = leer_prediccion(prediccion)
        probabilidad = modelo.predict_proba(caso)[0, 1]
        clase = int(modelo.predict(caso)[0])
        print("\nRESULTADO DEL NUEVO REGISTRO")
        print(f"Clasificación de tamizaje: {'POSITIVO' if clase else 'NEGATIVO'}")
        print(f"Probabilidad estimada de positivo: {probabilidad:.1%}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena y consulta un Random Forest con 30 registros ADHD.")
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--crear-plantilla", action="store_true", help="Imprime el CSV vacío de 30 registros.")
    grupo.add_argument(
        "--entrenar", type=Path, metavar="CSV", default=CSV_POR_DEFECTO,
        help="CSV de 30 registros para entrenar. Por defecto: datos/respuestas_adhd.csv.",
    )
    parser.add_argument("--predecir", metavar="ITEMS", help="18 valores 0-3 separados por comas; se consulta tras entrenar.")
    parser.add_argument(
        "--guardar-modelo", nargs="?", type=Path, const=MODELO_POR_DEFECTO,
        help="Guarda el modelo entrenado para que Laravel lo use. Sin ruta usa modelos/adhd_random_forest.pkl.",
    )
    args = parser.parse_args()
    if args.crear_plantilla:
        plantilla()
    else:
        entrenar(args.entrenar, args.predecir, args.guardar_modelo)


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(2)
