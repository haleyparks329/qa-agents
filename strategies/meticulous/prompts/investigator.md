# Investigator Strategy Notes

Compare base and head replay evidence and classify each derived finding as one
of:

- expected_change
- confirmed_regression
- likely_regression
- environment_or_replay_issue
- insufficient_evidence

Every finding must cite session IDs, diff IDs, branch IDs when available, and
workflow cluster IDs. Raw replay evidence is immutable; investigation outputs
are derived records.
