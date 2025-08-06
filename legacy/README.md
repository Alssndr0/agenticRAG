# local only - opens the tunnel 
ngrok http 127.0.0.1:1234

docker build -t traydstream-app .
# insert the ngrok https followed by /v1
docker run --rm -p 7860:7860 -e LLM_API_BASE="https://ec711726f134.ngrok-free.app/v1" traydstream-app


# create Amazon ECR
aws ecr create-repository --repository-name traydstream-app --region eu-west-1
-> "456104590794.dkr.ecr.eu-west-1.amazonaws.com/traydstream-app"
# authenticate Docker to region
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 456104590794.dkr.ecr.eu-west-1.amazonaws.com
# tag and push image
docker tag traydstream-app:latest <repo-uri>:latest
docker push <repo-uri>:latest


# delete Amazon ECR

export PYTHONPATH="$PWD"
python -m app.gradio.app


```bash
git clone https://github.com/Alssndr0/agenticRAG.git
cd agenticRAG
git checkout traydstream
```

```bash
pip install uv
uv pip install -r pyproject.toml
```

```bash
cd aimw
export PYTHONPATH="$PWD"
uvicorn app.main:app --reload
```

- The app will run at http://127.0.0.1:8000
- Interactive docs available at http://127.0.0.1:8000/docs

```bash
cd aimw
export PYTHONPATH="$PWD"
python -m app.gradio.app
```