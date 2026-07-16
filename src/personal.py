"""Personal AI helpers for AlphaOS."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypedDict


class PersonalProfile(TypedDict, total=False):
    holdings: list[str]
    investment_period: str
    risk_tolerance: str
    style: str
    interested_markets: list[str]


def normalize_personal_profile(payload: Mapping[str, Any] | None) -> PersonalProfile:
    if not isinstance(payload, Mapping):
        return {}

    profile: PersonalProfile = {}
    holdings = _string_list(payload.get("holdings"))
    if holdings:
        profile["holdings"] = holdings
    period = _text(payload.get("investment_period"))
    if period:
        profile["investment_period"] = period
    risk_tolerance = _text(payload.get("risk_tolerance"))
    if risk_tolerance:
        profile["risk_tolerance"] = risk_tolerance
    style = _text(payload.get("style"))
    if style:
        profile["style"] = style
    markets = _string_list(payload.get("interested_markets"))
    if markets:
        profile["interested_markets"] = markets
    return profile


def personalize_candidates(
    candidates: list[Mapping[str, Any]],
    profile: Mapping[str, Any] | None,
) -> dict[str, Any]:
    normalized = normalize_personal_profile(profile)
    if not normalized:
        return {"profile": {}, "candidates": list(candidates), "notes": ["No personal profile provided."]}

    filtered: list[dict[str, Any]] = []
    notes: list[str] = []
    holdings = {item.upper() for item in normalized.get("holdings", [])}
    style = _text(normalized.get("style")).lower()
    risk_tolerance = _text(normalized.get("risk_tolerance")).lower()
    markets = {item.lower() for item in normalized.get("interested_markets", [])}
    investment_period = _text(normalized.get("investment_period")).lower()

    for candidate in candidates:
        symbol = _text(candidate.get("symbol")).upper()
        adjusted = dict(candidate)
        if symbol in holdings:
            notes.append(f"{symbol} is already held, so it is de-emphasized.")
            continue
        if style == "daytrade" and _text(candidate.get("horizon")) != "daytrade":
            continue
        if style == "longterm" and _text(candidate.get("horizon")) == "daytrade":
            continue
        if risk_tolerance == "low" and _text(candidate.get("confidence")) == "low":
            continue
        if investment_period in {"short", "intraday"} and _text(candidate.get("horizon")) == "long":
            continue
        if markets:
            sector = _text(candidate.get("sector")).lower()
            if sector and sector not in markets:
                notes.append(f"{symbol} is outside the preferred market set.")
                continue
        adjusted["personalized_score"] = _personalized_score(adjusted, normalized)
        adjusted["personalization_notes"] = _personalization_notes(adjusted, normalized)
        filtered.append(adjusted)

    if not filtered:
        filtered = [dict(candidate) for candidate in candidates[:1]]
        if filtered:
            notes.append("Profile filters were strict, so the top candidate was kept as a fallback.")

    for candidate in filtered:
        if "personalized_score" not in candidate:
            candidate["personalized_score"] = _personalized_score(candidate, normalized)
        if holdings and _text(candidate.get("symbol")).upper() in holdings:
            candidate["note"] = "Already held; keep only if portfolio context changes."

    filtered.sort(
        key=lambda candidate: (
            float(candidate.get("personalized_score", candidate.get("score", 0.0))),
            float(candidate.get("score", 0.0)),
        ),
        reverse=True,
    )

    return {
        "profile": normalized,
        "candidates": filtered,
        "notes": _unique_short_list(notes),
    }


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _text(item)
        if text:
            items.append(text)
    return items


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _unique_short_list(values: list[str]) -> list[str]:
    unique: list[str] = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique[:4]


def _numeric(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return default
    return default


def _personalized_score(candidate: Mapping[str, Any], profile: Mapping[str, Any]) -> float:
    score = _numeric(candidate.get("score"), 0.0)
    horizon = _text(candidate.get("horizon")).lower()
    style = _text(profile.get("style")).lower()
    investment_period = _text(profile.get("investment_period")).lower()
    confidence = _text(candidate.get("confidence")).lower()
    sector = _text(candidate.get("sector")).lower()
    markets = {item.lower() for item in _string_list(profile.get("interested_markets"))}
    holdings = {item.upper() for item in _string_list(profile.get("holdings"))}
    symbol = _text(candidate.get("symbol")).upper()

    if style == "daytrade":
        score += 0.04 if horizon == "daytrade" else -0.02
    elif style == "longterm":
        score += 0.04 if horizon == "long" else -0.01

    if investment_period in {"short", "intraday"}:
        score += 0.03 if horizon == "daytrade" else -0.01
    elif investment_period in {"long", "multi_year"}:
        score += 0.03 if horizon == "long" else -0.01

    if confidence == "high":
        score += 0.01
    elif confidence == "low" and _text(profile.get("risk_tolerance")).lower() == "low":
        score -= 0.02

    if markets and sector and sector in markets:
        score += 0.03

    if holdings and symbol in holdings:
        score -= 0.05

    return round(score, 4)


def _personalization_notes(candidate: Mapping[str, Any], profile: Mapping[str, Any]) -> list[str]:
    notes: list[str] = []
    horizon = _text(candidate.get("horizon")).lower()
    style = _text(profile.get("style")).lower()
    investment_period = _text(profile.get("investment_period")).lower()
    if style == "daytrade" and horizon == "daytrade":
        notes.append("Matches the requested daytrade style.")
    elif style == "longterm" and horizon == "long":
        notes.append("Matches the requested long-term style.")
    if investment_period in {"short", "intraday"} and horizon == "daytrade":
        notes.append("Fits the requested short holding period.")
    if investment_period in {"long", "multi_year"} and horizon == "long":
        notes.append("Fits the requested long holding period.")
    sector = _text(candidate.get("sector"))
    markets = {item.lower() for item in _string_list(profile.get("interested_markets"))}
    if sector and sector.lower() in markets:
        notes.append(f"{sector} matches the preferred market set.")
    return _unique_short_list(notes)
