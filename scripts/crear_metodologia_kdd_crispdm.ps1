$ErrorActionPreference = 'Stop'

$out = Join-Path $PSScriptRoot '..\documentos\metodologia_kdd_crisp_dm_adhd.docx'
$out = [IO.Path]::GetFullPath($out)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Add()
$selection = $word.Selection

# Constantes de Word.
$wdStyleNormal = -1; $wdStyleTitle = -63; $wdStyleHeading1 = -2; $wdStyleHeading2 = -3
$wdPageBreak = 7; $wdCollapseEnd = 0; $wdAlignCenter = 1; $wdAlignLeft = 0

$doc.PageSetup.TopMargin = $word.CentimetersToPoints(2.5)
$doc.PageSetup.BottomMargin = $word.CentimetersToPoints(2.5)
$doc.PageSetup.LeftMargin = $word.CentimetersToPoints(2.5)
$doc.PageSetup.RightMargin = $word.CentimetersToPoints(2.5)
$doc.Styles.Item($wdStyleNormal).Font.Name = 'Calibri'
$doc.Styles.Item($wdStyleNormal).Font.Size = 11
$doc.Styles.Item($wdStyleNormal).ParagraphFormat.SpaceAfter = 8
$doc.Styles.Item($wdStyleNormal).ParagraphFormat.LineSpacingRule = 0
$doc.Styles.Item($wdStyleHeading1).Font.Name = 'Calibri'
$doc.Styles.Item($wdStyleHeading1).Font.Color = 0
$doc.Styles.Item($wdStyleHeading2).Font.Name = 'Calibri'
$doc.Styles.Item($wdStyleHeading2).Font.Color = 0

function Add-Paragraph([string]$Text, [int]$Style = -1, [int]$Alignment = 0) {
    $selection.Style = $Style
    $selection.ParagraphFormat.Alignment = $Alignment
    $selection.TypeText($Text)
    $selection.TypeParagraph()
}

function Add-Table([string[]]$Headers, [object[]]$Rows) {
    $table = $doc.Tables.Add($selection.Range, $Rows.Count + 1, $Headers.Count)
    $table.Borders.Enable = 1
    $table.Rows.Item(1).Range.Font.Bold = 1
    $table.Rows.Item(1).Shading.BackgroundPatternColor = 14277081
    for ($c = 1; $c -le $Headers.Count; $c++) { $table.Cell(1, $c).Range.Text = $Headers[$c - 1] }
    for ($r = 0; $r -lt $Rows.Count; $r++) {
        for ($c = 0; $c -lt $Headers.Count; $c++) { $table.Cell($r + 2, $c + 1).Range.Text = [string]$Rows[$r][$c] }
    }
    $selection.SetRange($table.Range.End, $table.Range.End)
    $selection.TypeParagraph()
}

function New-Page { $selection.InsertBreak($wdPageBreak) }

# Página 1
Add-Paragraph 'Metodología KDD y CRISP DM para el proyecto de tamizaje ADHD Rating Scale IV' $wdStyleTitle $wdAlignCenter
Add-Paragraph 'Documento metodológico para el desarrollo y evaluación de modelos SVM, regresión logística y Random Forest' $wdStyleNormal $wdAlignCenter
Add-Paragraph '1. Propósito y alcance' $wdStyleHeading1
Add-Paragraph 'Este documento define la metodología para construir, evaluar y documentar modelos de clasificación que apoyen el tamizaje con ADHD Rating Scale IV, versión para profesores. El sistema procesa las respuestas de 18 ítems, codificadas de 0 a 3, y estima la probabilidad de un tamizaje positivo. Su propósito es técnico y exploratorio: no reemplaza una evaluación clínica ni emite un diagnóstico.'
Add-Paragraph 'Se utilizarán dos marcos complementarios. KDD organiza el descubrimiento de conocimiento desde la selección y transformación de los datos hasta la interpretación de los patrones. CRISP-DM ofrece un ciclo de trabajo para gestionar el problema, preparar los datos, modelar, evaluar y planificar el despliegue. La combinación permite mantener trazabilidad entre la necesidad educativa, las decisiones analíticas y las limitaciones del resultado.'
Add-Paragraph 'La muestra de trabajo contiene 30 registros. Mientras no se disponga de respuestas reales y etiquetas profesionales verificadas, los resultados deben identificarse expresamente como demostrativos. Las métricas obtenidas validan el funcionamiento del flujo de machine learning y no la utilidad clínica del modelo.'
Add-Paragraph '2. Pregunta de trabajo' $wdStyleHeading1
Add-Paragraph '¿Cómo puede construirse un flujo reproducible y responsable para clasificar un tamizaje positivo o negativo a partir de los 18 ítems de la escala, comparando Random Forest, SVM y regresión logística, sin atribuir valor diagnóstico a resultados entrenados con datos sintéticos?' 
New-Page

# Página 2
Add-Paragraph '3. Marco KDD' $wdStyleHeading1
Add-Paragraph 'KDD, Knowledge Discovery in Databases, entiende el modelado como una secuencia de decisiones que transforma datos en conocimiento útil. En este proyecto, el conocimiento esperado no es una conclusión clínica, sino evidencia técnica sobre el comportamiento de los algoritmos y las condiciones necesarias para una futura validación con datos reales.'
Add-Table @('Etapa KDD','Aplicación en el proyecto','Producto esperado') @(
    @('Selección','Definir registros, variables y criterio de inclusión.','Matriz de 30 registros con 18 ítems y etiqueta.'),
    @('Preprocesamiento','Verificar completitud, rangos y consistencia.','Datos sin valores inválidos ni columnas faltantes.'),
    @('Transformación','Convertir respuestas en matriz numérica y normalizar cuando el modelo lo requiere.','Variables aptas para SVM y regresión logística.'),
    @('Minería de datos','Entrenar Random Forest, SVM y regresión logística.','Modelos reproducibles con semilla fija.'),
    @('Interpretación','Comparar métricas, errores y limitaciones.','Informe técnico sin afirmaciones diagnósticas.')
)
Add-Paragraph 'Cada etapa debe conservar evidencia de entrada, decisión y salida. Por ejemplo, si se generan datos sintéticos porque el archivo está vacío, esa condición se registra antes del entrenamiento y se repite en el informe de resultados. Así se evita que una métrica aparentemente alta se interprete como evidencia obtenida con población escolar real.'
Add-Paragraph '3.1 Criterio de calidad' $wdStyleHeading2
Add-Paragraph 'La calidad se revisará en tres niveles: calidad de datos, calidad predictiva y calidad de comunicación. Un flujo correcto requiere que los 18 ítems estén completos, que las etiquetas contengan ambas clases y que las métricas se presenten junto con tamaño de muestra, matriz de confusión y advertencias de uso.'
New-Page

# Página 3
Add-Paragraph '4. KDD Etapa 1 Selección de datos' $wdStyleHeading1
Add-Paragraph 'La unidad de análisis es un registro de la escala ADHD Rating Scale IV completada por un profesor. Cada registro incluye item_1 a item_18 y la variable objetivo tamizaje_positivo. Los ítems representan respuestas ordinales entre 0 y 3. La etiqueta objetivo utiliza 0 para tamizaje negativo y 1 para tamizaje positivo.'
Add-Table @('Elemento','Regla metodológica') @(
    @('Tamaño de muestra','Se requieren exactamente 30 registros para el flujo actual.'),
    @('Variables predictoras','18 ítems, todos con valores enteros de 0 a 3.'),
    @('Variable objetivo','tamizaje_positivo, con valores 0 o 1.'),
    @('Inclusión','Registro con los 18 ítems y la etiqueta completos.'),
    @('Exclusión','Fila incompleta, valor fuera de rango o etiqueta no válida.'),
    @('Trazabilidad','Registrar origen, fecha de corte y condición real o sintética.')
)
Add-Paragraph 'La selección deberá respetar confidencialidad y minimización de datos. No se incorporarán nombres, documentos de identidad, direcciones ni otros identificadores personales en el archivo de entrenamiento. Si en el futuro se recolectan datos reales, las etiquetas deberán provenir de un procedimiento profesional definido y documentado.'
Add-Paragraph 'El archivo de datos debe conservar un diccionario de variables. Este diccionario describe el significado de cada ítem, el rango permitido, el responsable de la carga y la versión de la escala. Mantenerlo evita cambios silenciosos en las columnas que puedan alterar el comportamiento del modelo.'
New-Page

# Página 4
Add-Paragraph '5. KDD Etapas 2 y 3 Preprocesamiento y transformación' $wdStyleHeading1
Add-Paragraph 'Antes de entrenar, el proceso verifica que existan las 19 columnas esperadas y que cada una de las 30 filas sea válida. Las respuestas se convierten a valores numéricos enteros. También se comprueba que existan al menos dos ejemplos de cada clase; de lo contrario no es posible realizar una partición estratificada ni estimar métricas de clasificación de forma útil.'
Add-Paragraph 'La división de evaluación utiliza 80 por ciento de los registros para entrenamiento, equivalente a 24 casos, y 20 por ciento para prueba, equivalente a 6 casos. La semilla aleatoria 42 permite repetir la partición y contrastar los resultados entre modelos en las mismas condiciones.'
Add-Table @('Modelo','Transformación aplicada','Justificación') @(
    @('Random Forest','Matriz numérica original.','Los árboles no necesitan escalamiento de las variables.'),
    @('SVM','Estandarización con StandardScaler.','Evita que la escala de las variables afecte la distancia del kernel.'),
    @('Regresión logística','Estandarización con StandardScaler.','Facilita el ajuste numérico y la comparación de coeficientes.'),
    @('Todos','Partición estratificada y semilla 42.','Mantiene proporción de clases y reproducibilidad.')
)
Add-Paragraph 'Cuando el archivo se encuentre vacío, el código genera datos sintéticos deterministas para comprobar la ejecución. Esta alternativa no debe mezclarse con datos reales ni utilizarse para decisiones sobre estudiantes. Los archivos, gráficos y modelos resultantes deben etiquetarse como demostración.'
New-Page

# Página 5
Add-Paragraph '6. Marco CRISP DM' $wdStyleHeading1
Add-Paragraph 'CRISP-DM, Cross Industry Standard Process for Data Mining, convierte la metodología analítica en un ciclo de gestión del proyecto. Aunque se originó en problemas de negocio, en este caso se adapta al contexto educativo como un proceso de apoyo técnico, con restricciones éticas y de validación más exigentes.'
Add-Table @('Fase CRISP-DM','Decisión aplicada al proyecto') @(
    @('Comprensión del problema','Definir el apoyo al tamizaje y prohibir la interpretación diagnóstica.'),
    @('Comprensión de los datos','Revisar estructura, cantidad de registros, distribución de clases y origen.'),
    @('Preparación de los datos','Validar rangos, completitud, codificación y partición estratificada.'),
    @('Modelado','Entrenar tres clasificadores con parámetros documentados.'),
    @('Evaluación','Analizar métricas, matriz de confusión, curvas y validación cruzada.'),
    @('Despliegue','Integrar solo con controles, documentación y revisión profesional.')
)
Add-Paragraph 'El carácter cíclico de CRISP-DM es especialmente importante en una muestra pequeña. Si la evaluación muestra sensibilidad insuficiente, no se debe avanzar directamente al despliegue: se vuelve a las fases de comprensión de datos, preparación y modelado para revisar calidad de etiquetas, tamaño muestral, umbral de decisión y criterios de inclusión.'
New-Page

# Página 6
Add-Paragraph '7. CRISP-DM Comprensión, preparación y modelado' $wdStyleHeading1
Add-Paragraph 'En la comprensión del problema, el criterio de éxito no se limita a accuracy. En un tamizaje interesa conocer cuántos positivos se identifican, cuántos se omiten y cuántas alertas resultan incorrectas. Por ello se evaluarán sensibilidad, especificidad, precisión, F1, ROC AUC y PR AUC, junto con la matriz de confusión.'
Add-Paragraph 'En la preparación, se documentarán valores faltantes, duplicados, distribución de clases y cualquier regla usada para generar o corregir etiquetas. No se debe imputar ni alterar una respuesta clínica sin una política aprobada. Los cambios sobre los datos se registran en una bitácora reproducible.'
Add-Paragraph 'El modelado compara tres alternativas. Random Forest usa 300 árboles, ponderación balanceada de clases y semilla 42. SVM usa kernel RBF, escalamiento y calibración de probabilidades. La regresión logística usa escalamiento, ponderación balanceada y un máximo de 1000 iteraciones. Los parámetros se conservan en el código para que una ejecución posterior pueda repetirse.'
Add-Paragraph 'Las probabilidades se usan para explorar el comportamiento de cada modelo, no para declarar un nivel de riesgo clínico. Si se considera modificar el umbral de 0.5, el cambio debe justificarse con datos reales, un objetivo explícito de sensibilidad o especificidad y evaluación independiente.'
New-Page

# Página 7
Add-Paragraph '8. CRISP-DM Evaluación y despliegue responsable' $wdStyleHeading1
Add-Paragraph 'La evaluación se realiza primero sobre los seis casos reservados para prueba y después mediante validación cruzada estratificada sobre el conjunto de entrenamiento. Dado el tamaño reducido, ambas evaluaciones son inestables y se reportan como evidencia exploratoria. Ninguna métrica aislada debe utilizarse para elegir un modelo.'
Add-Table @('Evidencia','Uso correcto','Límite') @(
    @('Accuracy y balanced accuracy','Resumen del acierto global y por clase.','Pueden ocultar fallos de sensibilidad.'),
    @('Matriz de confusión','Identificar verdaderos y falsos positivos o negativos.','Depende de pocos casos en la muestra actual.'),
    @('ROC AUC y PR AUC','Explorar ordenación de probabilidades.','No garantizan desempeño con un umbral concreto.'),
    @('Calibración','Revisar relación entre probabilidad y frecuencia observada.','No es estable con seis casos de prueba.'),
    @('Importancia o coeficientes','Explorar la contribución técnica de ítems.','No representa relevancia clínica.')
)
Add-Paragraph 'El despliegue solo será considerado cuando existan datos reales, consentimiento y gobernanza definida, etiquetas validadas, evaluación externa y revisión por especialistas. La interfaz debe mostrar que el resultado es un apoyo de tamizaje, conservar auditoría de versión del modelo y permitir la revisión humana de cada caso.'
New-Page

# Página 8
Add-Paragraph '9. Integración de KDD y CRISP-DM y plan de trabajo' $wdStyleHeading1
Add-Paragraph 'KDD aporta profundidad analítica sobre los datos y los patrones; CRISP-DM aporta control de proyecto y decisiones de ciclo de vida. En conjunto, ambos marcos aseguran que la elección de un algoritmo no se separe de la calidad de los registros, del significado de la etiqueta ni de las condiciones éticas de uso.'
Add-Table @('Hito','Resultado verificable','Responsable sugerido') @(
    @('1. Consolidar datos reales','Archivo anonimizado, completo y con diccionario de variables.','Equipo de recolección y profesional responsable.'),
    @('2. Validar etiquetas','Criterio profesional documentado y trazable.','Especialista designado.'),
    @('3. Reentrenar y comparar','Métricas, gráficos y matriz de confusión actualizados.','Equipo técnico.'),
    @('4. Validación independiente','Prueba en muestra no usada durante el ajuste.','Equipo de evaluación.'),
    @('5. Revisión de uso','Protocolo de apoyo, privacidad y supervisión humana.','Responsables institucionales.')
)
Add-Paragraph '10. Conclusión' $wdStyleHeading1
Add-Paragraph 'La metodología propuesta permite documentar el proyecto de manera ordenada, reproducible y responsable. Con la muestra disponible, los modelos SVM, regresión logística y Random Forest deben presentarse como demostraciones técnicas. La siguiente etapa no es automatizar decisiones, sino recolectar datos reales de calidad, validar las etiquetas y repetir el ciclo KDD y CRISP-DM con supervisión profesional.'
Add-Paragraph 'Nota de uso: este documento describe metodología de ciencia de datos aplicada a un tamizaje. No constituye guía clínica, diagnóstico ni recomendación individual para estudiantes.'

$doc.SaveAs([ref]$out, [ref]16)
$doc.Close()
$word.Quit()
Write-Output $out
