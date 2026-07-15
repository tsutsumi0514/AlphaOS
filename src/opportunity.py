"""Opportunity Engine helpers for ranked buy candidates."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, NotRequired, TypedDict

from .agents.contracts import normalize_confidence


class OpportunityCandidate(TypedDict):
    symbol: str
    name: str
    horizon: str
    rank: int
    score: float
    confidence: str
    reasons: list[str]
    risk_alerts: list[str]
    evidence: list[dict[str, Any]]
    entry_timing: str
    entry_reason: str
    status: str
    counter_evidence: list[str]
    liquidity: str
    note: NotRequired[str]
    sector: NotRequired[str]
    sector_strength: NotRequired[str]


class OpportunityExclusion(TypedDict):
    symbol: str
    name: str
    horizon: str
    score: float
    confidence: str
    liquidity: str
    reason: str


class OpportunityPool(TypedDict):
    candidates: list[OpportunityCandidate]
    excluded: list[OpportunityExclusion]


def build_opportunity_candidates(
    briefing: Mapping[str, Any],
    *,
    horizon: str = "swing",
    limit: int = 5,
) -> list[OpportunityCandidate]:
    """Rank buy candidates from the current briefing payload."""
    return evaluate_candidate_pool(briefing, horizon=horizon, limit=limit)["candidates"]


def evaluate_candidate_pool(
    briefing: Mapping[str, Any],
    *,
    horizon: str = "swing",
    limit: int = 5,
) -> OpportunityPool:
    horizon_value = _normalize_horizon(horizon)
    watchlist_items = _watchlist_items(briefing)
    if not watchlist_items:
        return {"candidates": [], "excluded": []}

    candidates: list[OpportunityCandidate] = []
    excluded: list[OpportunityExclusion] = []
    for item in watchlist_items:
        candidate = _build_candidate(briefing, item, horizon_value)
        if _should_exclude(candidate):
            excluded.append(
                {
                    "symbol": candidate["symbol"],
                    "name": candidate["name"],
                    "horizon": candidate["horizon"],
                    "score": candidate["score"],
                    "confidence": candidate["confidence"],
                    "liquidity": candidate["liquidity"],
                    "reason": _exclude_reason(candidate),
                }
            )
            continue
        candidates.append(candidate)

    candidates.sort(key=lambda candidate: candidate["score"], reverse=True)
    for index, candidate in enumerate(candidates, start=1):
        candidate["rank"] = index
    return {
        "candidates": candidates[: max(limit, 0)],
        "excluded": excluded,
    }


def _build_candidate(
    briefing: Mapping[str, Any],
    item: Mapping[str, Any],
    horizon: str,
) -> OpportunityCandidate:
    symbol = _text(item.get("symbol")) or "UNKNOWN"
    name = _text(item.get("name")) or symbol
    score = _candidate_score(briefing, item, horizon)
    confidence = _candidate_confidence(score, briefing)
    liquidity = _liquidity_state(item)
    sector = _candidate_sector(item)
    sector_strength = _sector_strength(briefing, sector)
    reasons = _candidate_reasons(briefing, item, sector_strength)
    risk_alerts = _candidate_risk_alerts(briefing, item, liquidity)
    evidence = _candidate_evidence(briefing, item, sector)
    counter_evidence = _candidate_counter_evidence(
        briefing, item, liquidity, confidence, evidence
    )
    entry_timing = _entry_timing(score, briefing, item, horizon, liquidity)
    status = _candidate_status(score, briefing, item, horizon, liquidity)

    candidate: OpportunityCandidate = {
        "symbol": symbol,
        "name": name,
        "horizon": horizon,
        "score": score,
        "confidence": confidence,
        "reasons": reasons,
        "risk_alerts": risk_alerts,
        "evidence": evidence,
        "entry_timing": entry_timing,
        "entry_reason": _entry_reason(candidate_status=status, entry_timing=entry_timing, liquidity=liquidity, score=score),
        "status": status,
        "counter_evidence": counter_evidence,
        "liquidity": liquidity,
    }
    if sector:
        candidate["sector"] = sector
    if sector_strength:
        candidate["sector_strength"] = sector_strength
    note = _candidate_note(candidate)
    if note is not None:
        candidate["note"] = note
    return candidate


def _should_exclude(candidate: OpportunityCandidate) -> bool:
    evidence_count = len(candidate["evidence"])
    confidence = candidate["confidence"]
    score = candidate["score"]
    liquidity = candidate["liquidity"]
    status = candidate["status"]
    horizon = candidate["horizon"]

    if evidence_count == 0:
        return True
    if score < 0.42:
        return True
    if confidence == "low" and score < 0.6:
        return True
    if status == "avoid" and score < 0.58:
        return True
    if horizon == "daytrade" and liquidity in {"thin", "unknown"} and score < 0.72:
        return True
    if liquidity == "thin" and confidence == "low":
        return True
    return False


def _exclude_reason(candidate: OpportunityCandidate) -> str:
    if candidate["horizon"] == "daytrade" and candidate["liquidity"] in {"thin", "unknown"}:
        return "Liquidity is too weak for day-trade use."
    if candidate["confidence"] == "low":
        return "Confidence is too low for a ranked candidate."
    if candidate["score"] < 0.42:
        return "Score is too weak after evidence and risk checks."
    if candidate["status"] == "avoid":
        return "Risk and evidence do not support a candidate."
    if not candidate["evidence"]:
        return "No structured evidence is available."
    return "Candidate does not pass the exclusion filter."


def _candidate_score(
    briefing: Mapping[str, Any],
    item: Mapping[str, Any],
    horizon: str,
) -> float:
    score = _base_score(item.get("status"))

    market_state = _text(briefing.get("market_state"))
    if market_state == "bullish":
        score += 0.1
    elif market_state == "bearish":
        score -= 0.1

    fx_state = _text(briefing.get("fx_state"))
    if fx_state == "weak yen":
        score += 0.08
    elif fx_state == "strong yen":
        score -= 0.08

    decision_ai = briefing.get("decision_ai")
    if isinstance(decision_ai, Mapping):
        stance = _text(decision_ai.get("stance"))
        if stance == "supportive":
            score += 0.08
        elif stance == "defensive":
            score -= 0.08

    evidence_count = len(_evidence_items(briefing))
    if evidence_count >= 4:
        score += 0.05
    elif evidence_count <= 1:
        score -= 0.05

    liquidity = _liquidity_state(item)
    if liquidity == "high":
        score += 0.05
    elif liquidity == "medium":
        score += 0.02
    elif liquidity == "thin":
        score -= 0.12

    sector_strength = _sector_strength(briefing, _candidate_sector(item))
    if sector_strength in {"strong", "supported", "positive", "bullish"}:
        score += 0.04
    elif sector_strength in {"weak", "negative", "bearish"}:
        score -= 0.04

    if horizon == "daytrade":
        if liquidity == "thin":
            score -= 0.08
        elif liquidity == "high":
            score += 0.03

    return round(_clamp(score), 3)


def _candidate_confidence(score: float, briefing: Mapping[str, Any]) -> str:
    briefing_confidence = normalize_confidence(briefing.get("confidence"))
    if score >= 0.8 and briefing_confidence == "high":
        return "high"
    if score >= 0.6:
        return "medium"
    return "low"


def _candidate_reasons(
    briefing: Mapping[str, Any],
    item: Mapping[str, Any],
    sector_strength: str,
) -> list[str]:
    reasons: list[str] = []

    symbol = _text(item.get("symbol")) or "Watchlist"
    status = _text(item.get("status"))
    if status == "strong":
        reasons.append(f"{symbol} is showing strong momentum.")
    elif status == "steady":
        reasons.append(f"{symbol} is holding a steady setup.")
    elif status == "weak":
        reasons.append(f"{symbol} is weakening and needs caution.")

    market_state = _text(briefing.get("market_state"))
    if market_state == "bullish":
        reasons.append("Market tone is supportive.")
    elif market_state == "bearish":
        reasons.append("Market tone is defensive.")

    fx_state = _text(briefing.get("fx_state"))
    if fx_state == "weak yen":
        reasons.append("Yen weakness may support exporters.")
    elif fx_state == "strong yen":
        reasons.append("Yen strength may pressure exporters.")

    if sector_strength:
        reasons.append(f"Sector tone is {sector_strength}.")

    decision_ai = briefing.get("decision_ai")
    if isinstance(decision_ai, Mapping):
        reason = _text(decision_ai.get("reason"))
        if reason:
            reasons.append(reason)

    return _unique_short_list(reasons)


def _candidate_risk_alerts(
    briefing: Mapping[str, Any],
    item: Mapping[str, Any],
    liquidity: str,
) -> list[str]:
    alerts = _string_list(briefing.get("risk_alerts"))

    status = _text(item.get("status"))
    symbol = _text(item.get("symbol")) or "Watchlist"
    if status == "weak":
        alerts.append(f"{symbol} is weak and entry timing is fragile.")
    if liquidity == "thin":
        alerts.append(f"{symbol} has thin liquidity for active entry.")

    return _unique_short_list(alerts)


def _candidate_counter_evidence(
    briefing: Mapping[str, Any],
    item: Mapping[str, Any],
    liquidity: str,
    confidence: str,
    evidence: list[dict[str, Any]],
) -> list[str]:
    counters: list[str] = []

    market_state = _text(briefing.get("market_state"))
    if market_state == "bearish":
        counters.append("Broad market tone is defensive.")

    fx_state = _text(briefing.get("fx_state"))
    if fx_state == "strong yen":
        counters.append("Yen strength may pressure exporters.")

    status = _text(item.get("status"))
    if status == "weak":
        counters.append("Watchlist status is weak.")

    if liquidity == "thin":
        counters.append("Liquidity is thin for near-term entry.")

    if confidence == "low":
        counters.append("Briefing confidence is low.")

    if len(evidence) <= 1:
        counters.append("Evidence coverage is limited.")

    decision_ai = briefing.get("decision_ai")
    if isinstance(decision_ai, Mapping) and _text(decision_ai.get("stance")) == "defensive":
        counters.append("Decision AI is defensive.")

    if not counters:
        symbol = _text(item.get("symbol")) or "The candidate"
        counters.append(f"{symbol} still depends on momentum staying intact.")

    return _unique_short_list(counters)


def _candidate_evidence(
    briefing: Mapping[str, Any],
    item: Mapping[str, Any],
    sector: str,
) -> list[dict[str, Any]]:
    evidence = _evidence_items(briefing)
    symbol = _text(item.get("symbol"))
    if symbol:
        evidence.append(
            {
                "source": "opportunity",
                "label": symbol,
                "value": item.get("status"),
                "note": f"change_pct={item.get('change_pct')}",
            }
        )
    if sector:
        evidence.append(
            {
                "source": "opportunity",
                "label": "sector",
                "value": sector,
                "note": _sector_strength(briefing, sector) or "unrated",
            }
        )
    return evidence


def _entry_timing(
    score: float,
    briefing: Mapping[str, Any],
    item: Mapping[str, Any],
    horizon: str,
    liquidity: str,
) -> str:
    status = _text(item.get("status"))
    market_state = _text(briefing.get("market_state"))
    confidence = _candidate_confidence(score, briefing)

    if horizon == "daytrade":
        if liquidity == "high" and score >= 0.65 and status == "strong":
            return "buy_now"
        if liquidity in {"high", "medium"} and score >= 0.55 and market_state != "bearish":
            return "wait"
        return "avoid"

    if horizon == "long":
        if (
            score >= 0.82
            and status == "strong"
            and liquidity == "high"
            and confidence == "high"
            and market_state in {"bullish", "neutral", "balanced"}
        ):
            return "buy_now"
        if score >= 0.7 and status in {"strong", "steady"} and market_state != "bearish":
            return "wait"
        return "avoid"

    if score >= 0.75 and status == "strong" and market_state != "bearish":
        return "buy_now"
    if score >= 0.55:
        return "wait"
    return "avoid"


def _candidate_status(
    score: float,
    briefing: Mapping[str, Any],
    item: Mapping[str, Any],
    horizon: str,
    liquidity: str,
) -> str:
    market_state = _text(briefing.get("market_state"))
    status = _text(item.get("status"))
    confidence = _candidate_confidence(score, briefing)

    if horizon == "long" and (
        confidence == "low"
        or score < 0.7
        or market_state == "bearish"
        or status not in {"strong", "steady"}
    ):
        return "avoid"
    if score >= 0.72 and status == "strong" and market_state != "bearish":
        return "buy_watch"
    if horizon == "daytrade" and liquidity == "thin":
        return "avoid"
    if score <= 0.45 or market_state == "bearish":
        return "avoid"
    return "wait"


def _entry_reason(
    *,
    candidate_status: str,
    entry_timing: str,
    liquidity: str,
    score: float,
) -> str:
    if entry_timing == "buy_now":
        if liquidity == "high":
            return "Strong evidence and liquid flow support action now."
        return "Signals are aligned enough to act now."
    if candidate_status == "avoid":
        return "Risk and evidence are not aligned enough for entry."
    if liquidity == "thin":
        return "Setup is valid, but liquidity is too thin to act now."
    if score >= 0.55:
        return "Setup is valid, but timing is not yet favorable."
    return "Evidence is too weak for a candidate entry."


def _candidate_note(candidate: OpportunityCandidate) -> str | None:
    if candidate["status"] == "avoid":
        return "Risk is higher than the current evidence supports."
    if candidate["confidence"] == "low":
        return "Evidence is thin; keep this as a watch item only."
    if candidate["entry_timing"] == "wait":
        return "Timing is not yet favorable."
    return None


def _base_score(status: Any) -> float:
    text = _text(status)
    if text == "strong":
        return 0.68
    if text == "steady":
        return 0.55
    if text == "weak":
        return 0.38
    return 0.48


def _normalize_horizon(value: Any) -> str:
    text = _text(value).lower()
    if text == "daytrade":
        return "daytrade"
    return "swing"


def _watchlist_items(briefing: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    watchlist_status = briefing.get("watchlist_status")
    if not isinstance(watchlist_status, list):
        return []

    items: list[Mapping[str, Any]] = []
    for item in watchlist_status:
        if isinstance(item, Mapping):
            items.append(item)
    return items


def _evidence_items(briefing: Mapping[str, Any]) -> list[dict[str, Any]]:
    evidence = briefing.get("evidence")
    if not isinstance(evidence, list):
        return []

    items: list[dict[str, Any]] = []
    for item in evidence:
        if isinstance(item, Mapping):
            items.append(dict(item))
    return items


def _candidate_sector(item: Mapping[str, Any]) -> str:
    sector = _text(item.get("sector"))
    if sector:
        return sector
    return _text(item.get("industry"))


def _sector_strength(briefing: Mapping[str, Any], sector: str) -> str:
    if not sector:
        return ""

    sector_rotation = briefing.get("sector_rotation")
    if isinstance(sector_rotation, Mapping):
        value = _text(sector_rotation.get(sector))
        if value:
            return value
        value = _text(sector_rotation.get(sector.lower()))
        if value:
            return value
        for key, raw_value in sector_rotation.items():
            if _text(key).lower() == sector.lower():
                value = _text(raw_value)
                if value:
                    return value
    elif isinstance(sector_rotation, list):
        for item in sector_rotation:
            if not isinstance(item, Mapping):
                continue
            entry_sector = _text(item.get("sector")) or _text(item.get("name"))
            if entry_sector and entry_sector.lower() == sector.lower():
                value = _text(item.get("strength")) or _text(item.get("state"))
                if value:
                    return value

    market_state = _text(briefing.get("market_state"))
    if market_state == "bullish":
        return "supported"
    if market_state == "bearish":
        return "weak"
    return ""


def _liquidity_state(item: Mapping[str, Any]) -> str:
    volume = _numeric(item.get("volume"))
    if volume is None:
        volume = _numeric(item.get("avg_volume"))
    if volume is None:
        volume = _numeric(item.get("average_volume"))
    if volume is None:
        return "unknown"
    if volume >= 1_000_000:
        return "high"
    if volume >= 200_000:
        return "medium"
    return "thin"


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    items: list[str] = []
    for item in value:
        text = _text(item)
        if text:
            items.append(text)
    return items


def _unique_short_list(values: list[str]) -> list[str]:
    unique: list[str] = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique[:4]


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _clamp(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value
