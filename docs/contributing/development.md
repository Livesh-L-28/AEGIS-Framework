# Development Guide

```bash
git clone https://github.com/Livesh-L-28/AEGIS-Framework.git
cd AEGIS-Framework
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,all]"
pytest -v
ruff check .
mypy aegis
```
