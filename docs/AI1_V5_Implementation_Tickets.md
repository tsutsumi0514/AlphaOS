# AlphaOS V5 Implementation Tickets

## Scope
V5 is the Opportunity Engine. The goal is to turn the existing evidence, confidence, and risk stack into ranked buy candidates with entry timing hints.

## V5-01
- **Title**: OpportunityCandidate schema
- **Purpose**: Define one stable record format for candidate symbol, horizon, score, confidence, evidence, risk, and entry timing.
- **Dependencies**: None
- **Done**: A candidate model exists, is documented, and is covered by validation tests.
- **Priority**: High

## V5-02
- **Title**: Candidate scoring from current decision stack
- **Purpose**: Convert Evidence, Confidence, RiskAI, and ChairmanAI output into one candidate score.
- **Dependencies**: V5-01
- **Done**: The system can produce a candidate score from current briefing data without breaking `/briefing`.
- **Priority**: High

## V5-03
- **Title**: Candidate ranking
- **Purpose**: Rank one or more buy candidates using the shared candidate score and explain why the top item won.
- **Dependencies**: V5-01, V5-02
- **Done**: The system returns a sorted candidate list with reasons, risk notes, and a short entry reason.
- **Priority**: High

## V5-04
- **Title**: Entry timing hint
- **Purpose**: Add a minimal entry timing hint based on current signals, while keeping the logic simple and explainable.
- **Dependencies**: V5-01, V5-02
- **Done**: The system returns a short entry timing recommendation such as `buy_now`, `wait`, or `avoid`.
- **Priority**: Medium

## V5-05
- **Title**: Mode split for swing and day-trade
- **Purpose**: Prepare a shared core that can branch into swing-trade and day-trade outputs without duplicating the data collection layer.
- **Dependencies**: V5-01, V5-03
- **Done**: The system can label a candidate as swing or day-trade oriented and apply a stricter day-trade liquidity filter.
- **Priority**: Medium

## V5-06
- **Title**: Candidate output API and presenter hook
- **Purpose**: Expose the opportunity output through a separate endpoint or presenter path while keeping `/briefing` backward compatible.
- **Dependencies**: V5-03, V5-04, V5-05
- **Done**: A candidate-oriented output is reachable without changing the current briefing contract.
- **Priority**: Medium

## V5-07
- **Title**: Opportunity Engine safety tests
- **Purpose**: Protect backward compatibility and ensure candidate ranking stays explainable and evidence-based.
- **Dependencies**: V5-01, V5-03, V5-06
- **Done**: Tests cover schema stability, ranking order, filtering, backward compatibility, and no auto-trading behavior.
- **Priority**: High

## Deferred to V6
- Market Memory
- similar-case retrieval
- outcome linkage for historical candidate comparisons

## Implementation order
1. V5-01
2. V5-02
3. V5-03
4. V5-04
5. V5-05
6. V5-06
7. V5-07

## Notes for AI1
- Keep `briefing.py` as orchestration only.
- Do not put heavy analysis inside `briefing.py`.
- Preserve `/briefing` backward compatibility.
- Keep Evidence, Confidence, Risk, and human final judgment intact.
- Use the current V4 decision stack as the source of truth for candidate generation.
