from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
import json
import sys
from pathlib import Path

# путь к utils
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.process_query import *
from utils.get_dynamic_query_list import get_dynamic_query_list
from utils.config import levels
from utils.fit_hierarchy import *

app = FastAPI()

app.mount("/static", StaticFiles(directory="server/static"), name="static")
templates = Jinja2Templates(directory="server/templates")

# глобальные переменные
# hierarchy = None
# all_terms, norm2keys = None, None

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload-hierarchy/")
async def upload_hierarchy(file: UploadFile):
    try:
        content = await file.read()
        hierarchy = json.loads(content.decode("utf-8"))
        all_terms, norm2keys = fit_hierarchy(hierarchy)

        # Сохраняем в app.state
        app.state.hierarchy = hierarchy
        app.state.all_terms = all_terms
        app.state.norm2keys = norm2keys

        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/process-query/")
async def process_query_api(query: str = Form(...)):
    hierarchy = getattr(app.state, "hierarchy", None)
    all_terms = getattr(app.state, "all_terms", None)
    norm2keys = getattr(app.state, "norm2keys", None)

    if hierarchy is None:
        return {"status": "error", "message": "Иерархия не загружена"}

    try:
        processed_query = process_query(
            query, all_terms, norm2keys, hierarchy, levels,
            long_score_cutoff_first=65,
            long_score_cutoff_second=81,
            sim_threshold=60,
            sim_scorer=fuzz.token_set_ratio
        )
        queries_list = get_dynamic_query_list(hierarchy, processed_query, levels)
        return {"status": "ok", "response": str(queries_list)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
