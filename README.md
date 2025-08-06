# 🚢 Traydstream Compliance Agent

Automated compliance checking for trade documents.

## Clone & Setup (Linux)

```bash
git clone https://github.com/Alssndr0/agenticRAG.git
cd agenticRAG
pip install uv
uv pip install -r pyproject.toml
cd aimw
# Add the project directory to PYTHONPATH
export PYTHONPATH="$PWD"
# lunch the service
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# lunch Gradio
python -m app.gradio.app
```
---

## Run Locally with Docker

```bash
# From project root - Build and compose.
docker compose up --build
```

---

## API Endpoint: `POST /api/v1/run/run-check`

### Description

Uploads and checks a trade document (PDF or text) for compliance. Returns a detailed compliance report.

| Method | URL                                      | Content-Type |
| ------ | ---------------------------------------- | ------------ |
| `POST` | `http://127.0.0.1:8000/api/v1/run/run-check` | `form-data`  |

| Field | Type   | Example          | Description                   |
| ----- | ------ | ---------------- | ----------------------------- |
| file  | File   | bill_of_lading.pdf | The document to check         |
| query | String | Please check...  | (Optional) extra instructions |

---

**NOTE**: All endpoints require an **API Key** header: `mysecretkey1`

---

### Example cURL

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/run/run-check" \
  -H "Authorization: Bearer mysecretkey1" \
  -F "file=@data/bill_of_lading.pdf" \
  -F "query=Please check my document for compliance."
```

## Infrastructure Management (Terraform - Kubernetes - Docker)
All infrastructure-as-code files are in the `infra` folder.

---

## Developer Tips

`cd aimw` and add `export PYTHONPATH="$PWD"` before launching for clean imports.


## License

...

