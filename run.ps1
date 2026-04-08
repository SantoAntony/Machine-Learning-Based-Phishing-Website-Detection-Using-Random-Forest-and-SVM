

param(
  [Parameter(Position = 0)]
  [string]$App = "Home.py",

  [int]$Port = 8501,

  [switch]$Setup
)

function Get-PythonExe {
  $venvPython = Join-Path $PSScriptRoot ".venv\\Scripts\\python.exe"
  if (Test-Path $venvPython) { return $venvPython }

  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) { return "py -3" }

  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) { return $python.Source }

  throw "Python not found. Install Python 3.8+ (python.org), then re-run."
}

function Invoke-Python {
  param([Parameter(Mandatory = $true)][string]$Python, [Parameter(Mandatory = $true)][string[]]$Args)
  if ($Python -eq "py -3") {
    & py -3 @Args
  }
  else {
    & $Python @Args
  }
}

$pythonExe = Get-PythonExe

if ($Setup -and -not (Test-Path (Join-Path $PSScriptRoot ".venv\\Scripts\\python.exe"))) {
  if ($pythonExe -eq "py -3") {
    & py -3 -m venv (Join-Path $PSScriptRoot ".venv")
  }
  else {
    & $pythonExe -m venv (Join-Path $PSScriptRoot ".venv")
  }
  $pythonExe = Join-Path $PSScriptRoot ".venv\\Scripts\\python.exe"
}

if ($Setup) {
  Invoke-Python -Python $pythonExe -Args @("-m", "pip", "install", "-r", (Join-Path $PSScriptRoot "requirements.txt"))
}

Invoke-Python -Python $pythonExe -Args @(
  "-m", "streamlit", "run", (Join-Path $PSScriptRoot $App),
  "--server.port", "$Port"
)

