#!/usr/bin/env python3
"""Ejecutor de tamizaje ADHD-RS-IV para Laravel.

Laravel envía por stdin un JSON con ``respuestas.item_1`` a
``respuestas.item_18``. El programa responde exclusivamente con JSON por
stdout; no crea ni modifica registros de la base de datos.

El archivo de modelo es generado previamente durante el entrenamiento y se
carga solamente cuando Laravel solicita un diagnóstico.
"""

from __future__ import annotations

import json
import pickle
import sys
from base64 import b64decode
from pathlib import Path

import numpy as np


RAIZ = Path(__file__).resolve().parent.parent
MODELO_POR_DEFECTO = RAIZ / "modelos" / "adhd_random_forest.pkl"
ITEMS = tuple(f"item_{numero}" for numero in range(1, 19))
NOMBRES_ITEMS = (
    "Atención a detalles", "Mueve manos o pies", "Mantiene atención",
    "Permanece sentado", "Parece no escuchar", "Corre o trepa",
    "Sigue instrucciones", "Juega calladamente", "Organiza tareas",
    "Activado por motor", "Evita esfuerzo mental", "Habla excesivamente",
    "Pierde cosas", "Responde impulsivamente", "Se distrae",
    "Espera su turno", "Es olvidadizo", "Interrumpe",
)
INDICES_INATENCION = (0, 2, 4, 6, 8, 10, 12, 14, 16)
INDICES_HIPERACTIVIDAD = (1, 3, 5, 7, 9, 11, 13, 15, 17)


def error(mensaje: str) -> None:
    print(json.dumps({"error": mensaje}, ensure_ascii=False))
    raise SystemExit(1)


def cargar_respuestas(entrada: dict) -> list[int]:
    respuestas = entrada.get("respuestas")
    if not isinstance(respuestas, dict):
        error("'respuestas' debe ser un objeto con item_1 a item_18.")

    faltantes = [item for item in ITEMS if item not in respuestas]
    if faltantes:
        error(f"Faltan respuestas: {', '.join(faltantes)}.")

    valores: list[int] = []
    for item in ITEMS:
        valor = respuestas[item]
        if isinstance(valor, bool) or not isinstance(valor, int) or valor not in (0, 1, 2, 3):
            error(f"{item} debe ser un entero entre 0 y 3.")
        valores.append(valor)
    return valores


def cargar_modelo(ruta: Path):
    if not ruta.is_file():
        error("No existe el modelo entrenado. Entrene y publique modelos/adhd_random_forest.pkl antes de diagnosticar.")
    try:
        with ruta.open("rb") as archivo:
            paquete = pickle.load(archivo)
    except (OSError, pickle.UnpicklingError, EOFError, AttributeError, ImportError) as exc:
        error(f"No se pudo cargar el modelo entrenado: {exc}")

    modelo = paquete.get("modelo") if isinstance(paquete, dict) else paquete
    if not hasattr(modelo, "predict") or not hasattr(modelo, "predict_proba"):
        error("El archivo de modelo no contiene un clasificador compatible.")
    return modelo


def clasificacion_regla(inatencion: int, hiperactividad: int) -> tuple[str, str]:
    if inatencion >= 6 and hiperactividad >= 6:
        return "positivo_combinado", "Tamizaje positivo en inatención y en hiperactividad/impulsividad. Requiere evaluación clínica profesional."
    if inatencion >= 6:
        return "positivo_inatencion", "Tamizaje positivo para síntomas de inatención. Requiere evaluación clínica profesional."
    if hiperactividad >= 6:
        return "positivo_hiperactividad_impulsividad", "Tamizaje positivo para síntomas de hiperactividad/impulsividad. Requiere evaluación clínica profesional."
    return "negativo", "El tamizaje no alcanza el umbral de síntomas frecuentes; no reemplaza una evaluación clínica profesional."


def main() -> None:
    try:
        # Laravel envía un único argumento Base64; se conserva stdin para poder
        # ejecutar y probar el archivo manualmente si fuera necesario.
        if len(sys.argv) == 2:
            entrada = json.loads(b64decode(sys.argv[1]).decode("utf-8"))
        else:
            entrada = json.load(sys.stdin)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        error("La entrada debe ser un JSON válido.")
    if not isinstance(entrada, dict):
        error("La entrada debe ser un objeto JSON.")

    valores = cargar_respuestas(entrada)
    modelo = cargar_modelo(MODELO_POR_DEFECTO)
    vector = np.asarray([valores])
    probabilidad = float(modelo.predict_proba(vector)[0, 1])
    prediccion_modelo = int(modelo.predict(vector)[0])

    sintomas_inatencion = sum(valores[indice] >= 2 for indice in INDICES_INATENCION)
    sintomas_hiperactividad = sum(valores[indice] >= 2 for indice in INDICES_HIPERACTIVIDAD)
    clasificacion, conclusion = clasificacion_regla(sintomas_inatencion, sintomas_hiperactividad)
    total = sum(valores)
    detalles = [
        {
            "codigo": item,
            "concepto": NOMBRES_ITEMS[indice],
            "respuesta": valores[indice],
            "puntaje": valores[indice],
            "puntaje_maximo": 3,
            "porcentaje": round(valores[indice] / 3 * 100, 2),
            "observaciones": "Síntoma frecuente" if valores[indice] >= 2 else "Síntoma no frecuente",
        }
        for indice, item in enumerate(ITEMS)
    ]
    salida = {
        "test": {
            "codigo": "adhd-rs-iv-docente",
            "nombre": "ADHD Rating Scale-IV — Docente",
            "descripcion": "Tamizaje de 18 ítems para reporte docente; no constituye un diagnóstico clínico.",
            "version": "1.0",
        },
        "resultado": {
            "puntaje_total": total,
            "puntaje_maximo": 54,
            "porcentaje": round(total / 54 * 100, 2),
            "sintomas_inatencion": sintomas_inatencion,
            "sintomas_hiperactividad_impulsividad": sintomas_hiperactividad,
            "clasificacion_tamizaje": clasificacion,
            "prediccion_modelo": "positivo" if prediccion_modelo else "negativo",
            "probabilidad_modelo": round(probabilidad, 4),
            "conclusion": conclusion,
            "observaciones": "Resultado de tamizaje basado en respuestas del docente y en un modelo entrenado; requiere interpretación profesional.",
        },
        "detalles": detalles,
    }
    sys.stdout.buffer.write(json.dumps(salida, ensure_ascii=False).encode("utf-8"))


if __name__ == "__main__":
    main()
