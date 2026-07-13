from fastapi import FastAPI
from .briefing import build_briefing

app = FastAPI(title="AlphaOS")


@app.get("/briefing")
def get_briefing():
    return build_briefing()
