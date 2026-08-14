# Edge Cases: AI-Powered Restaurant Recommendation System

**Based on:** [problemstatement.md](./problemstatement.md) · [architecture.md](./architecture.md)

## Overview

This document lists detailed edge cases across all five architecture phases. Each case includes the scenario, expected system behavior, and severity.

| Severity | Meaning |
| --- | --- |
| Critical | Blocks recommendations or produces wrong/harmful output |
| High | Major UX or accuracy issue |
| Medium | Recoverable with degraded experience |
| Low | Minor inconsistency or polish issue |

---

## Phase 1: Data Ingestion

| ID | Scenario | Expected Behavior | Severity |
| --- | --- | --- | --- |
| DI-01 | Hugging Face dataset is unreachable or download fails | Show clear error; do not proceed to filtering/LLM | Critical |
| DI-02 | Dataset file is empty (0 rows) | Fail fast with “no restaurant data available” | Critical |
| DI-03 | Required columns missing (e.g., name, location, rating) | Reject load; report missing schema fields | Critical |
| DI-04 | Null / blank restaurant names | Drop or mark invalid; exclude from recommendations | High |
| DI-05 | Null location, cuisine, cost, or rating | Apply safe defaults or exclude from filters that need that field | High |
| DI-06 | Invalid rating values (negative, >5, non-numeric, “NEW”) | Normalize when possible; otherwise exclude from rating filters | High |
| DI-07 | Cost stored as text (`₹1,200`, `1200 for two`, empty) | Parse into comparable numeric/budget bands; skip unparseable rows from budget filter | High |
| DI-08 | Duplicate restaurant rows (same name + location) | Deduplicate before serving candidates | Medium |
| DI-09 | Inconsistent location naming (`Delhi`, `delhi`, `New Delhi`, `NCR`) | Normalize location keys for reliable filtering | High |
| DI-10 | Cuisine field contains multiple values (`Italian, Chinese`) or typos | Split multi-cuisine values; support fuzzy/normalized cuisine matching | Medium |
| DI-11 | Extremely large dataset causing slow load / memory pressure | Cache cleaned data; load once; optionally sample/index for filters | Medium |
| DI-12 | Special characters / encoding issues in names or cuisines | Preserve UTF-8; sanitize only unsafe control characters | Medium |
| DI-13 | Dataset schema changes upstream | Validate schema on load; fail with actionable message | High |

---

## Phase 2: User Input

| ID | Scenario | Expected Behavior | Severity |
| --- | --- | --- | --- |
| UI-01 | User submits with all fields empty | Block submit; show required-field validation | Critical |
| UI-02 | Location left blank but other fields filled | Require location (or define explicit “any location” behavior) | High |
| UI-03 | Location not present in dataset (e.g., `Goa` when data is city-limited) | Return “no restaurants found for this location” before LLM call | High |
| UI-04 | Location casing/spacing variants (`bangalore`, ` Bangaluru `) | Normalize input (trim, casefold, alias map) | High |
| UI-05 | Invalid budget value outside `{low, medium, high}` | Reject or map to nearest valid band | High |
| UI-06 | Minimum rating out of range (`-1`, `6`, `abc`) | Validate numeric range (e.g., 0–5); show inline error | High |
| UI-07 | Minimum rating with high precision (`4.75`) | Accept and compare correctly against dataset ratings | Medium |
| UI-08 | Cuisine not in dataset (`Ethiopian`) | Return empty/no-match message; do not invent restaurants | High |
| UI-09 | Multiple cuisines selected / comma-separated cuisine | Support OR/AND matching explicitly; document rule | Medium |
| UI-10 | Additional preferences empty | Treat as optional; proceed with structured filters only | Low |
| UI-11 | Very long additional preferences (thousands of characters) | Truncate with limit; warn user | Medium |
| UI-12 | Conflicting preferences (budget=low + luxury-only notes) | Still run pipeline; LLM should call out trade-offs in explanation | Medium |
| UI-13 | Contradictory filters (cuisine + location with zero intersection) | Stop after filtering with clear no-results message | High |
| UI-14 | Special characters / prompt-injection text in free-form preferences | Sanitize/escape before prompt assembly; never execute injected instructions | Critical |
| UI-15 | Rapid repeated submits | Debounce / disable button; avoid duplicate LLM calls | Medium |

---

## Phase 3: Integration Layer

| ID | Scenario | Expected Behavior | Severity |
| --- | --- | --- | --- |
| IL-01 | Filters return 0 candidates | Skip LLM; show “No restaurants match your preferences” with refine hints | Critical |
| IL-02 | Filters return exactly 1 candidate | Still call LLM for explanation, or show single result with reason | Medium |
| IL-03 | Filters return hundreds/thousands of matches | Cap shortlist (e.g., top N by rating/cost proximity) before prompting | High |
| IL-04 | Budget bands poorly aligned with cost distribution | Define explicit mapping (e.g., low/medium/high percentiles); document thresholds | High |
| IL-05 | Soft mismatch (close cuisine/location aliases) | Prefer normalized exact match first; optionally fuzzy expand | Medium |
| IL-06 | Rating filter removes all otherwise valid options | Inform user that rating threshold is too strict | High |
| IL-07 | Candidate fields missing when building prompt | Omit incomplete rows or fill with “unknown”; never send broken JSON | High |
| IL-08 | Prompt becomes too large for model context | Truncate candidates, summarize fields, or chunk ranking | Critical |
| IL-09 | Prompt missing ranking/explanation instructions | Enforce prompt template with required output schema | High |
| IL-10 | Additional preferences contradict filtered shortlist | Pass both; instruct LLM to note conflicts instead of fabricating fit | High |
| IL-11 | Unstable ordering of candidates across identical requests | Sort deterministically before prompt (e.g., rating desc, name) | Medium |
| IL-12 | Filter logic treats multi-cuisine restaurants incorrectly | Match if any listed cuisine matches user cuisine (unless AND mode) | High |

---

## Phase 4: Recommendation Engine (LLM)

| ID | Scenario | Expected Behavior | Severity |
| --- | --- | --- | --- |
| RE-01 | LLM API timeout / network failure | Retry with backoff; then show graceful fallback (filtered list without AI explanations) | Critical |
| RE-02 | LLM returns empty response | Fallback to deterministic ranking of filtered candidates | Critical |
| RE-03 | LLM returns malformed JSON / unparsable output | Re-prompt once for schema repair; else fallback ranking | Critical |
| RE-04 | LLM invents restaurants not in candidate list | Validate output against candidate IDs/names; drop hallucinations | Critical |
| RE-05 | LLM ranks restaurants that fail user filters | Post-validate each item against preferences before display | Critical |
| RE-06 | LLM returns fewer than requested top-N | Show available results; do not pad with fake entries | High |
| RE-07 | LLM returns duplicate restaurants | Deduplicate while preserving best rank/explanation | Medium |
| RE-08 | Missing explanations for some/all items | Show structured fields; use generic fallback reason if needed | High |
| RE-09 | Explanation ignores user preferences | Prefer regeneration or template reason tied to matched filters | Medium |
| RE-10 | LLM over-claims attributes not in data (e.g., “best rooftop”) | Constrain prompt to use only provided fields; strip unsupported claims when detectable | High |
| RE-11 | Optional summary missing | Still show ranked list; summary is non-blocking | Low |
| RE-12 | LLM rate limit / quota exceeded | Surface clear retry message; offer non-LLM filtered results | High |
| RE-13 | Non-deterministic rankings for same input | Accept variance within reason; optionally seed/temp=0 for demos | Medium |
| RE-14 | Unsafe or offensive content in free-form preference handling | Refuse unsafe requests; keep recommendations restaurant-focused | High |
| RE-15 | Very small candidate set with weak preference fit | Rank remaining options and explicitly state partial match | Medium |

---

## Phase 5: Output Display

| ID | Scenario | Expected Behavior | Severity |
| --- | --- | --- | --- |
| OD-01 | No recommendations to render | Show empty state with guidance to relax filters | High |
| OD-02 | Missing display field (rating/cost/cuisine null) | Show “N/A” or hide field gracefully; do not break layout | High |
| OD-03 | Extremely long restaurant name or explanation | Truncate with expand/read-more; preserve layout | Medium |
| OD-04 | Special characters / HTML in LLM explanation | Escape HTML; render as plain text | Critical |
| OD-05 | Ranking order disagrees with displayed score cues | Keep LLM order unless post-validation resorts; show clear rank | Medium |
| OD-06 | Only partial payload received from Phase 4 | Render available cards; log incomplete response | Medium |
| OD-07 | User changes preferences after results are shown | Clear old results on new search; avoid mixing sessions | High |
| OD-08 | Loading state while LLM is running | Show progress/spinner; disable duplicate submits | Medium |
| OD-09 | Mobile / narrow screens with long explanation text | Responsive layout; wrap text without overflow | Medium |
| OD-10 | Tie scores / equal suitability | Keep stable secondary sort; avoid jumpy reordering | Low |

---

## Cross-Phase / End-to-End Edge Cases

| ID | Scenario | Expected Behavior | Severity |
| --- | --- | --- | --- |
| E2E-01 | Phase 1 data not ready when user submits | Block search with “dataset loading” / retry state | Critical |
| E2E-02 | Preferences valid but all later phases fail | Preserve user input; show recoverable error | Critical |
| E2E-03 | Partial success: filters work, LLM fails | Show filtered restaurants without AI explanations | High |
| E2E-04 | User asks for “best” with no measurable criteria beyond defaults | Use rating/cost heuristics + LLM explanation of assumptions | Medium |
| E2E-05 | Same query repeated quickly | Cache recent filter+LLM result for short TTL | Medium |
| E2E-06 | Dataset refresh mid-session changes results | Version/cache snapshot for active request consistency | Medium |
| E2E-07 | Privacy: free-text preferences contain personal data | Avoid logging raw sensitive text; minimize retention | High |

---

## Suggested Handling Priority

1. **Must handle first:** DI-01–03, UI-01/14, IL-01/08, RE-01–05, OD-04, E2E-01–02  
2. **Should handle next:** empty/no-match paths, shortlist capping, schema validation, fallback ranking  
3. **Nice to have:** caching, fuzzy location/cuisine aliases, response summarization polish

## Test Checklist (Quick)

- [ ] Dataset load failure and empty dataset
- [ ] Missing/invalid preference combinations
- [ ] Zero-match and single-match filter results
- [ ] Oversized candidate shortlist / prompt truncation
- [ ] LLM timeout, malformed output, and hallucination rejection
- [ ] Empty-state and partial-field UI rendering
- [ ] Prompt-injection / unsafe free-text preferences
