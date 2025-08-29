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

## CSC Rahti 2 Deployment Instructions

### 1. Push Docker Image to Rahti Registry

```bash
# Tag the image for Rahti registry
docker tag gemma-fast-api image-registry.apps.2.rahti.csc.fi/gaik/gemma-fast-api:latest

# Login to Rahti and Docker registry
oc login --server=https://api.2.rahti.csc.fi:6443
oc whoami -t | docker login image-registry.apps.2.rahti.csc.fi -u $(oc whoami) --password-stdin

# Push the image
docker push image-registry.apps.2.rahti.csc.fi/gaik/gemma-fast-api:latest
```

### 2. Deploy via Rahti Web Console

1. **Create Secret for API Key:**

   - Go to Workloads → Secrets → Create Secret
   - Name: `gemma-api-secret`
   - Type: `Opaque`
   - Key: `api-key`
   - Value: `your-generated-api-key`

2. **Create Deployment:**

   - Go to Workloads → Deployments → Create Deployment
   - Name: `gemma-fast-api`
   - Image: `image-registry.apps.2.rahti.csc.fi/gaik/gemma-fast-api:latest`
   - Port: `8080`
   - Environment Variables:
     - `API_KEY` → From Secret → `gemma-api-secret` → `api-key`
     - `MODEL_ID` → Value → `google/gemma-3-270m-it`
     - `HF_HUB_OFFLINE` → Value → `1`
     - `HF_HUB_DISABLE_TELEMETRY` → Value → `1`
   - Resources:
     - CPU Request: `500m`, Limit: `2000m`
     - Memory Request: `2Gi`, Limit: `4Gi`
   - Health Checks:
     - Readiness Probe: HTTP GET `/healthz` port `8080`, delay `30s`, period `10s`
     - Liveness Probe: HTTP GET `/healthz` port `8080`, delay `60s`, period `30s`

3. **Create Service:**

   - Go to Networking → Services → Create Service
   - Name: `gemma-fast-api-service`
   - Selector: `app=gemma-fast-api`
   - Port: `8080` → Target Port: `8080`

4. **Create Route:**
   - Go to Networking → Routes → Create Route
   - Name: `gemma-fast-api-route`
   - Service: `gemma-fast-api-service`
   - Target Port: `8080`
   - Secure Route: ✓ (TLS Termination: Edge)

### 3. API Usage Examples

Once deployed, your API will be available at: `https://gemma-fast-api-route-gaik.apps.2.rahti.csc.fi`

#### Health Check

```bash
curl https://gemma-fast-api-route-gaik.apps.2.rahti.csc.fi/healthz
# Response: {"status":"ok","ready":true}
```

#### Text Generation

```bash
curl -X POST https://gemma-fast-api-route-gaik.apps.2.rahti.csc.fi/v1/generate \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is artificial intelligence?",
    "max_new_tokens": 100,
    "temperature": 0.7,
    "top_p": 0.9
  }'
```

#### Python Example

```python
import requests

url = "https://gemma-fast-api-route-gaik.apps.2.rahti.csc.fi/v1/generate"
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

#### JavaScript Example

```javascript
const response = await fetch(
  "https://gemma-fast-api-route-gaik.apps.2.rahti.csc.fi/v1/generate",
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

OpenShift / CSC Rahti 2 notes

- Container listens on `8080` and runs as non-root (`USER 1001`).
- Caches are in `/cache` and writable for arbitrary UID.
- Provide env vars via Secrets/ConfigMaps:
  - `API_KEY` (required)
  - `HUGGINGFACE_HUB_TOKEN` (optional)
  - `MODEL_ID` (optional)
- Resource guidance (CPU-only): start with 2 CPU / 2-3 GiB RAM. The 270M model in FP32 needs ~1.1 GiB RAM for weights plus overhead.

Notes

- Model is loaded on startup; `/healthz` indicates readiness.
- Uses CPU with `torch.float32`. No GPU dependencies are required.
