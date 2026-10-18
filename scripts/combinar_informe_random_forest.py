from copy import deepcopy
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import shutil
import tempfile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "resultados_svm_regresion_logistica_adhd_ampliado_con_random_forest.docx"
SOURCE = ROOT / "documentos" / "informe_random_forest_30_registros.docx"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
ET.register_namespace("w", W)
ET.register_namespace("r", R)
# Estas declaraciones siguen siendo necesarias porque mc:Ignorable las referencia,
# aunque el árbol no contenga elementos w14/wp14 después de una edición XML.
ET.register_namespace("w14", "http://schemas.microsoft.com/office/word/2010/wordml")
ET.register_namespace("wp14", "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing")


def qn(name: str) -> str:
    prefix, local = name.split(":")
    return f"{{{W if prefix == 'w' else R}}}{local}"


def text_of(element) -> str:
    return "".join(node.text or "" for node in element.iter(qn("w:t")))


def paragraph(text: str, style: str | None = None):
    p = ET.Element(qn("w:p"))
    if style:
        props = ET.SubElement(p, qn("w:pPr"))
        ET.SubElement(props, qn("w:pStyle"), {qn("w:val"): style})
    run = ET.SubElement(p, qn("w:r"))
    node = ET.SubElement(run, qn("w:t"))
    node.text = text
    return p


def replace_texts(table, values):
    nodes = list(table.iter(qn("w:t")))
    if len(nodes) != len(values):
        raise RuntimeError(f"La tabla de referencia tiene {len(nodes)} textos; se esperaban {len(values)}.")
    for node, value in zip(nodes, values):
        node.text = value


def main():
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        target_dir = temp / "target"
        source_dir = temp / "source"
        with ZipFile(TARGET) as archive:
            archive.extractall(target_dir)
        with ZipFile(SOURCE) as archive:
            archive.extractall(source_dir)

        target_tree = ET.parse(target_dir / "word" / "document.xml")
        target_root = target_tree.getroot()
        # ElementTree omite declaraciones de espacios de nombres no usados por
        # nodos; Word las requiere porque mc:Ignorable las enumera en el root.
        target_root.set("xmlns:w14", "http://schemas.microsoft.com/office/word/2010/wordml")
        target_root.set("xmlns:wp14", "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing")
        target_body = target_root.find(qn("w:body"))
        title = next(item for item in target_body if text_of(item).startswith("Resultados de los modelos SVM"))
        next(title.iter(qn("w:t"))).text = "Resultados de los modelos SVM Regresión logística y Random Forest para ADHD Rating Scale IV"
        source_tree = ET.parse(source_dir / "word" / "document.xml")
        source_body = source_tree.getroot().find(qn("w:body"))

        # Relaciones de las siete figuras de Random Forest.
        target_rels_path = target_dir / "word" / "_rels" / "document.xml.rels"
        target_rels_tree = ET.parse(target_rels_path)
        target_rels_root = target_rels_tree.getroot()
        source_rels_root = ET.parse(source_dir / "word" / "_rels" / "document.xml.rels").getroot()
        source_rels = {rel.attrib["Id"]: rel for rel in source_rels_root}
        used_ids = {rel.attrib["Id"] for rel in target_rels_root}
        numeric_ids = [int(item[3:]) for item in used_ids if item.startswith("rId") and item[3:].isdigit()]
        next_id = max(numeric_ids, default=0) + 1
        relationship_map = {}
        media_dir = target_dir / "word" / "media"
        media_dir.mkdir(exist_ok=True)

        def import_relationship(old_id: str) -> str:
            nonlocal next_id
            if old_id in relationship_map:
                return relationship_map[old_id]
            rel = source_rels[old_id]
            new_id = f"rId{next_id}"
            next_id += 1
            attrs = dict(rel.attrib)
            attrs["Id"] = new_id
            target = attrs.get("Target", "")
            if target.startswith("media/"):
                source_file = source_dir / "word" / target
                new_name = f"random_forest_{source_file.name}"
                shutil.copy2(source_file, media_dir / new_name)
                attrs["Target"] = f"media/{new_name}"
            target_rels_root.append(ET.Element(f"{{{REL}}}Relationship", attrs))
            relationship_map[old_id] = new_id
            return new_id

        # Selecciona el bloque de resultados del informe de Random Forest, sin portada ni limitación duplicada.
        source_children = list(source_body)
        start = next(i for i, item in enumerate(source_children) if text_of(item) == "Métricas de evaluación")
        end = next(i for i, item in enumerate(source_children) if text_of(item) == "Limitaciones")
        rf_content = [deepcopy(item) for item in source_children[start:end]]
        existing_picture_ids = [int(node.attrib.get("id", "0")) for node in target_root.iter(f"{{{WP}}}docPr")]
        next_picture_id = max(existing_picture_ids, default=0) + 1
        for item in rf_content:
            for node in item.iter():
                embedded = node.attrib.get(qn("r:embed"))
                if embedded:
                    node.set(qn("r:embed"), import_relationship(embedded))
                if node.tag == f"{{{WP}}}docPr":
                    node.set("id", str(next_picture_id))
                    node.set("name", f"Random Forest {next_picture_id}")
                    next_picture_id += 1

        # Usa la tabla de métricas SVM como plantilla, preservando el diseño del informe.
        template_table = next(item for item in target_body if item.tag == qn("w:tbl"))
        metrics_table = deepcopy(template_table)
        replace_texts(metrics_table, [
            "Métrica", "Resultado", "Interpretación",
            "Accuracy", "0.6667", "Proporción total de clasificaciones correctas.",
            "Balanced accuracy", "0.5000", "Promedio equilibrado del acierto en ambas clases.",
            "Precision", "0.0000", "Proporción de positivos predichos que fueron positivos.",
            "Recall o sensibilidad", "0.0000", "Proporción de positivos identificados correctamente.",
            "Especificidad", "1.0000", "Proporción de negativos identificados correctamente.",
            "F1 score", "0.0000", "Equilibrio entre precisión y sensibilidad.",
            "ROC AUC", "0.8750", "Capacidad de separar las clases positiva y negativa.",
            "PR AUC", "0.8333", "Desempeño de precisión y sensibilidad en distintos umbrales.",
        ])

        intro = [
            paragraph("Random Forest", "Heading1"),
            paragraph("Esta sección presenta los resultados del modelo Random Forest aplicado al tamizaje ADHD Rating Scale IV para profesores. La evaluación usa la misma división estratificada: 24 registros para entrenamiento y 6 para prueba."),
            metrics_table,
            paragraph("En esta partición, Random Forest obtuvo una exactitud de 0.6667, equivalente a cuatro clasificaciones correctas de seis. La exactitud balanceada de 0.5000 y los valores de precisión, sensibilidad y F1 de 0.0000 reflejan que el umbral empleado no identificó los dos casos positivos. La especificidad de 1.0000 indica que los cuatro negativos fueron reconocidos. Al mismo tiempo, ROC AUC de 0.8750 y PR AUC de 0.8333 muestran una ordenación favorable de las probabilidades a distintos umbrales; estos valores no sustituyen la sensibilidad observada con el umbral actual. Como la prueba se realizó con seis registros sintéticos, los resultados son técnicos y no constituyen validación clínica."),
        ]

        # Inserta Random Forest antes de la comparación final existente.
        comparison_index = next(i for i, item in enumerate(target_body) if text_of(item) == "Comparación y limitación de la prueba")
        for offset, item in enumerate([*intro, *rf_content]):
            target_body.insert(comparison_index + offset, item)

        # Actualiza la conclusión para comparar los tres modelos.
        comparison_index = next(i for i, item in enumerate(target_body) if text_of(item) == "Comparación y limitación de la prueba")
        first_comparison = target_body[comparison_index + 1]
        second_comparison = target_body[comparison_index + 2]
        for node in list(first_comparison):
            first_comparison.remove(node)
        revised_first = paragraph("En la partición de prueba, SVM, regresión logística y Random Forest alcanzaron 66.67 por ciento de accuracy. La regresión logística mostró F1 de 0.500 y detectó un caso positivo; SVM y Random Forest tuvieron F1 de 0.000 y no detectaron positivos con el umbral actual. Random Forest presentó ROC AUC de 0.875 y PR AUC de 0.833 en esta partición, lo que indica una ordenación favorable de probabilidades, pero no compensa la falta de sensibilidad a dicho umbral.")
        for node in list(revised_first):
            first_comparison.append(node)
        for node in list(second_comparison):
            second_comparison.remove(node)
        revised_second = paragraph("Los datos y etiquetas son sintéticos porque el archivo fuente aún no contiene respuestas reales. En consecuencia, las métricas solo validan la ejecución del flujo de machine learning. Antes de utilizar cualquiera de los modelos como apoyo al tamizaje, se deben incorporar respuestas reales de docentes y etiquetas profesionales validadas, además de realizar una evaluación con una muestra más amplia.")
        for node in list(revised_second):
            second_comparison.append(node)

        target_tree.write(target_dir / "word" / "document.xml", encoding="utf-8", xml_declaration=True)
        target_rels_tree.write(target_rels_path, encoding="utf-8", xml_declaration=True)
        with ZipFile(TARGET, "w", ZIP_DEFLATED) as archive:
            for file in target_dir.rglob("*"):
                if file.is_file():
                    archive.write(file, file.relative_to(target_dir).as_posix())


if __name__ == "__main__":
    main()
