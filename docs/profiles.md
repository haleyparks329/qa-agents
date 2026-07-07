# Profiles

Profiles give the QA planner app context without hardcoding private repo details.

Each profile lives in `profiles/<name>.json` and includes:

- `name`
- `app_description`
- `key_user_flows`
- `risk_areas`
- `test_priorities`
- `constraints`

## Included profiles

### ecommerce

Use this profile for simulated storefront flows such as browsing, cart updates, promotions, checkout, and order confirmation.

Primary risks include pricing accuracy, checkout interruptions, inventory state, promotion edge cases, and mobile checkout behavior.

### saas_dashboard

Use this profile for simulated dashboards where users filter records, inspect metrics, export reports, or manage workspace settings.

Primary risks include role-based visibility, stale dashboard state, filter combinations, export formatting, and empty or error states.

## Adding a profile

1. Copy an existing JSON profile.
2. Rename it with a generic app category.
3. Replace user flows, risks, priorities, and constraints.
4. Run `pytest`.
5. Run a demo command with the new profile.

Profiles should not contain private company names, customer data, internal URLs, secrets, or production metrics.
