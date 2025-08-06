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

After running, visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for all API endpoints.

---

## Run Locally with Docker

```bash
# From project root - Build Docker image
docker build -t traydstream-app:latest .
# Run
docker run -p 8000:8000 traydstream-app:latest
```

---

## Deploy to Amazon ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name traydstream-app --region eu-west-1
# "456104590794.dkr.ecr.eu-west-1.amazonaws.com/traydstream-app"
# Authenticate Docker
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 456104590794.dkr.ecr.eu-west-1.amazonaws.com
# Tag and push images
docker tag traydstream-app:latest 456104590794.dkr.ecr.eu-west-1.amazonaws.com/traydstream-app:latest
docker push 456104590794.dkr.ecr.eu-west-1.amazonaws.com/traydstream-app:latest
# Delete the ECR repository (if needed)
aws ecr delete-repository --repository-name traydstream-app --region eu-west-1 --force
```

## Infrastructure Management (Terraform)
All infrastructure-as-code files are in the `infra` folder.

```bash
cd infra
terraform init
# preview changes 
terraform plan
# provision resources 
terraform apply
# destroy infrastructure 
terraform destroy
```

## API Endpoint: `POST /api/v1/run/run-check`

### Description

Uploads and checks a trade document (PDF or text) for compliance. Returns a detailed compliance report.

| Method | URL                                      | Content-Type |
| ------ | ---------------------------------------- | ------------ |
| `POST` | `http://127.0.0.1:8000/api/v1/run/run-check` | `form-data`  |

### Request fields

| Field | Type   | Example          | Description                   |
| ----- | ------ | ---------------- | ----------------------------- |
| file  | File   | bill_of_lading.pdf | The document to check         |
| query | String | Please check...  | (Optional) extra instructions |

---

**NOTE**: All endpoints require an **API Key** header: `mysecretkey1`

---

### Example cURL

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/run-check" \
  -H "X-API-Key: mysecretkey1" \
  -F "file=@/path/to/BillOfLading.pdf" \
  -F "query=Please check my document for compliance."
```

### Example Response

```json
{
  "answer": "DOCUMENT COMPLIANCE REPORT\n========================\nTotal checks performed: 3\nChecks passed: 2\nChecks failed: 1\nOverall status: NON-COMPLIANT\n\nDETAILED RESULTS:\n1. SWIFT CHECK: ✓ PASSED\n   Explanation: All required SWIFT fields present.\n2. UCP600 CHECK: ✓ PASSED\n   Explanation: Document conforms to UCP600 requirements.\n3. CONFLICT CHECK: ✗ FAILED\n   Explanation: Discrepancy with letter of credit terms."
}
```



## Developer Tips

`cd aimw` and add `export PYTHONPATH="$PWD"` before launching for clean imports.


## License

...

