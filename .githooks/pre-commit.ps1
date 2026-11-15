$ErrorActionPreference = "Stop"

# Check whether there are staged changes before doing any work.
$changed = git diff --cached --name-only

if (-not $changed) {
    Write-Host "[hook] No staged changes. Nothing to do."
    exit 0
}

# Prefer the repository virtual environment; otherwise use Python from PATH.
$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $python = $pythonCommand.Source
    }
    else {
        Write-Host "[hook] Python was not found. Install Python or create the repository .venv."
        exit 1
    }
}

# Check staged Python files for lint and formatting issues before continuing.
$pythonFiles = @($changed | Where-Object { $_ -match '\.py$' })

if ($pythonFiles.Count -gt 0) {
    Write-Host "[hook] Checking staged Python files with Ruff..."
    & $python -m ruff check --statistics --output-format=full @pythonFiles

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[hook] Ruff found issues. Fix them with: $python -m ruff check . --fix"
        exit 1
    }

    Write-Host "[hook] Checking staged Python files with Black..."
    & $python -m black --check @pythonFiles

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[hook] Black found formatting issues. Format them with: $python -m black $($pythonFiles -join ' ')"
        exit 1
    }
}
else {
    Write-Host "[hook] No staged Python files. Skipping Ruff and Black."
}
# Check all the repository for lint and formatting issues, even if no Python files are staged. This ensures that the repository is always in a clean state.
Write-Host "[hook] Checking staged Python files with Ruff..."
& $python -m  ruff check --statistics --output-format=full
if ($LASTEXITCODE -ne 0) {
    Write-Host "[hook] Ruff found issues. Run 'ruff check . --fix' and stage the corrected files."
    exit 1
}

Write-Host "[hook] Checking staged Python files with Black..."
& $python -m black --check .

if ($LASTEXITCODE -ne 0) {
    Write-Host "[hook] Black found formatting issues. Run 'black .' and stage the formatted files."
    exit 1
}
# Only react when a dependency file has changed.
# This keeps the hook lightweight and avoids regenerating lock files for unrelated edits.
$needsLock = $false

foreach ($f in $changed) {
    if ($f -match '(^|/)requirements\.txt$' -or
        $f -match '(^|/)requirements/.+\.txt$' -or
        $f -match '(^|/)requirements-.+\.txt$') {
        $needsLock = $true
        break
    }
}

if (-not $needsLock) {
    Write-Host "[hook] No dependency file changed. Skipping lock refresh."
    exit 0
}

Write-Host "[hook] Dependency file changed. Refreshing lock files..."

# If the repository root does not already provide a requirements.txt file,
# create one from the current Python environment so the default file exists.
if (-not (Test-Path "requirements.txt")) {
    Write-Host "[hook] requirements.txt not found in the repo root. Creating it from pip freeze."
    python -m pip freeze > requirements.txt
    git add requirements.txt
}
else {
    Write-Host "[hook] Root requirements.txt already exists. Keeping the repository default file."
}

# Generate the main hashed lock file only when the root requirements file exists.
if (Test-Path "requirements.txt") {
    Write-Host "[hook] Generating hashed lock for the root requirements.txt"
    pip-compile --generate-hashes --output-file requirements-lock.txt requirements.txt
    git add requirements.txt requirements-lock.txt
}

# Generate grouped lock files for project-specific dependency sets.
# These are usually easier to maintain and faster to resolve than one giant lock file.
if (Test-Path "requirements/requirements-ml.txt") {
    Write-Host "[hook] Generating ML lock file"
    pip-compile --generate-hashes --output-file requirements/requirements-ml-lock.txt requirements/requirements-ml.txt
    git add requirements/requirements-ml-lock.txt
}

if (Test-Path "requirements/requirements-kaggle.txt") {
    Write-Host "[hook] Generating Kaggle lock file"
    pip-compile --generate-hashes --output-file requirements/requirements-kaggle-lock.txt requirements/requirements-kaggle.txt
    git add requirements/requirements-kaggle-lock.txt
}

if (Test-Path "requirements/requirements-dev.txt") {
    Write-Host "[hook] Generating development lock file"
    pip-compile --generate-hashes --output-file requirements/requirements-dev-lock.txt requirements/requirements-dev.txt
    git add requirements/requirements-dev-lock.txt
}

Write-Host "[hook] Lock files refreshed and staged."
