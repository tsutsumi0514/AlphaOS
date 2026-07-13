def build_briefing():
    return {
        "market_state": "unknown",
        "watchlist_status": [],
        "risk_alerts": [],
        "key_changes": [],
    }


if __name__ == "__main__":
    briefing = build_briefing()
    print(briefing)
