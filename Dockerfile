FROM python:3.12-slim

# Install uv
RUN pip install --upgrade pip && pip install uv

# Copy pyproject.toml and poetry.lock 
COPY pyproject.toml /app/pyproject.toml

# If you use a lockfile (highly recommended for prod), add it:
COPY uv.lock /app/uv.lock

WORKDIR /app

# Install all dependencies using uv (fast, reproducible)
RUN uv pip install --system --no-cache-dir .

# Copy your app code into the image
COPY traydstream /app/traydstream

EXPOSE 7860

CMD ["python", "-u", "traydstream/app.py"]
