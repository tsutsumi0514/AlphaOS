def build_briefing():
    return {
        "market_state": "unknown",
        "watchlist_status": [],
        "risk_alerts": [],
        "key_changes": [],
    }


def main():
    briefing = build_briefing()
    print(briefing)


if __name__ == "__main__":
    main()
