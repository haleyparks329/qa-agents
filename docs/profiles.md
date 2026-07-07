# Profiles

Profiles give agents app context without hardcoding private repo details.

## Implemented Format

Each profile can live at:

```text
profiles/<name>/profile.json
profiles/<name>/house-rules.md
```

The package also still reads the earlier flat JSON files, such as `profiles/ecommerce.json`, so the existing CLI demo remains compatible.

Required fields:

- `name`
- `app_description`
- `key_user_flows`
- `risk_areas`
- `test_priorities`
- `constraints`

Optional structured fields used by `profile.py`:

- `repo_name`
- `repo_root`
- `test_layout`
- `tools`
- `issue_tracker`

## Included Profiles

### ecommerce

Generic simulated storefront context: catalog, cart, promotion, checkout, and order confirmation flows.

### saas_dashboard

Generic simulated dashboard context: role visibility, metrics, filters, exports, settings, empty states, and refresh behavior.

## Commands

```bash
python3 profile.py list
python3 profile.py --profile ecommerce show
python3 profile.py --profile ecommerce agent-context herbie
python3 profile.py --profile ecommerce get issue_tracker.ticket_prefixes
python3 profile.py --profile ecommerce resolve-path test_layout.e2e
```

## Guardrails

Profiles should not contain private company names, customer data, internal URLs, secrets, or production metrics.
