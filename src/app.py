from fastapi import FastAPI

app = FastAPI(title="AlphaOS")


@app.get("/briefing")
def get_briefing():
    return {
        "market_state": "unknown",
        "watchlist_status": [],
        "risk_alerts": [],
        "key_changes": [],
    }
