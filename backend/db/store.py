"""Phase-1 in-memory store — dicts in the wire shapes from CONTRACTS §3-§4. Owner: C (Seb).

Routes read/write these directly so the full API runs end-to-end on fake data with no
Atlas dependency (PARALLEL_IMPLEMENTATION_PLAN Phase 1). Phase 2 swaps the internals for
db/mongo.py persistence behind the same route code paths.

Keys: TESTS by test id, VARIANTS by variant id, SCORES by *variant* id (one score per
variant), USERS by user id.
"""
TESTS: dict[str, dict] = {}
VARIANTS: dict[str, dict] = {}
SCORES: dict[str, dict] = {}
USERS: dict[str, dict] = {}
