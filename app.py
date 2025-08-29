import os

import torch
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

# Configuration
API_KEY = os.getenv("API_KEY", "")
MODEL_ID = os.getenv("MODEL_ID", "google/gemma-3-270m-it")
DTYPE = torch.float32  # CPU-safe

app = FastAPI(title="Gemma-3 270M API", version="1.0.0")
security = HTTPBearer()


def check_bearer(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not API_KEY or credentials.scheme.lower() != "bearer" or credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


@app.on_event("startup")
def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=DTYPE,
        low_cpu_mem_usage=True,
        local_files_only=True,
    )
    model.eval()
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token = tokenizer.eos_token
    app.state.tokenizer = tokenizer
    app.state.model = model


class GenerateRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 128
    temperature: float = 0.7
    top_p: float = 0.9


class GenerateResponse(BaseModel):
    output: str


@app.get("/healthz")
def health():
    ready = hasattr(app.state, "model") and hasattr(app.state, "tokenizer")
    return {"status": "ok", "ready": ready}


@app.post("/v1/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest, _=Depends(check_bearer)):
    tokenizer = app.state.tokenizer
    model = app.state.model

    # Prefer chat template (-it models); fallback to plain tokenization
    try:
        input_ids = tokenizer.apply_chat_template(
            [{"role": "user", "content": req.prompt}],
            add_generation_prompt=True,
            return_tensors="pt",
        )
    except Exception:
        input_ids = tokenizer(req.prompt, return_tensors="pt").input_ids

    with torch.no_grad():
        output_ids = model.generate(
            input_ids,
            max_new_tokens=req.max_new_tokens,
            do_sample=req.temperature > 0,
            temperature=req.temperature,
            top_p=req.top_p,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
        )

    new_tokens = output_ids[0, input_ids.shape[-1]:]
    text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    return GenerateResponse(output=text)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8080)


