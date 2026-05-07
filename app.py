"""
FastAPI web server for the multi-agent news aggregation pipeline.

Usage:
    uvicorn app:app --reload          # development
    python app.py                     # production (port 8000)
"""
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.WARNING)

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(title="Balanced News Digest", version="0.1.0")

# Serve frontend static files
FRONTEND = ROOT / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")


# ── Models ─────────────────────────────────────────────────────────────────────

class RunRequest(BaseModel):
    topic: str = Field(default="economy", min_length=1, max_length=100)
    demo: bool = False


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    html_path = FRONTEND / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.post("/api/run")
def run_pipeline(req: RunRequest):
    """Run the news aggregation pipeline and return the balanced digest."""
    try:
        from run_local import run
        result = run(topic=req.topic, demo=req.demo)
        digest = result.get("balanced_digest", {})
        # Count stats for the UI
        digest["_stats"] = {
            "left_count": len(result.get("left_articles", [])),
            "right_count": len(result.get("right_articles", [])),
            "summaries_count": len(result.get("summaries", [])),
            "pairs_count": len(result.get("matched_stories", [])),
        }
        return digest
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health")
def health():
    return {"status": "ok"}


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
