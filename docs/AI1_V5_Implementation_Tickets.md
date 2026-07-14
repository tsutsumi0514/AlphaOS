# AlphaOS V5 Implementation Tickets

## Scope
V5 is Market Memory. Start with realistic, measurable, evidence-based features only.

## V5-01
- **Title**: MemoryRecord schema
- **Purpose**: Define one stable record format for briefing, evidence, confidence, risk, outcome, and timestamps.
- **Dependencies**: None
- **Done**: A MemoryRecord model exists, is documented, and is covered by validation tests.
- **Priority**: High

## V5-02
- **Title**: Convert briefing history into MemoryRecord
- **Purpose**: Preserve existing briefing history by converting it into the new memory format.
- **Dependencies**: V5-01
- **Done**: Existing briefing snapshots can be stored as MemoryRecord without breaking current /briefing output.
- **Priority**: High

## V5-03
- **Title**: Rule-based market regime classifier
- **Purpose**: Tag each record with a simple regime such as risk_on, risk_off, strong_yen, weak_yen, rising_market, falling_market.
- **Dependencies**: V5-01
- **Done**: Regime tags are derived from current signals using explicit rules and unit tests.
- **Priority**: High

## V5-04
- **Title**: Similar memory search
- **Purpose**: Find the top similar past cases for the current briefing using explainable weighted scoring.
- **Dependencies**: V5-01, V5-03
- **Done**: The system returns similar_cases, similarity_score, common_factors, different_factors, and a low-confidence result when matches are weak.
- **Priority**: High

## V5-05
- **Title**: Outcome linkage
- **Purpose**: Attach later market outcomes to saved memory records so past cases can be judged against reality.
- **Dependencies**: V5-01
- **Done**: Records can store follow-up outcomes for next-day, 5-day, and 20-day checks.
- **Priority**: Medium

## V5-06
- **Title**: Optional memory_context in /briefing
- **Purpose**: Add memory as supporting context without changing the existing briefing contract.
- **Dependencies**: V5-04, V5-05
- **Done**: /briefing can include memory_context optionally, while old fields remain unchanged.
- **Priority**: Medium

## V5-07
- **Title**: V5 evidence and safety tests
- **Purpose**: Ensure memory never uses future data and never overrides current evidence.
- **Dependencies**: V5-01, V5-04, V5-06
- **Done**: Tests cover no-future-info, stable similarity, no-match behavior, and backward compatibility.
- **Priority**: High

## Deferred to V5.5
- A/B comparison between memory-aware and memory-free decisions
- /memory/{id} detail API
- /memory/compare API
- more advanced comparison analytics

## Implementation order
1. V5-01
2. V5-02
3. V5-03
4. V5-04
5. V5-05
6. V5-06
7. V5-07

## Notes for AI1
- Keep briefing.py as orchestration only.
- Do not add heavy AI or vector DB logic in V5.
- Preserve backward compatibility of /briefing.
- Evidence, Confidence, Risk, and human final judgment must remain intact.
