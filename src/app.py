from fastapi import FastAPI, Query
from .briefing import build_briefing

app = FastAPI(title="AlphaOS")


@app.get("/briefing")
def get_briefing(usd_jpy: float | None = Query(default=None, description="USD/JPY rate")):
    source = {"usd_jpy": usd_jpy} if usd_jpy is not None else None
    return build_briefing(source)
