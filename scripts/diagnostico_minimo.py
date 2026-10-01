#!/usr/bin/env python3
"""Diagnóstico mínimo de prueba.

Recibe por stdin un JSON con las respuestas del formulario y devuelve un
resultado deliberadamente estático. Más adelante aquí podrá sustituirse por la
lógica real (modelo, reglas clínicas, etc.) sin cambiar el contrato de la API.
"""

import json
import sys


PREGUNTAS = [
    ("animo", "¿Cómo calificarías tu estado de ánimo hoy?"),
    ("sueno", "¿Qué tan reparador fue tu sueño reciente?"),
    ("energia", "¿Cómo está tu nivel de energía hoy?"),
    ("concentracion", "¿Qué tan fácil te resulta concentrarte?"),
]


def main():
    entrada = json.load(sys.stdin)
    respuestas = entrada.get("respuestas", {})

    detalles = []
    for codigo, pregunta in PREGUNTAS:
        detalles.append({
            "codigo": codigo,
            "concepto": pregunta,
            "respuesta": respuestas.get(codigo),
            "puntaje": 2,
            "puntaje_maximo": 3,
            "porcentaje": 66.67,
            "observaciones": "Resultado de prueba fijo.",
        })

    salida = {
        "test": {
            "codigo": "diagnostico-minimo",
            "nombre": "Diagnóstico mínimo de prueba",
            "descripcion": "Cuestionario básico de bienestar general.",
            "version": "1.0",
        },
        "resultado": {
            "puntaje_total": 8,
            "puntaje_maximo": 12,
            "porcentaje": 66.67,
            "nivel": "moderado",
            "conclusion": "Resultado fijo de prueba: se recomienda una evaluación posterior.",
            "observaciones": "Generado por el diagnóstico mínimo de prueba.",
        },
        "detalles": detalles,
    }

    # Se escribe UTF-8 de forma explícita para que PHP reciba JSON válido tanto
    # en Windows como en Linux, independientemente de la página de códigos.
    sys.stdout.buffer.write(json.dumps(salida, ensure_ascii=False).encode("utf-8"))


if __name__ == "__main__":
    main()
