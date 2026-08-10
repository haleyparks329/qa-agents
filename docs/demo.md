# Little Bytes Pricing Investigation

Little Bytes is a deliberately small bakery application used to produce understandable QA evidence.

## Scenario

A pricing change alters how quantity and a percentage discount interact. Existing unit tests continue to pass because they do not cover that combination.

## Evidence

- the pricing behavior changed;
- the configured unit tests passed;
- the changed behavior had no direct regression evidence;
- no browser run, generated test, patch, or merge occurred.

## Investigation outcome

The result is **acted** because the available evidence supports recording a coverage gap and suggesting a narrow next action. The suggestion is to add a human-reviewed regression example for quantity plus discount behavior.

If the test artifact had been missing, the investigation would be **blocked**. If the requested action required authority outside the role, it would **abstain**.

The [static artifact](../examples/demo-runs/little-bytes-pricing.json) is deliberately not a stable schema or runtime export contract.
