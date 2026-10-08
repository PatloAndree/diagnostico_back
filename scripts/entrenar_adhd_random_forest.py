#!/usr/bin/env python3
"""Entrena una línea base sintética para ADHD Rating Scale-IV (profesores).

No usa historias clínicas ni diagnósticos reales. Las 18 respuestas se generan
aleatoriamente entre 0 y 3 y la etiqueta también es sintética: reproduce el
criterio de tamizaje de seis síntomas (valor >= 2) en alguna subescala, con
ruido controlado. Por ello las métricas son exclusivamente una comprobación
técnica del pipeline, no evidencia de validez clínica ni diagnóstica.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, average_precision_score, balanced_accuracy_score,
    brier_score_loss, classification_report, cohen_kappa_score,
    confusion_matrix, f1_score, log_loss, matthews_corrcoef,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split


ITEMS = {
    1: "No logra prestar atención a detalles o es descuidado con su trabajo escolar.",
    2: "Continuamente mueve sus manos o pies o se retuerce en el asiento.",
    3: "Tiene dificultad en mantener su atención en las tareas o actividades de juego.",
    4: "No permanece en su asiento cuando se requiere que se mantenga sentado.",
    5: "No parece escuchar cuando se le habla directamente.",
    6: "Corre y se encarama excesivamente en situaciones no apropiadas.",
    7: "No sigue instrucciones y no logra terminar su trabajo.",
    8: "Tiene dificultad realizando calladamente actividades recreativas o de descanso.",
    9: "Tiene dificultad para organizar sus tareas o actividades.",
    10: "Está siempre de prisa o actúa como si estuviera activado por un motor.",
    11: "Evita tareas que requieren un esfuerzo mental continuo.",
    12: "Habla excesivamente.",
    13: "Pierde cosas necesarias para sus tareas o actividades.",
    14: "Responde impulsivamente antes de que se termine de preguntar.",
    15: "Se distrae fácilmente.",
    16: "Tiene dificultad en esperar su turno.",
    17: "Es olvidadizo con sus actividades diarias.",
    18: "Interrumpe o se entromete sin la autorización de otros.",
}
INATENCION = (1, 3, 5, 7, 9, 11, 13, 15, 17)
HIPERACTIVIDAD_IMPULSIVIDAD = (2, 4, 6, 8, 10, 12, 14, 16, 18)
FEATURES = [f"item_{numero}" for numero in ITEMS]


def generar_datos_sinteticos(muestras: int, semilla: int, ruido: float) -> tuple[np.ndarray, np.ndarray]:
    """Genera respuestas uniformes 0--3 y una etiqueta de tamizaje simulada."""
    generador = np.random.default_rng(semilla)
    respuestas = generador.integers(0, 4, size=(muestras, len(FEATURES)), endpoint=False)
    inatencion = (respuestas[:, np.array(INATENCION) - 1] >= 2).sum(axis=1)
    hiperactividad = (respuestas[:, np.array(HIPERACTIVIDAD_IMPULSIVIDAD) - 1] >= 2).sum(axis=1)
    etiqueta = ((inatencion >= 6) | (hiperactividad >= 6)).astype(int)
    # No representa error clínico: solo evita una evaluación sintética trivial.
    cambiar_etiqueta = generador.random(muestras) < ruido
    etiqueta[cambiar_etiqueta] = 1 - etiqueta[cambiar_etiqueta]
    return respuestas, etiqueta


def evaluar(modelo: RandomForestClassifier, x_prueba: np.ndarray, y_prueba: np.ndarray) -> dict:
    predicciones = modelo.predict(x_prueba)
    probabilidades = modelo.predict_proba(x_prueba)[:, 1]
    tn, fp, fn, tp = confusion_matrix(y_prueba, predicciones, labels=[0, 1]).ravel()
    return {
        "tamano_prueba": int(len(y_prueba)),
        "prevalencia_positiva": round(float(y_prueba.mean()), 6),
        "umbral_decision": 0.5,
        "accuracy": round(float(accuracy_score(y_prueba, predicciones)), 6),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_prueba, predicciones)), 6),
        "precision": round(float(precision_score(y_prueba, predicciones, zero_division=0)), 6),
        "recall_sensibilidad": round(float(recall_score(y_prueba, predicciones, zero_division=0)), 6),
        "especificidad": round(float(tn / (tn + fp)) if tn + fp else 0.0, 6),
        "f1": round(float(f1_score(y_prueba, predicciones, zero_division=0)), 6),
        "roc_auc": round(float(roc_auc_score(y_prueba, probabilidades)), 6),
        "average_precision_pr_auc": round(float(average_precision_score(y_prueba, probabilidades)), 6),
        "matthews_corrcoef": round(float(matthews_corrcoef(y_prueba, predicciones)), 6),
        "cohen_kappa": round(float(cohen_kappa_score(y_prueba, predicciones)), 6),
        "log_loss": round(float(log_loss(y_prueba, probabilidades, labels=[0, 1])), 6),
        "brier_score": round(float(brier_score_loss(y_prueba, probabilidades)), 6),
        "matriz_confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "reporte_por_clase": classification_report(y_prueba, predicciones, output_dict=True, zero_division=0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena Random Forest para datos sintéticos ADHD-RS-IV.")
    parser.add_argument("--muestras", type=int, default=10_000)
    parser.add_argument("--semilla", type=int, default=42)
    parser.add_argument("--ruido", type=float, default=0.12)
    parser.add_argument("--salida", type=Path, default=Path("storage/app/ml/adhd_random_forest"))
    args = parser.parse_args()
    if args.muestras < 100 or not 0 <= args.ruido < 0.5:
        parser.error("--muestras debe ser >= 100 y --ruido debe estar entre 0 y 0.5.")

    x, y = generar_datos_sinteticos(args.muestras, args.semilla, args.ruido)
    x_entrenamiento, x_prueba, y_entrenamiento, y_prueba = train_test_split(
        x, y, test_size=0.20, random_state=args.semilla, stratify=y
    )
    modelo = RandomForestClassifier(
        n_estimators=500, max_features="sqrt", min_samples_leaf=2,
        class_weight="balanced", random_state=args.semilla, n_jobs=-1,
    )
    modelo.fit(x_entrenamiento, y_entrenamiento)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=args.semilla)
    cv_resultado = cross_validate(
        modelo, x_entrenamiento, y_entrenamiento, cv=cv,
        scoring={"accuracy": "accuracy", "precision": "precision", "recall": "recall", "f1": "f1", "roc_auc": "roc_auc"}, n_jobs=-1,
    )

    args.salida.mkdir(parents=True, exist_ok=True)
    ruta_modelo = args.salida / "modelo.joblib"
    ruta_metricas = args.salida / "metricas.json"
    joblib.dump({"modelo": modelo, "features": FEATURES, "version": "ADHD-RS-IV-profesores-sintetico-1"}, ruta_modelo)
    metricas = evaluar(modelo, x_prueba, y_prueba)
    metricas.update({
        "advertencia": "Entrenado y evaluado con datos y etiquetas sintéticos. No usar para diagnóstico clínico.",
        "modelo": "RandomForestClassifier", "version_dataset": "ADHD-RS-IV-profesores-sintetico-1",
        "parametros": modelo.get_params(), "muestras_total": args.muestras,
        "muestras_entrenamiento": int(len(y_entrenamiento)), "semilla": args.semilla, "ruido_etiqueta": args.ruido,
        "criterio_etiqueta_sintetica": "Positiva si >=6 ítems con valor >=2 en inatención o hiperactividad/impulsividad; luego se invierte una fracción controlada.",
        "subescalas": {"inatencion": list(INATENCION), "hiperactividad_impulsividad": list(HIPERACTIVIDAD_IMPULSIVIDAD)},
        "validacion_cruzada_5_folds": {
            nombre: {"media": round(float(valores.mean()), 6), "desviacion_estandar": round(float(valores.std()), 6)}
            for nombre, valores in cv_resultado.items() if nombre.startswith("test_")
        },
        "importancia_variables": [
            {"item": indice + 1, "feature": FEATURES[indice], "pregunta": ITEMS[indice + 1], "importancia": round(float(valor), 6)}
            for indice, valor in sorted(enumerate(modelo.feature_importances_), key=lambda par: par[1], reverse=True)
        ],
    })
    ruta_metricas.write_text(json.dumps(metricas, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
    print(f"Modelo: {ruta_modelo}")
    print(f"Métricas: {ruta_metricas}")
    print(json.dumps({clave: metricas[clave] for clave in ("accuracy", "precision", "recall_sensibilidad", "f1", "roc_auc")}, indent=2))


if __name__ == "__main__":
    main()
