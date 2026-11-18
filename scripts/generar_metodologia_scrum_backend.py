from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "documentos" / "metodologia_desarrollo_scrum_backend_adhd.docx"

NAVY = "1F4E79"
PALE_BLUE = "EAF2F8"
GRID = "D9E2F3"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_margins(cell, top=100, start=120, bottom=100, end=120):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("Página ")
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = "PAGE"
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr_text)
    run._r.append(fld_char2)


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = False
    hdr = table.rows[0]
    set_repeat_table_header(hdr)
    for index, text in enumerate(headers):
        cell = hdr.cells[index]
        if widths:
            cell.width = Cm(widths[index])
        set_cell_shading(cell, NAVY)
        set_cell_margins(cell)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        run.font.size = Pt(9)
    for row_index, values in enumerate(rows):
        cells = table.add_row().cells
        for index, value in enumerate(values):
            cell = cells[index]
            if widths:
                cell.width = Cm(widths[index])
            set_cell_margins(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if row_index % 2 == 1:
                set_cell_shading(cell, PALE_BLUE)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.05
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if index == 0 and len(headers) <= 3 else WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(str(value))
            run.font.size = Pt(8.7)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    p.add_run(text)


def paragraph(doc, text, bold_lead=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(7)
    p.paragraph_format.line_spacing = 1.12
    if bold_lead:
        lead, rest = text.split(" ", 1)
        r = p.add_run(lead + " ")
        r.bold = True
        p.add_run(rest)
    else:
        p.add_run(text)
    return p


def heading(doc, text, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.add_run(text)
    return p


def build():
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2.3)
    section.bottom_margin = Cm(2.2)
    section.left_margin = Cm(2.35)
    section.right_margin = Cm(2.35)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after = Pt(7)
    for name, size in (("Title", 20), ("Heading 1", 14), ("Heading 2", 11.5)):
        style = styles[name]
        style.font.name = "Aptos Display" if name == "Title" else "Aptos"
        style._element.rPr.rFonts.set(qn("w:ascii"), style.font.name)
        style._element.rPr.rFonts.set(qn("w:hAnsi"), style.font.name)
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(12 if name != "Title" else 0)
        style.paragraph_format.space_after = Pt(6)

    footer = section.footer.paragraphs[0]
    footer.style = styles["Normal"]
    footer.paragraph_format.space_before = Pt(6)
    add_page_number(footer)

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("Metodología de desarrollo Scrum aplicada al backend de tamizaje ADHD")
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(18)
    subtitle.add_run("Documento metodológico para el desarrollo de la API y la integración del componente de clasificación").italic = True

    heading(doc, "1 Propósito y alcance")
    paragraph(doc, "Esta metodología describe cómo se aplicó Scrum al desarrollo del backend de una aplicación de apoyo al tamizaje ADHD Rating Scale IV. El trabajo se centró en construir una API REST con Laravel, persistir la información requerida por los flujos de evaluación y conectar el backend con scripts de Python que procesan cuestionarios y modelos de clasificación.")
    paragraph(doc, "El resultado del desarrollo es un conjunto de servicios que permite iniciar sesión, administrar instituciones y pacientes, ejecutar un diagnóstico mínimo de prueba, ejecutar el cuestionario ADHD de 18 ítems y consultar los diagnósticos almacenados. Los resultados entregados por el sistema son de apoyo al tamizaje y no sustituyen la valoración clínica profesional.")
    heading(doc, "2 Enfoque de trabajo")
    paragraph(doc, "Scrum se utilizó como marco de organización del trabajo porque permitió dividir el backend en incrementos funcionales y verificables. Cada incremento combina una necesidad del usuario con sus tareas técnicas: rutas, controlador, validación, modelos, migraciones, tratamiento de errores, persistencia y prueba.")
    add_table(doc, ["Elemento Scrum", "Aplicación en el proyecto"], [
        ("Producto", "Backend Laravel 12 que expone servicios REST para el flujo de tamizaje y consulta de resultados."),
        ("Product Backlog", "Historias de usuario y tareas técnicas priorizadas por dependencia y valor funcional."),
        ("Sprint", "Iteración corta orientada a completar un flujo de backend demostrable."),
        ("Incremento", "Endpoint integrado, validado y persistente, con respuesta JSON comprobable."),
        ("Definition of Done", "Criterios mínimos de validación, seguridad, persistencia, manejo de errores y evidencia de prueba."),
    ], [4.0, 12.3])

    doc.add_page_break()
    heading(doc, "3 Contexto técnico del incremento desarrollado")
    paragraph(doc, "La solución sigue una arquitectura cliente-servidor. El cliente consumidor de la API no forma parte de este entregable metodológico; el alcance documentado corresponde al backend y a su integración local con Python. Laravel concentra las reglas de negocio, la autenticación, las validaciones y la persistencia transaccional. Python procesa el cuestionario y carga los modelos de clasificación previamente entrenados.")
    add_table(doc, ["Componente", "Tecnología y responsabilidad"], [
        ("API", "Laravel 12 y PHP 8.2. Define rutas REST, controladores, validaciones y respuestas JSON."),
        ("Autenticación", "Laravel Sanctum. Genera tokens Bearer al validar las credenciales del usuario."),
        ("Persistencia", "Modelos Eloquent y migraciones para usuarios, instituciones, pacientes, diagnósticos, pruebas y detalles."),
        ("Procesamiento", "Python 3. Ejecuta el diagnóstico mínimo y el procesamiento ADHD; entrega JSON al backend."),
        ("Modelos", "Random Forest, SVM y regresión logística almacenados como archivos pickle para el flujo ADHD."),
        ("Pruebas", "Pruebas feature de Laravel para formulario, ejecución, guardado, listado y detalle del diagnóstico mínimo."),
    ], [4.0, 12.3])
    heading(doc, "4 Roles y responsabilidades")
    paragraph(doc, "En un proyecto académico una misma persona puede asumir varios roles. Para conservar trazabilidad, las responsabilidades se separan conceptualmente aunque el desarrollo sea individual.")
    add_table(doc, ["Rol", "Responsabilidad aplicada"], [
        ("Product Owner", "Prioriza las necesidades del producto: acceso, gestión de pacientes, ejecución del tamizaje y consulta de resultados."),
        ("Scrum Master", "Organiza las ceremonias, identifica bloqueos técnicos y registra acciones de mejora para el siguiente sprint."),
        ("Equipo de desarrollo", "Diseña e implementa rutas, controladores, modelos, migraciones, validaciones, scripts Python y pruebas."),
        ("Asesor o revisor", "Revisa el avance, los entregables y la coherencia entre los objetivos del proyecto y la evidencia técnica."),
        ("Usuario validador", "Aporta retroalimentación sobre el flujo de uso, sin delegar decisiones clínicas al sistema."),
    ], [4.0, 12.3])

    doc.add_page_break()
    heading(doc, "5 Product Backlog implementado")
    paragraph(doc, "El backlog se formuló en historias de usuario y se descompuso en tareas técnicas. Las historias de mayor prioridad fueron las que habilitan el flujo completo desde la autenticación hasta el registro y la consulta de un resultado.")
    add_table(doc, ["Prioridad", "Historia o necesidad", "Evidencia en el backend"], [
        ("Alta", "Como usuario, deseo iniciar sesión para obtener acceso mediante token.", "POST /api/login valida credenciales y devuelve token Bearer de Sanctum."),
        ("Alta", "Como usuario, deseo gestionar instituciones y pacientes.", "Recursos REST para instituciones y pacientes, con validación y relaciones Eloquent."),
        ("Alta", "Como usuario autenticado, deseo enviar un cuestionario de prueba y conservar el resultado.", "GET formulario y POST de diagnóstico mínimo; ejecución Python y guardado transaccional."),
        ("Alta", "Como usuario autenticado, deseo ejecutar el cuestionario ADHD de 18 ítems.", "POST /api/diagnosticos/adhd valida ítems de 0 a 3, ejecuta Python y registra los detalles."),
        ("Media", "Como usuario, deseo consultar diagnósticos y su detalle.", "GET /api/diagnosticos y GET /api/diagnosticos/{diagnostico} con relaciones cargadas."),
        ("Media", "Como responsable técnico, deseo comparar modelos de clasificación.", "Scripts de entrenamiento guardan modelos y gráficos de métricas para Random Forest, SVM y regresión logística."),
    ], [2.0, 6.2, 8.1])
    heading(doc, "6 Plan de sprints")
    paragraph(doc, "La siguiente organización representa los incrementos de desarrollo alcanzados. La duración de cada sprint puede adaptarse al cronograma académico, manteniendo siempre un objetivo, tareas seleccionadas, evidencia de cierre y acciones de mejora.")
    add_table(doc, ["Sprint", "Objetivo", "Incremento verificable"], [
        ("Sprint 0", "Preparar la base del proyecto y el modelo de datos.", "Proyecto Laravel configurado; migraciones y modelos para entidades centrales."),
        ("Sprint 1", "Habilitar el acceso y los catálogos principales.", "Inicio de sesión con Sanctum y servicios REST para instituciones y pacientes."),
        ("Sprint 2", "Construir un flujo de diagnóstico de prueba de extremo a extremo.", "Formulario mínimo, validación, ejecución de Python, transacción y detalle persistido."),
        ("Sprint 3", "Incorporar el flujo ADHD y la clasificación.", "Validación de 18 ítems, carga del modelo, cálculo de resultados y registro de detalles."),
        ("Sprint 4", "Verificar calidad, trazabilidad y consulta de resultados.", "Pruebas feature, endpoints de listado/detalle y documentación de modelos y métricas."),
    ], [2.0, 6.0, 8.3])

    doc.add_page_break()
    heading(doc, "7 Eventos Scrum y control del avance")
    paragraph(doc, "Los eventos de Scrum se aplican de forma ligera y documentable. Su finalidad es mantener visibles las prioridades, resolver bloqueos y disponer de evidencia del proceso de desarrollo.")
    add_table(doc, ["Evento", "Aplicación", "Evidencia"], [
        ("Sprint Planning", "Se seleccionan las historias y se define el objetivo del sprint.", "Sprint Backlog con tareas, dependencias y criterios de aceptación."),
        ("Daily Scrum", "Seguimiento breve: realizado, siguiente actividad y bloqueo técnico.", "Bitácora de avances, incidencias y acuerdos."),
        ("Sprint Review", "Se demuestra el endpoint mediante solicitudes válidas e inválidas.", "Capturas de respuestas JSON, prueba ejecutada y criterios aceptados."),
        ("Retrospectiva", "Se identifica una mejora de proceso para la siguiente iteración.", "Acción concreta: mejorar una validación, prueba o manejo de error."),
        ("Refinamiento", "Se aclaran historias pendientes y se dividen tareas grandes.", "Backlog actualizado y priorizado."),
    ], [3.2, 7.0, 6.1])
    heading(doc, "8 Definition of Done")
    paragraph(doc, "Una historia se considera terminada cuando cumple sus criterios funcionales y técnicos. La interfaz o la ruta aislada no son suficientes: el incremento debe poder ejecutarse, validar los datos y producir una respuesta coherente.")
    bullet(doc, "La ruta y el controlador están implementados y devuelven códigos HTTP acordes con el resultado.")
    bullet(doc, "La solicitud se valida en Laravel antes de procesar o persistir información.")
    bullet(doc, "Las relaciones y registros se guardan de forma consistente; para diagnósticos se emplea una transacción de base de datos.")
    bullet(doc, "Los flujos protegidos requieren autenticación mediante Sanctum.")
    bullet(doc, "La comunicación con Python devuelve una salida JSON válida o genera un error controlado.")
    bullet(doc, "Existe evidencia de prueba del caso principal y, cuando corresponde, de datos incompletos o fuera de rango.")
    bullet(doc, "La historia, sus decisiones y pendientes relevantes se registran en el backlog o la bitácora del sprint.")

    doc.add_page_break()
    heading(doc, "9 Pruebas, calidad y trazabilidad")
    paragraph(doc, "El control de calidad se incorporó dentro de los sprints. Las pruebas feature existentes validan el formulario del diagnóstico mínimo, la ejecución autenticada, el almacenamiento de diagnóstico y detalles, y la consulta posterior por listado y detalle. Esta evidencia verifica tanto el contrato de la API como la persistencia de la información.")
    add_table(doc, ["Aspecto", "Verificación aplicada"], [
        ("Autenticación", "El login verifica credenciales y emite un token Bearer para acceder a rutas protegidas."),
        ("Validación", "Se controlan IDs existentes, campos obligatorios, fechas válidas y rangos de respuesta: 1 a 5 en prueba mínima y 0 a 3 en ADHD."),
        ("Integridad", "Los diagnósticos, pruebas y detalles se registran dentro de una transacción de base de datos."),
        ("Consulta", "Las respuestas de listado y detalle cargan paciente, usuario, prueba y detalles requeridos."),
        ("Modelos", "El entrenamiento conserva los artefactos y las métricas; el ejecutor comprueba que el archivo contenga un clasificador compatible."),
        ("Uso responsable", "El mensaje de salida indica que el resultado es tamizaje y requiere interpretación profesional."),
    ], [4.0, 12.3])
    heading(doc, "10 Integración de Scrum con el componente de aprendizaje automático")
    paragraph(doc, "Scrum organiza el desarrollo e integración del producto de software. El entrenamiento y evaluación de los modelos se realizan mediante scripts de Python, con generación de métricas, curvas y archivos de modelo. Estas actividades se incorporan al Sprint Backlog cuando habilitan un incremento del backend, por ejemplo, cuando el endpoint ADHD debe ejecutar el modelo y registrar el resultado.")
    paragraph(doc, "Los modelos disponibles incluyen Random Forest, SVM y regresión logística. El script de ejecución utiliza por defecto Random Forest y adicionalmente calcula los umbrales de inatención e hiperactividad/impulsividad. Esta doble comprobación se comunica como apoyo técnico y no como diagnóstico clínico.")
    heading(doc, "11 Conclusión metodológica")
    paragraph(doc, "La aplicación de Scrum permitió estructurar el backend en incrementos funcionales: base de datos, autenticación, catálogos, diagnóstico mínimo, tamizaje ADHD, persistencia, consulta y pruebas. Cada incremento se puede demostrar mediante la API y se vincula con una necesidad del Product Backlog. La metodología mantiene la trazabilidad entre requisito, implementación, prueba y mejora, lo que aporta evidencia técnica para el desarrollo del proyecto.")
    paragraph(doc, "Consideración ética. El sistema procesa resultados de apoyo al tamizaje y no debe emplearse como herramienta de diagnóstico ni como reemplazo de la evaluación por profesionales competentes.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.core_properties.title = "Metodología de desarrollo Scrum aplicada al backend de tamizaje ADHD"
    doc.core_properties.subject = "Metodología de desarrollo de software"
    doc.core_properties.author = "Proyecto de diagnóstico"
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
