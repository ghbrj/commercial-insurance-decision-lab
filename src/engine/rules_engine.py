"""Engine module: rules_engine (TASK-AGNOSTIC).

Contract (v0.2 plan §3): this module reads ONLY what task specs declare.
It must never reference property triage, NorthStar, or any specific task.
Fill in at the corresponding milestone:
  generate_corpus  -> M2   rules_engine      -> M3
  jev_client       -> M0/M4  runner          -> M0/M4
  metrics          -> M5
"""

