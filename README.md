# # Gemma 3 270M - FastAPI (CPU)

Minimal FastAPI service wrapping `google/gemma-3-270m-it` model.

- Bearer API key authentication
- CPU-only inference (no GPU required)
- Docker containerized

## Requirements

- `API_KEY` (required for authentication)
- `HUGGINGFACE_HUB_TOKEN` (required for model access - Gemma 3 requires authentication)
- Optional: `MODEL_ID` (default: `google/gemma-3-270m-it`)

## Local Development

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0
   ```

2. **Set environment variables:**

   ```bash
   export API_KEY=your-demo-key
   export HUGGINGFACE_HUB_TOKEN=hf_...  # required for model download
   ```

3. **Run locally:**

   ```bash
   python -m uvicorn app:app --host 0.0.0.0 --port 8080
   ```

## Docker

```bash
# Build
docker build -t gemma-fast-api .

# Run
docker run -e API_KEY=your-demo-key -e HUGGINGFACE_HUB_TOKEN=hf_... -p 8080:8080 gemma-fast-api
```

## API Endpoints

- `GET /healthz` - Health check
- `POST /v1/generate` - Text generation
- `GET /docs` - FastAPI documentation

## Usage Examples

### Health Check

```bash
curl http://localhost:8080/healthz
```

### Text Generation

```bash
curl -X POST http://localhost:8080/v1/generate \
  -H "Authorization: Bearer your-demo-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is artificial intelligence?",
    "max_new_tokens": 100,
    "temperature": 0.7
  }'
```

### Python Example

```python
import requests

response = requests.post(
    "http://localhost:8080/v1/generate",
    headers={"Authorization": "Bearer your-demo-key"},
    json={
        "prompt": "Explain machine learning",
        "max_new_tokens": 150,
        "temperature": 0.8
    }
)
print(response.json()["output"])
```
