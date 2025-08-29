Gemma 3 270M - FastAPI (CPU) for CSC Rahti 2

- Minimal FastAPI service wrapping `google/gemma-3-270m` (default: `-it`).
- Bearer API key auth with `Authorization: Bearer <API_KEY>`.
- UBI9 Python base, OpenShift-friendly (non-root, port 8080).

Requirements

- Set `API_KEY` (required).
- Optional: `HUGGINGFACE_HUB_TOKEN` if the model requires auth or rate-limit relief.
- Optional: `MODEL_ID` (default: `google/gemma-3-270m-it`).

Local run

- Create and export env vars locally:
  - `API_KEY=your-demo-key`
  - `HUGGINGFACE_HUB_TOKEN=hf_...` (optional)
- Install deps:
  - `pip install -r requirements.txt`
  - `pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0`
- Run: `python -m uvicorn app:app --host 0.0.0.0 --port 8080`

Docker build

- Build: `docker build -t gemma-fast-api:latest .`
- Run: `docker run -e API_KEY=your-demo-key -p 8080:8080 gemma-fast-api:latest`

Endpoints

- `GET /healthz`: `{ status: "ok", ready: true|false }`.
- `POST /v1/generate`:
  - Headers: `Authorization: Bearer <API_KEY>`
  - Body: `{ "prompt": "hello", "max_new_tokens": 64, "temperature": 0.7, "top_p": 0.9 }`
  - Response: `{ "output": "..." }`

Example curl

```bash
curl -s -X POST http://localhost:8080/v1/generate \
  -H "Authorization: Bearer your-demo-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is the capital of Finland?","max_new_tokens":32}'
```

## CSC Rahti 2 Deployment

```bash
# Build and push to Rahti registry
docker build -t gemma-fast-api .
docker tag gemma-fast-api image-registry.apps.2.rahti.csc.fi/gaik/gemma-fast-api:latest

oc login --server=https://api.2.rahti.csc.fi:6443
oc whoami -t | docker login image-registry.apps.2.rahti.csc.fi -u $(oc whoami) --password-stdin
docker push image-registry.apps.2.rahti.csc.fi/gaik/gemma-fast-api:latest
```

Deploy via Rahti Web Console with:

- **Image**: `image-registry.apps.2.rahti.csc.fi/gaik/gemma-fast-api:latest`
- **Resources**: CPU 2000m, Memory 4Gi
- **Environment**: `API_KEY` (from secret), `HF_HUB_OFFLINE=1`

## API Usage Examples

Once deployed, your API will be available at: `https://gemma-llm-gaik.2.rahtiapp.fi`

### Health Check

```bash
curl https://gemma-llm-gaik.2.rahtiapp.fi/healthz
# Response: {"status":"ok","ready":true}
```

#### FastAPI Documentation

Open in browser: `https://gemma-llm-gaik.2.rahtiapp.fi/docs`

### Text Generation

```bash
curl -X POST https://gemma-llm-gaik.2.rahtiapp.fi/v1/generate \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is artificial intelligence?",
    "max_new_tokens": 100,
    "temperature": 0.7,
    "top_p": 0.9
  }'
```

### Postman Testing

1. **Health Check Request:**

   - Method: `GET`
   - URL: `https://gemma-llm-gaik.2.rahtiapp.fi/healthz`
   - Headers: None required
   - Expected Response: `{"status":"ok","ready":true}`

2. **Text Generation Request:**

   - Method: `POST`
   - URL: `https://gemma-llm-gaik.2.rahtiapp.fi/v1/generate`
   - Headers:

     ```text
     Authorization: Bearer your-api-key
     Content-Type: application/json
     ```

   - Body (raw JSON):

     ```json
     {
       "prompt": "Explain machine learning in simple terms",
       "max_new_tokens": 100,
       "temperature": 0.7,
       "top_p": 0.9
     }
     ```

   - Expected Response:

     ```json
     {
       "output": "Machine learning is a subset of artificial intelligence..."
     }
     ```

3. **Import to Postman:**
   - Create new Collection: "Gemma API"
   - Add Environment variables:
     - `base_url`: `https://gemma-llm-gaik.2.rahtiapp.fi`
     - `api_key`: `your-api-key`
   - Use `{{base_url}}` and `{{api_key}}` in requests

### Python Example

```python
import requests

url = "https://gemma-llm-gaik.2.rahtiapp.fi/v1/generate"
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}
data = {
    "prompt": "Explain machine learning in simple terms",
    "max_new_tokens": 150,
    "temperature": 0.8
}

response = requests.post(url, headers=headers, json=data)
result = response.json()
print(result["output"])
```

### JavaScript Example

```javascript
const response = await fetch(
  "https://gemma-llm-gaik.2.rahtiapp.fi/v1/generate",
  {
    method: "POST",
    headers: {
      Authorization: "Bearer your-api-key",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      prompt: "Write a haiku about coding",
      max_new_tokens: 50,
      temperature: 0.9,
    }),
  }
);

const result = await response.json();
console.log(result.output);
```

## Notes

- Container listens on `8080` and runs as non-root (`USER 1001`).
- Caches are in `/cache` and writable for arbitrary UID.
- Provide env vars via Secrets/ConfigMaps:
  - `API_KEY` (required)
  - `HUGGINGFACE_HUB_TOKEN` (optional)
  - `MODEL_ID` (optional)
- Resource guidance (CPU-only): start with 2 CPU / 2-3 GiB RAM. The 270M model in FP32 needs ~1.1 GiB RAM for weights plus overhead.
- Model is loaded on startup; `/healthz` indicates readiness.
- Uses CPU with `torch.float32`. No GPU dependencies are required.
