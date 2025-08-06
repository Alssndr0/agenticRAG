FROM python:3.12-slim

# Install uv
RUN pip install --upgrade pip && pip install uv

WORKDIR /aimw

COPY pyproject.toml /aimw/pyproject.toml
COPY uv.lock /aimw/uv.lock
RUN uv pip install --system --no-cache-dir .

COPY aimw/app /aimw/app
COPY conf /aimw/conf    

ENV PYTHONPATH=/aimw

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


