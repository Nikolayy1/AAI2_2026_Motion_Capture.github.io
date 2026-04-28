from fastapi import FastAPI
import json
from pathlib import Path

app = FastAPI()
ROOT = Path(__file__).resolve().parent
ANIMATION_FILE = ROOT / "opensim_animation.json"

@app.get('/opensim/animation')
def get_opensim_animation():
    with open(ANIMATION_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)
