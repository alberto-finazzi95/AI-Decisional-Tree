$ErrorActionPreference = "Stop"

# Check whether there are staged changes before doing any work.
$changed = git diff --cached --name-only

if (-not $changed) {
    Write-Host "[hook] No staged changes. Nothing to do."
    exit 0
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
