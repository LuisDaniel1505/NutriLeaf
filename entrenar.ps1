# ============================================================
# NutriLeaf — Script para entrenar el modelo en una ventana visible
# Uso: hacer doble clic, o ejecutar:  .\entrenar.ps1
# ============================================================

# Ubica la carpeta del proyecto (independientemente de dónde se invoque)
Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "   NutriLeaf - Entrenamiento del modelo" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""

# Entrena 20 épocas con ResNet18 y guarda el log en train_log.txt
.\venv\Scripts\python.exe -m training.train --arch resnet18 --epochs 20 2>&1 |
    Tee-Object -FilePath train_log.txt

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "   Entrenamiento finalizado" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Presiona cualquier tecla para cerrar esta ventana..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
