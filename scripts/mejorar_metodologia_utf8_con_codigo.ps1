$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$docx = Join-Path $root 'documentos\metodologia_kdd_crisp_dm_adhd.docx'
$assets = Join-Path $root 'documentos\recursos_metodologia'
New-Item -ItemType Directory -Force -Path $assets | Out-Null

function New-CodeImage([string]$Path, [string]$Title, [string[]]$Lines) {
    $font = New-Object System.Drawing.Font('Consolas', 9.0)
    $titleFont = New-Object System.Drawing.Font('Segoe UI Semibold', 9.5)
    $lineHeight = 17
    $width = 1140
    $height = 54 + ($Lines.Count * $lineHeight) + 22
    $bitmap = New-Object System.Drawing.Bitmap($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = 'HighQuality'
    $graphics.Clear([System.Drawing.Color]::FromArgb(15, 23, 42))
    $accent = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(56, 189, 248))
    $text = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(226, 232, 240))
    $muted = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(148, 163, 184))
    $graphics.FillRectangle($accent, 0, 0, $width, 5)
    $graphics.DrawString($Title, $titleFont, $text, 28, 16)
    for ($i = 0; $i -lt $Lines.Count; $i++) {
        $number = ('{0,2}' -f ($i + 1))
        $graphics.DrawString($number, $font, $muted, 28, 52 + ($i * $lineHeight))
        $graphics.DrawString($Lines[$i], $font, $text, 68, 52 + ($i * $lineHeight))
    }
    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose(); $bitmap.Dispose(); $font.Dispose(); $titleFont.Dispose()
}

$validation = Join-Path $assets 'fragmento_validacion_datos.png'
$models = Join-Path $assets 'fragmento_modelos.png'
$metrics = Join-Path $assets 'fragmento_metricas.png'

New-CodeImage $validation 'Fragmento 1  Validación de datos de entrada' @(
    'faltantes = set([*FEATURES, "tamizaje_positivo"]) - set(lector.fieldnames or [])',
    'if faltantes:',
    '    raise ValueError(f"Faltan columnas: {chr(39)}, {chr(39)}.join(sorted(faltantes))}.")',
    'if len(filas) != TOTAL_REGISTROS:',
    '    raise ValueError("Se requieren exactamente 30 registros.")',
    'if any(valor not in (0, 1, 2, 3) for valor in items):',
    '    raise ValueError("Los ítems deben estar entre 0 y 3.")'
)
New-CodeImage $models 'Fragmento 2  Configuración reproducible de modelos' @(
    '"random_forest": RandomForestClassifier(',
    '    n_estimators=300, max_features="sqrt",',
    '    class_weight="balanced", random_state=SEMILLA, n_jobs=1,',
    '),',
    '"svm": Pipeline([("escalador", StandardScaler()),',
    '                 ("clasificador", CalibratedClassifierCV(SVC(kernel="rbf"), cv=3))]),',
    '"regresion_lineal": Pipeline([("escalador", StandardScaler()),',
    '                 ("clasificador", LogisticRegression(max_iter=1000, random_state=SEMILLA))])'
)
New-CodeImage $metrics 'Fragmento 3  Métricas y matriz de confusión' @(
    'prediccion = modelo.predict(x_test)',
    'probabilidad = modelo.predict_proba(x_test)[:, 1]',
    'tn, fp, fn, tp = confusion_matrix(y_test, prediccion, labels=[0, 1]).ravel()',
    'metricas = {',
    '    "Accuracy": accuracy_score(y_test, prediccion),',
    '    "Recall": recall_score(y_test, prediccion, zero_division=0),',
    '    "F1": f1_score(y_test, prediccion, zero_division=0),',
    '    "ROC-AUC": roc_auc_score(y_test, probabilidad),',
    '}'
)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open($docx)
$wdCollapseEnd = 0; $wdAlignCenter = 1

function Insert-CodeBlock([string]$Needle, [string]$Caption, [string]$ImagePath) {
    $range = $doc.Content
    $found = $range.Find.Execute($Needle)
    if (-not $found) { throw "No se encontró el texto de referencia: $Needle" }
    $range.Collapse($wdCollapseEnd)
    $range.InsertAfter("`r")
    $range.Collapse($wdCollapseEnd)
    $shape = $doc.InlineShapes.AddPicture($ImagePath, $false, $true, $range)
    $shape.Width = $word.CentimetersToPoints(14.7)
    $shape.LockAspectRatio = -1
    $range.SetRange($shape.Range.End, $shape.Range.End)
    $range.InsertAfter("`r$Caption`r")
    $captionRange = $doc.Range($shape.Range.End + 1, $shape.Range.End + 1 + $Caption.Length)
    $captionRange.ParagraphFormat.Alignment = $wdAlignCenter
    $captionRange.Font.Italic = 1
    $captionRange.Font.Size = 9
}

Insert-CodeBlock 'Cuando el archivo se encuentre vacío' 'Figura metodológica 1. Validación de estructura y rangos antes del entrenamiento.' $validation
Insert-CodeBlock 'El modelado compara tres alternativas' 'Figura metodológica 2. Parámetros centrales para reproducir el entrenamiento.' $models
Insert-CodeBlock 'La evaluación se realiza primero' 'Figura metodológica 3. Cálculo de predicciones, probabilidades y métricas.' $metrics

# Normaliza el texto de todo el documento para usar Unicode y tipografía legible.
$doc.Content.Font.Name = 'Calibri'
$doc.Content.Font.Size = 11
$doc.Save()
$doc.Close()
$word.Quit()
Write-Output $docx
