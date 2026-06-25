cd $PSScriptRoot\..

uv run python --version
uv run python -c "import pandas, numpy, pyarrow, matplotlib; print('core imports ok')"
uv run python scripts\validate_data.py
