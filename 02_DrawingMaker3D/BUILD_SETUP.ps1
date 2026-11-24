$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
Start-Transcript -Path (Join-Path $PSScriptRoot 'build-log.txt') -Force | Out-Null
function Run([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed (exit $LASTEXITCODE)" }
}
function Find-OCR {
    $candidates = @($env:TESSERACT_EXE, (Get-Command tesseract.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source), "$env:ProgramFiles\Tesseract-OCR\tesseract.exe", "${env:ProgramFiles(x86)}\Tesseract-OCR\tesseract.exe", "$env:LOCALAPPDATA\Programs\Tesseract-OCR\tesseract.exe")
    foreach ($p in $candidates) {
        if ($p -and (Test-Path -LiteralPath $p -PathType Leaf)) {
            $dir = Split-Path -Parent $p
            if (Test-Path -LiteralPath (Join-Path $dir 'tessdata\eng.traineddata')) { return $dir }
        }
    }
    return $null
}
function Find-ISCC {
    $candidates = @($env:ISCC_EXE, (Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source))
    foreach ($dir in @($env:ProgramFiles, ${env:ProgramFiles(x86)}, "$env:LOCALAPPDATA\Programs")) {
        if ($dir) { foreach ($v in @('6','7')) { $candidates += (Join-Path $dir "Inno Setup $v\ISCC.exe") } }
    }
    foreach ($p in $candidates) { if ($p -and (Test-Path -LiteralPath $p -PathType Leaf)) { return $p } }
    return $null
}
try {
    Write-Host '[1/6] Preparing Python build environment'
    $python = Join-Path $PSScriptRoot '.buildenv\Scripts\python.exe'
    if (!(Test-Path -LiteralPath $python)) {
        $py = Get-Command py.exe -ErrorAction SilentlyContinue
        if ($py) { Run $py.Source @('-3.12','-m','venv','.buildenv') }
        else {
            $p = Get-Command python.exe -ErrorAction SilentlyContinue
            if (!$p) { throw 'Python 3.12 x64 not found. Run INSTALL_PYTHON.bat and retry.' }
            Run $p.Source @('-m','venv','.buildenv')
        }
    }
    & $python -c 'import sys; sys.exit(int(sys.version_info[:2] != (3,12) or sys.maxsize <= 2**32))'
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 x64 required. Check Python installation and remove .buildenv before retrying.' }
    Run $python @('-m','pip','install','--disable-pip-version-check','-r','requirements.txt','-r','requirements-build.txt','lxml>=5,<7')
    Run $python @('-m','pip','check')
    Run $python @('-c','import lxml.etree; import trimesh.exchange.threemf')
    & $python -m pip freeze | Set-Content -Encoding ASCII 'build-dependencies.txt'
    if ($LASTEXITCODE -ne 0) { throw 'pip freeze failed' }
    Write-Host '[2/6] Preparing Tesseract OCR for offline installation'
    $ocr = Find-OCR
    if (!$ocr) { throw 'Tesseract OCR with English data not found. Run INSTALL_OCR.bat and retry.' }
    $ocrStage = Join-Path $PSScriptRoot 'build-ocr'
    if (Test-Path -LiteralPath $ocrStage) { Remove-Item -LiteralPath $ocrStage -Recurse -Force }
    New-Item -ItemType Directory -Path $ocrStage | Out-Null
    Get-ChildItem -LiteralPath $ocr -Force | Where-Object { $_.Name -notmatch '^(unins|uninstall)' } | Copy-Item -Destination $ocrStage -Recurse -Force
    Run (Join-Path $ocrStage 'tesseract.exe') @('--version')
    Write-Host '[3/6] Building standalone Windows application'
    $iconPath = Join-Path $PSScriptRoot 'DrawingMaker3D.ico'
    $versionPath = Join-Path $PSScriptRoot 'version_info.txt'
    foreach ($asset in @($iconPath, $versionPath)) {
        if (!(Test-Path -LiteralPath $asset -PathType Leaf)) { throw "Required build asset not found: $asset" }
    }
    $argsList = @('-m','PyInstaller','--noconfirm','--clean','--onedir','--windowed','--noupx','--name','DrawingMaker3D','--icon',$iconPath,'--contents-directory','_internal','--version-file',$versionPath,'--distpath',(Join-Path $PSScriptRoot 'dist'),'--workpath',(Join-Path $PSScriptRoot 'build-pyi'),'--specpath',(Join-Path $PSScriptRoot 'build-pyi'),'--paths',$PSScriptRoot)
    foreach ($module in @('trimesh','networkx','pypdfium2','pypdfium2_raw','shapely','lxml')) { $argsList += @('--collect-all',$module) }
    foreach ($module in @('scipy.spatial','scipy.sparse.csgraph','scipy.ndimage','scipy.optimize','matplotlib.backends.backend_tkagg','mpl_toolkits.mplot3d','cv2','PIL.ImageTk','lxml.etree','lxml._elementpath')) { $argsList += @('--hidden-import',$module) }
    foreach ($p in @('numpy','opencv-python-headless','Pillow','pytesseract','pypdfium2','trimesh','matplotlib','scipy','shapely','networkx','lxml')) { $argsList += @('--copy-metadata',$p) }
    Get-ChildItem -File | Where-Object { $_.Extension -in @('.png','.pdf') -and $_.Name -ne 'icon.png' } | ForEach-Object { $argsList += @('--add-data', ($_.FullName + ':.')) }
    $argsList += @('--add-data',((Join-Path $PSScriptRoot 'DrawingMaker3D.ico') + ':.'),'--add-data',($ocrStage + ':tesseract'),'--add-data',((Join-Path $PSScriptRoot 'README_RU.txt') + ':.'),'--add-data',((Join-Path $PSScriptRoot 'build-dependencies.txt') + ':.'),(Join-Path $PSScriptRoot 'windows_launcher.py'))
    Run $python $argsList
    Write-Host '[4/6] Testing the packaged EXE (all sample drawings, both exports)'
    $exe = Join-Path $PSScriptRoot 'dist\DrawingMaker3D\DrawingMaker3D.exe'
    $report = Join-Path $PSScriptRoot 'self-test.txt'
    if (Test-Path -LiteralPath $report) { Remove-Item -LiteralPath $report -Force }
    $process = Start-Process -FilePath $exe -ArgumentList ('--self-test "' + $report + '"') -Wait -PassThru
    if (Test-Path -LiteralPath $report) { Get-Content -LiteralPath $report }
    if ($process.ExitCode -ne 0 -or !(Test-Path -LiteralPath $report) -or !(Select-String -LiteralPath $report -Pattern '^ALL TESTS PASSED$' -Quiet)) { throw 'Packaged EXE self-test failed. See self-test.txt.' }
    Write-Host '[5/6] Finding or installing Inno Setup'
    $iscc = Find-ISCC
    if (!$iscc) {
        $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
        if (!$winget) { throw 'Install Inno Setup 6 from https://jrsoftware.org/isdl.php and run BUILD_SETUP.bat again.' }
        Run $winget.Source @('install','--id','JRSoftware.InnoSetup','--exact','--source','winget','--accept-package-agreements','--accept-source-agreements')
        $iscc = Find-ISCC
        if (!$iscc) { throw 'Inno Setup installed but ISCC.exe not found. Set ISCC_EXE to its full path.' }
    }
    Write-Host '[6/6] Compiling Setup.exe'
    Run $iscc @('/Qp',(Join-Path $PSScriptRoot 'DrawingMaker3D.iss'))
    $setup = Join-Path $PSScriptRoot 'dist\DrawingMaker3D-Setup-0.6.0-x64.exe'
    if (!(Test-Path -LiteralPath $setup -PathType Leaf)) { throw 'Setup.exe not found' }
    Write-Host "SUCCESS: $setup"
    Stop-Transcript | Out-Null
    exit 0
} catch {
    Write-Host $_ -ForegroundColor Red
    Stop-Transcript | Out-Null
    exit 1
}
