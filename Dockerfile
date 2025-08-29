FROM registry.access.redhat.com/ubi9/python-312:latest

LABEL name="gemma-fast-api" \
      vendor="demo" \
      summary="FastAPI wrapper for Google Gemma 3 270M" \
      description="CPU-only FastAPI service exposing a minimal text generation endpoint for Gemma 3 270M"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/opt/app-root/cache \
    TRANSFORMERS_CACHE=/opt/app-root/cache \
    HUGGINGFACE_HUB_CACHE=/opt/app-root/cache

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.8.0

# Create cache directory and pre-download the model during build
RUN mkdir -p /opt/app-root/cache && \
    chgrp -R 0 /opt/app-root/cache && \
    chmod -R g+rwX /opt/app-root/cache

ARG HUGGINGFACE_HUB_TOKEN
RUN python -c "\
import os; \
os.environ['HUGGINGFACE_HUB_TOKEN'] = '${HUGGINGFACE_HUB_TOKEN}'; \
from huggingface_hub import login; \
from transformers import AutoTokenizer, AutoModelForCausalLM; \
login(token='${HUGGINGFACE_HUB_TOKEN}'); \
model_id = 'google/gemma-3-270m-it'; \
print(f'Downloading model: {model_id}'); \
tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir='/opt/app-root/cache'); \
model = AutoModelForCausalLM.from_pretrained(model_id, cache_dir='/opt/app-root/cache'); \
print('Model downloaded successfully')"

# Copy the application
COPY app.py ./

EXPOSE 8080
ENV MODEL_ID=google/gemma-3-270m-it
ENV HF_HUB_OFFLINE=1
ENV HF_HUB_DISABLE_TELEMETRY=1

# Non-root user for OpenShift
USER 1001

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
