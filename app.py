import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx

app = FastAPI(
    title="${{ values.name }}",
    description="${{ values.description }}"
)

LITELLM_URL = os.getenv("LITELLM_URL", "http://litellm.llmops.svc.cluster.local:4000")
LITELLM_KEY = os.getenv("LITELLM_API_KEY", "")

class PromptRequest(BaseModel):
    prompt: str
    model: str = "dxp-default"

@app.post("/generate")
async def generate(req: PromptRequest):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{LITELLM_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {LITELLM_KEY}"},
            json={
                "model": req.model,
                "messages": [{"role": "user", "content": req.prompt}],
            },
            timeout=30,
        )
        return resp.json()

@app.get("/health")
def health():
    return {"status": "ok", "service": "${{ values.name }}"}

# S61 (Jeudi) : page de demo minimale -- juste pour rendre l'appel /generate
# visible en direct devant un public (un curl seul ne raconte rien).
@app.get("/", response_class=HTMLResponse)
def demo_page():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Atlas LLM Assistant</title>
<style>
  body { font-family: sans-serif; max-width: 640px; margin: 0 auto; padding: 2rem; }
  h1 { margin-bottom: 0.2rem; }
  p.sub { color: #666; margin-top: 0; }
  textarea { width: 100%; padding: 10px; font-size: 15px; box-sizing: border-box; }
  button { padding: 10px 20px; font-size: 15px; margin-top: 10px; cursor: pointer; }
  #answer { margin-top: 1.5rem; padding: 16px; border: 1px solid #ddd; border-radius: 6px;
            min-height: 40px; white-space: pre-wrap; background: #fafafa; }
  #meta { color: #999; font-size: 12px; margin-top: 8px; }
</style>
</head>
<body>
  <h1>Atlas LLM Assistant</h1>
  <p class="sub">Deploye sur DxP -- Golden Path LLMOps / LiteLLM Gateway</p>

  <textarea id="prompt" rows="3" placeholder="Posez une question...">Quelle est la capitale du Maroc ?</textarea>
  <br>
  <button onclick="ask()">Demander</button>

  <div id="answer">La reponse s'affichera ici.</div>
  <div id="meta"></div>

<script>
async function ask() {
  const prompt = document.getElementById('prompt').value;
  const answerEl = document.getElementById('answer');
  const metaEl = document.getElementById('meta');
  answerEl.textContent = 'Reflexion en cours...';
  metaEl.textContent = '';
  const t0 = performance.now();
  try {
    const res = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });
    const data = await res.json();
    const content = data.choices?.[0]?.message?.content ?? JSON.stringify(data);
    const ms = Math.round(performance.now() - t0);
    answerEl.textContent = content;
    metaEl.textContent = `modele: ${data.model || 'dxp-default'} -- ${ms} ms -- ${data.usage?.total_tokens ?? '?'} tokens`;
  } catch (e) {
    answerEl.textContent = 'Erreur: ' + e;
  }
}
</script>
</body>
</html>
"""

