$ErrorActionPreference = 'Stop'

$out = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\documentos\metodologia_scrum_app_adhd.docx'))
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Add()
$selection = $word.Selection

$normal = -1; $title = -63; $h1 = -2; $h2 = -3; $pageBreak = 7; $center = 1
$doc.PageSetup.TopMargin = $word.CentimetersToPoints(2.5)
$doc.PageSetup.BottomMargin = $word.CentimetersToPoints(2.5)
$doc.PageSetup.LeftMargin = $word.CentimetersToPoints(2.5)
$doc.PageSetup.RightMargin = $word.CentimetersToPoints(2.5)
$doc.Styles.Item($normal).Font.Name = 'Calibri'; $doc.Styles.Item($normal).Font.Size = 11
$doc.Styles.Item($normal).ParagraphFormat.SpaceAfter = 8
$doc.Styles.Item($h1).Font.Name = 'Calibri'; $doc.Styles.Item($h1).Font.Color = 0
$doc.Styles.Item($h2).Font.Name = 'Calibri'; $doc.Styles.Item($h2).Font.Color = 0

function P([string]$text, [int]$style = -1, [int]$align = 0) {
    $selection.Style = $style; $selection.ParagraphFormat.Alignment = $align
    $selection.TypeText($text); $selection.TypeParagraph()
}
function T([string[]]$headers, [object[]]$rows) {
    $table = $doc.Tables.Add($selection.Range, $rows.Count + 1, $headers.Count)
    $table.Borders.Enable = 1; $table.Rows.Item(1).Range.Font.Bold = 1
    $table.Rows.Item(1).Shading.BackgroundPatternColor = 14277081
    for ($c = 1; $c -le $headers.Count; $c++) { $table.Cell(1,$c).Range.Text = $headers[$c-1] }
    for ($r = 0; $r -lt $rows.Count; $r++) {
        for ($c = 0; $c -lt $headers.Count; $c++) { $table.Cell($r+2,$c+1).Range.Text = [string]$rows[$r][$c] }
    }
    $selection.SetRange($table.Range.End, $table.Range.End); $selection.TypeParagraph()
}
function PB { $selection.InsertBreak($pageBreak) }

# Página 1
P 'Metodología Scrum para el desarrollo de la aplicación móvil de tamizaje ADHD Rating Scale IV' $title $center
P 'Documento metodológico de gestión ágil para tesis' $normal $center
P '1. Propósito de la metodología' $h1
P 'Scrum se adopta como marco de gestión ágil para planificar, construir, revisar y mejorar una aplicación móvil de apoyo al tamizaje ADHD Rating Scale IV. El producto integra un frontend en React Native y un backend basado en Laravel 12 con PHP 8.2, API REST y autenticación mediante Laravel Sanctum. La metodología organiza el trabajo en iteraciones cortas con entregables verificables.'
P 'El uso de Scrum complementa CRISP-DM. Scrum gobierna la construcción del producto de software, la priorización de requisitos, la coordinación del equipo y las entregas incrementales. CRISP-DM, en cambio, guía exclusivamente el ciclo de vida de los modelos de machine learning: comprensión de datos, preparación, modelado, evaluación y despliegue. En la tesis se utilizarán ambos marcos de forma articulada.'
P 'La aplicación tiene como finalidad técnica registrar respuestas de la escala, enviar datos al backend, ejecutar el flujo de clasificación y presentar un resultado de apoyo al tamizaje. No reemplaza una valoración profesional ni genera diagnósticos clínicos.'
P '2. Objetivo de Scrum en la tesis' $h1
P 'Desarrollar un incremento funcional de la aplicación al finalizar cada sprint, validarlo con criterios de aceptación y conservar evidencia de las decisiones, pruebas y mejoras realizadas.'
PB

# Página 2
P '3. Fundamentos de Scrum aplicados al proyecto' $h1
P 'Scrum divide el trabajo en sprints con duración fija. Cada sprint inicia con una planificación, continúa con el desarrollo y seguimiento diario, finaliza con una revisión del incremento y concluye con una retrospectiva para mejorar el proceso. Para esta tesis se propone una duración de dos semanas por sprint, ajustable al calendario académico.'
T @('Elemento','Aplicación en la tesis') @(
    @('Producto','Aplicación móvil React Native conectada a API Laravel y módulo de clasificación.'),
    @('Sprint','Iteración de dos semanas con un objetivo, tareas y evidencia de cierre.'),
    @('Incremento','Funcionalidad integrada, probada y demostrable al finalizar el sprint.'),
    @('Product Backlog','Lista priorizada de requisitos funcionales, técnicos y de calidad.'),
    @('Sprint Backlog','Historias y tareas seleccionadas para la iteración actual.'),
    @('Definition of Done','Criterios mínimos para aceptar una historia como terminada.')
)
P 'La planificación será guiada por valor académico y funcional. Se priorizarán primero las funciones necesarias para demostrar el flujo completo: autenticación, registro de respuestas, comunicación móvil-servidor, clasificación y visualización responsable del resultado. Las funciones accesorias se programarán después de contar con un flujo principal verificable.'
P 'La trazabilidad se mantendrá mediante un tablero de tareas, actas breves de revisión y una relación entre cada historia de usuario, su evidencia de prueba y el commit o versión entregada.'
PB

# Página 3
P '4. Roles Scrum' $h1
P 'En un proyecto de tesis una misma persona puede asumir más de un rol, pero las responsabilidades deben mantenerse separadas conceptualmente. Esta separación permite justificar decisiones de priorización, implementación y control de calidad.'
T @('Rol','Responsabilidad aplicada') @(
    @('Product Owner','Representar las necesidades del usuario, priorizar el Product Backlog y aceptar las historias terminadas. Puede ser asumido por el tesista con validación del asesor.'),
    @('Scrum Master','Facilitar ceremonias, proteger el objetivo del sprint, retirar impedimentos y promover la mejora continua.'),
    @('Equipo de desarrollo','Diseñar, programar, probar e integrar el frontend React Native, backend Laravel, base de datos y módulo de machine learning.'),
    @('Asesor de tesis','Revisar el avance metodológico, la evidencia y la coherencia con los objetivos de investigación.'),
    @('Especialista o usuario validador','Aportar retroalimentación sobre comprensión del flujo y lenguaje de la interfaz, sin delegar en la aplicación decisiones clínicas.')
)
P 'Para evitar conflictos, el Product Owner valida que una historia responde a la necesidad definida; el equipo de desarrollo valida que cumple los criterios técnicos; y el asesor revisa que la evidencia sea suficiente para la tesis. Los cambios solicitados después de iniciar un sprint retornan al Product Backlog, salvo correcciones críticas.'
PB

# Página 4
P '5. Arquitectura y Product Backlog inicial' $h1
P 'La arquitectura sigue una separación cliente-servidor. React Native implementa la experiencia móvil; Laravel expone los servicios REST, controla autenticación y reglas de negocio; el módulo de machine learning procesa los 18 ítems y retorna una clasificación o probabilidad de apoyo. La información viaja únicamente por endpoints definidos y validados.'
T @('Capa','Tecnología','Responsabilidad') @(
    @('Cliente móvil','React Native','Pantallas, formularios, validación inicial y presentación de resultados.'),
    @('Servicios','Laravel 12 y PHP 8.2','API REST, autenticación con Sanctum, reglas de negocio y persistencia.'),
    @('Clasificación','Modelos Random Forest, SVM y regresión logística','Procesamiento técnico de las respuestas de la escala.'),
    @('Datos','Base de datos del proyecto','Usuarios autorizados, respuestas, auditoría y configuración.')
)
P 'El Product Backlog se redacta como historias de usuario. Cada historia contiene una prioridad, criterios de aceptación, estimación y dependencias. Se evitarán historias demasiado grandes; si una no puede completarse en un sprint, se divide en tareas más pequeñas y demostrables.'
T @('Prioridad','Historia de usuario resumida','Criterio de aceptación') @(
    @('Alta','Como usuario autorizado, deseo iniciar sesión para acceder al sistema.','La API valida credenciales y el móvil administra sesión segura.'),
    @('Alta','Como docente, deseo registrar los 18 ítems de la escala.','No permite valores fuera de 0 a 3 ni formularios incompletos.'),
    @('Alta','Como usuario, deseo enviar el formulario para obtener un resultado de apoyo.','La API recibe, valida y responde sin exponer errores internos.'),
    @('Media','Como usuario, deseo consultar resultados registrados.','Se muestran solo datos autorizados y con aviso de uso responsable.')
)
PB

# Página 5
P '6. Plan de sprints' $h1
P 'El siguiente plan propone cinco sprints de dos semanas. Puede ajustarse al cronograma de la tesis, pero cada cierre debe conservar el objetivo, las historias terminadas, las pruebas realizadas y los cambios pendientes. Los resultados de los sprints se constituyen como evidencia del proceso de desarrollo.'
T @('Sprint','Objetivo','Incremento verificable') @(
    @('Sprint 0','Definir alcance, arquitectura, herramientas y backlog.','Repositorio estructurado, tablero creado y criterios de aceptación aprobados.'),
    @('Sprint 1','Construir navegación, acceso y estructura inicial del frontend.','Aplicación React Native con pantallas base y flujo de autenticación.'),
    @('Sprint 2','Implementar backend y comunicación segura con el móvil.','API Laravel, endpoints documentados y autenticación Sanctum funcional.'),
    @('Sprint 3','Integrar cuestionario, validaciones y clasificación.','Registro de 18 ítems y respuesta controlada del módulo de ML.'),
    @('Sprint 4','Realizar pruebas, mejora de interfaz y documentación.','Incremento final demostrado, resultados de pruebas y manual técnico.')
)
P 'Cada Sprint Backlog se seleccionará de acuerdo con la capacidad disponible. Una tarea solo se incluirá si tiene criterio de aceptación claro. Las tareas técnicas, tales como migraciones, control de errores, pruebas de endpoints y revisión de seguridad, se planifican junto con las funciones visibles para no postergar la calidad al final del proyecto.'
PB

# Página 6
P '7. Eventos Scrum y evidencia de la tesis' $h1
T @('Evento','Aplicación','Evidencia sugerida') @(
    @('Sprint Planning','Seleccionar historias, definir objetivo y descomponer tareas.','Sprint Backlog, estimaciones y objetivo del sprint.'),
    @('Daily Scrum','Seguimiento breve de avances, bloqueos y próximo trabajo.','Registro conciso de impedimentos y acuerdos.'),
    @('Sprint Review','Demostrar el incremento ante asesor o usuario validador.','Capturas, acta de revisión y criterios aceptados o pendientes.'),
    @('Sprint Retrospective','Analizar qué funcionó, qué debe cambiar y una mejora concreta.','Lista de acciones de mejora para el siguiente sprint.'),
    @('Refinamiento','Aclarar, dividir y priorizar historias futuras.','Product Backlog actualizado y con criterios de aceptación.')
)
P 'La revisión no debe limitarse a una presentación visual. Se debe ejecutar el flujo acordado: inicio de sesión, ingreso de respuestas, validación de rangos, envío al backend y presentación del resultado. Si el modelo se usa con datos demostrativos, esa condición debe aparecer de manera visible durante la demostración.'
P 'Las retrospectivas son importantes para una tesis individual porque permiten registrar mejoras reales del proceso: por ejemplo, dividir una historia demasiado grande, añadir validaciones antes del envío o automatizar pruebas de un endpoint. Estas decisiones sustentan la aplicación práctica de Scrum.'
PB

# Página 7
P '8. Calidad, seguridad y Definition of Done' $h1
P 'La Definition of Done define las condiciones mínimas para declarar terminada una historia de usuario. El objetivo es evitar que una funcionalidad se considere completada solo porque su interfaz es visible. Una historia terminada debe estar integrada, validada y documentada en el nivel correspondiente.'
T @('Criterio','Condición de terminado') @(
    @('Funcionalidad','Cumple los criterios de aceptación definidos para la historia.'),
    @('Frontend','La pantalla React Native valida entradas, muestra mensajes comprensibles y no presenta errores bloqueantes.'),
    @('Backend','El endpoint Laravel valida solicitudes, responde con códigos adecuados y controla errores esperados.'),
    @('Seguridad','El acceso requiere autenticación cuando corresponde y no expone datos sensibles en mensajes o registros.'),
    @('Pruebas','Existe evidencia de prueba manual o automatizada para el flujo principal y casos inválidos.'),
    @('Documentación','Se actualizan API, instrucciones de uso o bitácora del sprint cuando el cambio lo requiere.')
)
P 'Las pruebas incluirán validación de campos, respuestas incompletas, valores fuera de rango, errores de autenticación y comunicación entre móvil y API. En el componente de machine learning se verificará que las 18 respuestas lleguen en el orden definido y que el mensaje mostrado sea coherente con su carácter de apoyo al tamizaje.'
PB

# Página 8
P '9. Integración de Scrum y CRISP-DM' $h1
P 'Scrum y CRISP-DM se usarán de forma complementaria. Scrum responde cómo se organiza y entrega el producto de software; CRISP-DM responde cómo se construye y evalúa el componente de datos y aprendizaje automático. Un sprint puede contener actividades de CRISP-DM, pero el cierre del sprint exige además una integración demostrable en la aplicación.'
T @('Actividad','Marco principal','Resultado') @(
    @('Priorizar el formulario y los endpoints','Scrum','Historias de usuario y Sprint Backlog.'),
    @('Revisar calidad de las respuestas y etiquetas','CRISP-DM','Datos preparados y limitaciones documentadas.'),
    @('Entrenar y comparar modelos','CRISP-DM','Métricas, gráficos y modelos versionados.'),
    @('Integrar la clasificación en la API y la app','Scrum + CRISP-DM','Incremento funcional y evidencia de prueba.'),
    @('Recoger retroalimentación y ajustar','Scrum','Backlog refinado y acciones de mejora.')
)
P '10. Conclusión metodológica' $h1
P 'La aplicación se desarrollará mediante Scrum en sprints de dos semanas, con Product Backlog priorizado, incrementos verificables y evidencia de revisión. CRISP-DM se mantendrá como metodología específica del componente de machine learning. Esta combinación permite sustentar tanto el desarrollo de la app React Native y Laravel como el tratamiento responsable de los modelos de clasificación.'
P 'Nota ética: el resultado de la aplicación constituye apoyo técnico al tamizaje. No debe utilizarse como diagnóstico, ni reemplaza la evaluación profesional o las políticas institucionales de protección de datos.'

$doc.SaveAs([ref]$out, [ref]16)
$doc.Close(); $word.Quit()
Write-Output $out
