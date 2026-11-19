python -m pip install --upgrade pip pip-tools

pip-compile --generate-hashes --output-file requirements/requirements-ml-lock.txt requirements/requirements-ml.txt
pip-compile --generate-hashes --output-file requirements/requirements-kaggle-lock.txt requirements/requirements-kaggle.txt
pip-compile --generate-hashes --output-file requirements/requirements-dev-lock.txt requirements/requirements-dev.txt

Write-Host "Generated hash lock files in requirements/"

