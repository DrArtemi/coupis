# Coupis API

Install the backend in editable mode from the repository root:

```bash
python -m pip install -e 'apps/api[dev]'
```

Start the development server from the repository root:

```bash
uvicorn coupis.api.main:app --app-dir apps/api/src --reload
```

The health endpoint is available at `http://localhost:8000/health` and the
interactive OpenAPI documentation at `http://localhost:8000/docs`.
