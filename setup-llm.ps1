# Quick Setup Check for LLM Integration

Write-Host "Rainly - LLM Integration Setup (Gemma 270M)" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Check if models directory exists
Write-Host "Checking directory structure..." -ForegroundColor Yellow
$modelsDir = "backend\models\llm"
if (!(Test-Path $modelsDir)) {
    New-Item -ItemType Directory -Force -Path $modelsDir | Out-Null
    Write-Host "[OK] Created: $modelsDir" -ForegroundColor Green
} else {
    Write-Host "[OK] Directory exists: $modelsDir" -ForegroundColor Green
}

Write-Host ""

# Check if model is downloaded
Write-Host "Checking for Gemma model..." -ForegroundColor Yellow
$modelPath = "$modelsDir\gemma-3-270m-it"
if (!(Test-Path $modelPath)) {
    Write-Host "[X] Model NOT found" -ForegroundColor Red
    Write-Host ""
    Write-Host "DOWNLOAD INSTRUCTIONS:" -ForegroundColor Cyan
    Write-Host "Place your Gemma 270M model files in:" -ForegroundColor White
    Write-Host "  $modelPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "If using Git LFS:" -ForegroundColor White
    Write-Host "  cd $modelsDir" -ForegroundColor Gray
    Write-Host "  git clone https://huggingface.co/google/gemma-3-270m-it" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Required files:" -ForegroundColor White
    Write-Host "  - config.json" -ForegroundColor Gray
    Write-Host "  - tokenizer.json / tokenizer.model" -ForegroundColor Gray
    Write-Host "  - model.safetensors (or .bin files)" -ForegroundColor Gray
} else {
    Write-Host "[OK] Model found: $modelPath" -ForegroundColor Green
    
    # Check for key files
    $configExists = Test-Path "$modelPath\config.json"
    $tokenizerExists = (Test-Path "$modelPath\tokenizer.json") -or (Test-Path "$modelPath\tokenizer.model")
    $modelExists = (Test-Path "$modelPath\*.safetensors") -or (Test-Path "$modelPath\*.bin")
    
    Write-Host ""
    Write-Host "File Check:" -ForegroundColor Yellow
    if ($configExists) { Write-Host "  [OK] config.json" -ForegroundColor Green } else { Write-Host "  [X] config.json missing" -ForegroundColor Red }
    if ($tokenizerExists) { Write-Host "  [OK] tokenizer files" -ForegroundColor Green } else { Write-Host "  [X] tokenizer missing" -ForegroundColor Red }
    if ($modelExists) { Write-Host "  [OK] model weights" -ForegroundColor Green } else { Write-Host "  [X] model weights missing" -ForegroundColor Red }
    
    Write-Host ""
    
    if ($configExists -and $tokenizerExists -and $modelExists) {
        # Check dependencies
        Write-Host "Checking Python dependencies..." -ForegroundColor Yellow
        $depsCheck = python -c "import transformers; import torch; print('OK')" 2>&1
        
        if ($depsCheck -like "*OK*") {
            Write-Host "[OK] Dependencies installed" -ForegroundColor Green
            Write-Host ""
            Write-Host "=====================================" -ForegroundColor Green
            Write-Host "  ALL READY! LLM is configured!" -ForegroundColor Green
            Write-Host "=====================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "Next steps:" -ForegroundColor Cyan
            Write-Host "1. Restart backend: uvicorn main:app --reload" -ForegroundColor White
            Write-Host "2. Test with simulator at http://localhost:3000/simulator" -ForegroundColor White
        } else {
            Write-Host "[X] Dependencies NOT installed" -ForegroundColor Red
            Write-Host ""
            Write-Host "Install with:" -ForegroundColor White
            Write-Host "  pip install -r backend\requirements-llm.txt" -ForegroundColor Gray
        }
    } else {
        Write-Host "[!] Model folder exists but some files are missing" -ForegroundColor Yellow
        Write-Host "    Make sure all model files are downloaded" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Model: Gemma 270M" -ForegroundColor White
Write-Host "  Path: backend\models\llm\gemma-3-270m-it" -ForegroundColor White
Write-Host "  Enabled: Yes (in .env)" -ForegroundColor White
Write-Host ""
