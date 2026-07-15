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
        filtered.append(dict(candidate))

    if not filtered:
        filtered = [dict(candidate) for candidate in candidates[:1]]
        if filtered:
            notes.append("Profile filters were strict, so the top candidate was kept as a fallback.")

    for candidate in filtered:
        if holdings and _text(candidate.get("symbol")).upper() in holdings:
            candidate["note"] = "Already held; keep only if portfolio context changes."

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
