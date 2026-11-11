$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$demoPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $demoPython)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -m venv .venv
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv .venv
    } else {
        throw 'Select or install a Python 3.10+ interpreter, then follow FRONTEND_GUIDE.md.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}
# Reconcile dependencies even when the environment already exists.
& $demoPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Could not install the dependencies.' }
& $demoPython -m streamlit run streamlit_app.py --global.developmentMode false --server.address 127.0.0.1

