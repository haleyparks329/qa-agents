from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STRATEGIES_DIR = PROJECT_ROOT / "strategies"


class StrategyError(ValueError):
    """Raised when a QA strategy or replay evidence artifact is invalid."""


@dataclass(frozen=True)
class QualityStrategy:
    id: str
    name: str
    version: int
    description: str
    disclaimer: str
    quality_model: str
    operating_principles: list[str]
    primary_evidence: list[str]
    outputs: list[str]
    root: Path


@dataclass(frozen=True)
class StrategyRegistry:
    root: Path = DEFAULT_STRATEGIES_DIR

    def available(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(
            path.name for path in self.root.iterdir() if (path / "strategy.yaml").exists()
        )

    def strategy_path(self, name: str) -> Path:
        return self.root / name / "strategy.yaml"


@dataclass(frozen=True)
class ClassificationRule:
    classification: str
    diff_type: str | None = None
    expected: bool | None = None
    severity: str | None = None
    expectation_required: bool = False


@dataclass(frozen=True)
class StrategyBehavior:
    clustering_features: list[str]
    classification_rules: list[ClassificationRule]
    summary_next_actions: list[str]


@dataclass(frozen=True)
class WorkflowCluster:
    cluster_id: str
    name: str
    session_ids: list[str]
    shared_routes: list[str]
    shared_branches: list[str]
    shared_differences: list[str]
    evidence_refs: list[str]
    confidence: float


@dataclass(frozen=True)
class DifferenceFinding:
    finding_id: str
    classification: str
    summary: str
    session_ids: list[str]
    diff_ids: list[str]
    diff_types: list[str]
    branch_ids: list[str]
    workflow_cluster_ids: list[str]


@dataclass(frozen=True)
class CoverageFinding:
    uncovered_changed_branches: list[str] = field(default_factory=list)
    missing_workflows: list[str] = field(default_factory=list)
    coverage_risk: str = "low"


@dataclass(frozen=True)
class PolicyDecision:
    decision: str
    matched_rule: str
    priority: str
    metrics: dict[str, Any]


@dataclass(frozen=True)
class InvestigationResult:
    case_id: str
    source: dict[str, Any]
    change: dict[str, Any]
    replay_summary: dict[str, Any]
    workflow_clusters: list[WorkflowCluster]
    findings: list[DifferenceFinding]
    coverage_audit: CoverageFinding
    strategy: dict[str, Any] | None = None
    policy_decision: PolicyDecision | None = None
    human_decision_required: bool = True
    summary: dict[str, Any] | None = None


def available_strategies(strategies_dir: Path = DEFAULT_STRATEGIES_DIR) -> list[str]:
    return StrategyRegistry(strategies_dir).available()


def load_strategy(
    name: str, strategies_dir: Path = DEFAULT_STRATEGIES_DIR
) -> QualityStrategy:
    registry = StrategyRegistry(strategies_dir)
    path = registry.strategy_path(name)
    if not path.exists():
        known = ", ".join(registry.available()) or "none"
        raise StrategyError(f"Unknown strategy '{name}'. Available strategies: {known}.")

    data = _parse_simple_yaml(path)
    required = {
        "id",
        "name",
        "version",
        "description",
        "disclaimer",
        "quality_model",
        "operating_principles",
        "primary_evidence",
        "outputs",
    }
    missing = sorted(required - set(data))
    if missing:
        raise StrategyError(f"Strategy '{name}' is missing fields: {', '.join(missing)}.")

    if data["id"] != name:
        raise StrategyError(f"Strategy id '{data['id']}' does not match directory '{name}'.")

    return QualityStrategy(
        id=str(data["id"]),
        name=str(data["name"]),
        version=int(data["version"]),
        description=str(data["description"]),
        disclaimer=str(data["disclaimer"]),
        quality_model=str(data["quality_model"]),
        operating_principles=_string_list(data["operating_principles"], "operating_principles"),
        primary_evidence=_string_list(data["primary_evidence"], "primary_evidence"),
        outputs=_string_list(data["outputs"], "outputs"),
        root=path.parent,
    )


def load_policy(strategy: QualityStrategy) -> dict[str, Any]:
    path = strategy.root / "decision-policy.yaml"
    if not path.exists():
        raise StrategyError(f"Strategy '{strategy.id}' has no decision-policy.yaml.")
    text = path.read_text(encoding="utf-8").lstrip()
    if text.startswith("{"):
        return json.loads(text)
    return _parse_simple_yaml(path)


def load_behavior(strategy: QualityStrategy) -> StrategyBehavior:
    policy = load_policy(strategy)
    return StrategyBehavior(
        clustering_features=_string_list(
            policy.get("clustering", {}).get(
                "features", ["workflow_hint", "route_sequence"]
            ),
            "clustering.features",
        ),
        classification_rules=[
            ClassificationRule(
                classification=str(rule["classification"]),
                diff_type=rule.get("diff_type"),
                expected=rule.get("expected"),
                severity=rule.get("severity"),
                expectation_required=bool(rule.get("expectation_required", False)),
            )
            for rule in policy.get("classification_rules", [])
        ],
        summary_next_actions=_string_list(
            policy.get("summary", {}).get("next_actions", []),
            "summary.next_actions",
        ),
    )


def load_evidence(path: str | Path) -> dict[str, Any]:
    evidence_path = Path(path)
    try:
        data = json.loads(evidence_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StrategyError(
            f"Invalid JSON in evidence file '{evidence_path}': line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(data, dict):
        raise StrategyError(f"Evidence file '{evidence_path}' must contain a JSON object.")
    return data


def validate_replay_evidence(evidence: dict[str, Any], strategy_id: str) -> list[str]:
    errors: list[str] = []
    for field_name in ("case_id", "source", "change", "replay_summary", "sessions"):
        if field_name not in evidence:
            errors.append(f"missing top-level field: {field_name}")

    source = evidence.get("source", {})
    if not isinstance(source, dict):
        errors.append("source must be an object")
        source = {}
    if source.get("strategy") != strategy_id:
        errors.append("source.strategy must match the selected strategy")
    if source.get("type") != "simulated_replay_platform":
        errors.append("source.type must be simulated_replay_platform")
    if source.get("simulated") is not True:
        errors.append("source.simulated must be true")

    change = evidence.get("change", {})
    if not isinstance(change, dict):
        errors.append("change must be an object")
    replay_summary = evidence.get("replay_summary", {})
    if not isinstance(replay_summary, dict):
        errors.append("replay_summary must be an object")

    sessions = evidence.get("sessions", [])
    if not isinstance(sessions, list):
        errors.append("sessions must be a list")
        return errors

    seen_sessions: set[str] = set()
    for index, session in enumerate(sessions):
        if not isinstance(session, dict):
            errors.append(f"sessions[{index}] must be an object")
            continue
        session_id = session.get("session_id")
        if not session_id:
            errors.append(f"sessions[{index}] missing session_id")
            continue
        if session_id in seen_sessions:
            errors.append(f"duplicate session_id: {session_id}")
        seen_sessions.add(session_id)
        if "workflow_hint" not in session:
            errors.append(f"{session_id} missing workflow_hint")
        if "route_sequence" not in session:
            errors.append(f"{session_id} missing route_sequence")
        differences = session.get("differences", [])
        if not isinstance(differences, list):
            errors.append(f"{session_id} differences must be a list")
            continue
        for diff_index, diff in enumerate(differences):
            if not isinstance(diff, dict):
                errors.append(f"{session_id} differences[{diff_index}] must be an object")
                continue
            if not diff.get("diff_id"):
                errors.append(f"{session_id} differences[{diff_index}] missing diff_id")
            if diff.get("deterministic") is not True:
                errors.append(f"{session_id} differences[{diff_index}] is not deterministic")

    return errors


def cluster_workflows(
    evidence: dict[str, Any], behavior: StrategyBehavior | None = None
) -> list[WorkflowCluster]:
    behavior = behavior or StrategyBehavior(
        clustering_features=["workflow_hint", "route_sequence"],
        classification_rules=[],
        summary_next_actions=[],
    )
    buckets: dict[tuple[str, tuple[str, ...]], list[dict[str, Any]]] = {}
    for session in affected_sessions(evidence):
        key = _cluster_key(session, behavior.clustering_features)
        buckets.setdefault(key, []).append(session)

    clusters: list[WorkflowCluster] = []
    for key, sessions in sorted(buckets.items()):
        workflow_slug = key[0]
        session_ids = sorted(str(session["session_id"]) for session in sessions)
        route_sets = [set(session.get("route_sequence", [])) for session in sessions]
        branch_sets = [set(session.get("covered_branches", [])) for session in sessions]
        diff_sets = [
            {
                _difference_signature(diff)
                for diff in session.get("differences", [])
                if diff.get("deterministic") is True
            }
            for session in sessions
        ]
        first_hint = str(sessions[0].get("workflow_hint", workflow_slug)).strip()
        clusters.append(
            WorkflowCluster(
                cluster_id=f"workflow-{workflow_slug}",
                name=first_hint[:1].upper() + first_hint[1:],
                session_ids=session_ids,
                shared_routes=sorted(set.intersection(*route_sets)) if route_sets else [],
                shared_branches=sorted(set.intersection(*branch_sets)) if branch_sets else [],
                shared_differences=sorted(set.intersection(*diff_sets)) if diff_sets else [],
                evidence_refs=session_ids,
                confidence=round(_cluster_confidence(sessions), 2),
            )
        )
    return clusters


def investigate_replay_evidence(
    evidence: dict[str, Any], behavior: StrategyBehavior | None = None
) -> InvestigationResult:
    behavior = behavior or StrategyBehavior(
        clustering_features=["workflow_hint", "route_sequence"],
        classification_rules=[],
        summary_next_actions=[],
    )
    clusters = cluster_workflows(evidence, behavior)
    cluster_by_session = {
        session_id: cluster.cluster_id
        for cluster in clusters
        for session_id in cluster.session_ids
    }
    findings = classify_differences(evidence, cluster_by_session, behavior)
    coverage = audit_coverage(evidence)
    return InvestigationResult(
        case_id=str(evidence["case_id"]),
        source=evidence["source"],
        change=evidence["change"],
        replay_summary=evidence["replay_summary"],
        workflow_clusters=clusters,
        findings=findings,
        coverage_audit=coverage,
    )


def classify_differences(
    evidence: dict[str, Any],
    cluster_by_session: dict[str, str],
    behavior: StrategyBehavior | None = None,
) -> list[DifferenceFinding]:
    behavior = behavior or StrategyBehavior(
        clustering_features=["workflow_hint", "route_sequence"],
        classification_rules=[],
        summary_next_actions=[],
    )
    groups: dict[tuple[str, str, str], dict[str, set[str]]] = {}
    summaries: dict[tuple[str, str, str], str] = {}

    for session in affected_sessions(evidence):
        session_id = str(session["session_id"])
        for diff in session.get("differences", []):
            if diff.get("deterministic") is not True:
                continue
            classification = _classify_difference(
                diff,
                evidence.get("known_expectations", []),
                behavior.classification_rules,
            )
            root = str(diff.get("root_cause_candidate") or diff.get("location") or "unknown")
            if classification == "expected_change" and diff.get("expectation_id"):
                root = str(diff["expectation_id"])
            key = (
                classification,
                root,
                str(diff.get("type", "unknown")),
            )
            bucket = groups.setdefault(
                key,
                {
                    "session_ids": set(),
                    "diff_ids": set(),
                    "diff_types": set(),
                    "branch_ids": set(),
                    "cluster_ids": set(),
                },
            )
            bucket["session_ids"].add(session_id)
            bucket["diff_ids"].add(str(diff["diff_id"]))
            bucket["diff_types"].add(str(diff.get("type", "unknown")))
            bucket["branch_ids"].update(str(branch) for branch in diff.get("branch_refs", []))
            bucket["cluster_ids"].add(cluster_by_session[session_id])
            summaries[key] = str(diff.get("summary") or diff.get("location") or key[1])

    findings: list[DifferenceFinding] = []
    for index, (key, refs) in enumerate(sorted(groups.items()), start=1):
        classification, root, diff_type = key
        findings.append(
            DifferenceFinding(
                finding_id=f"finding-{index:03d}",
                classification=classification,
                summary=summaries[key],
                session_ids=sorted(refs["session_ids"]),
                diff_ids=sorted(refs["diff_ids"]),
                diff_types=sorted(refs["diff_types"]),
                branch_ids=sorted(refs["branch_ids"]),
                workflow_cluster_ids=sorted(refs["cluster_ids"]),
            )
        )
    return findings


def audit_coverage(evidence: dict[str, Any]) -> CoverageFinding:
    changed_branches = set(evidence.get("change", {}).get("changed_branches", []))
    covered_branches: set[str] = set()
    for session in evidence.get("sessions", []):
        covered_branches.update(str(branch) for branch in session.get("covered_branches", []))

    uncovered = sorted(changed_branches - covered_branches)
    branch_expectations = evidence.get("coverage", {}).get("branch_expectations", {})
    missing = [
        str(branch_expectations.get(branch, branch)).strip()
        for branch in uncovered
    ]
    risk = "high" if uncovered else "low"
    if evidence.get("replay_summary", {}).get("sessions_selected", 0) == 0:
        risk = "high"
    elif uncovered and len(uncovered) == 1:
        risk = "medium"

    return CoverageFinding(
        uncovered_changed_branches=uncovered,
        missing_workflows=missing,
        coverage_risk=risk,
    )


def apply_decision_policy(
    investigation: InvestigationResult, policy: dict[str, Any]
) -> PolicyDecision:
    metrics = _policy_metrics(investigation)
    priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
    matched: list[dict[str, Any]] = []
    for rule in policy.get("rules", []):
        if _rule_matches(rule.get("when", {}), metrics):
            matched.append(rule)

    if not matched:
        return PolicyDecision(
            decision="requires_human_review",
            matched_rule="no-policy-rule-matched",
            priority="high",
            metrics=metrics,
        )

    selected = sorted(
        matched, key=lambda rule: priority_order.get(str(rule.get("priority", "normal")), 2)
    )[0]
    return PolicyDecision(
        decision=str(selected["decision"]),
        matched_rule=str(selected["id"]),
        priority=str(selected.get("priority", "normal")),
        metrics=metrics,
    )


def run_investigation(
    strategy_name: str,
    input_path: str | Path,
    strategies_dir: Path = DEFAULT_STRATEGIES_DIR,
) -> dict[str, Any]:
    return investigation_to_dict(
        run_investigation_result(strategy_name, input_path, strategies_dir)
    )


def run_investigation_result(
    strategy_name: str,
    input_path: str | Path,
    strategies_dir: Path = DEFAULT_STRATEGIES_DIR,
) -> InvestigationResult:
    strategy = load_strategy(strategy_name, strategies_dir)
    behavior = load_behavior(strategy)
    policy = load_policy(strategy)
    evidence = load_evidence(input_path)
    errors = validate_replay_evidence(evidence, strategy.id)
    if errors:
        formatted_errors = "\n  - ".join(errors)
        raise StrategyError(f"Invalid evidence for strategy '{strategy.id}':\n  - {formatted_errors}")
    investigation = investigate_replay_evidence(evidence, behavior)
    policy_decision = apply_decision_policy(investigation, policy)
    strategy_summary = {
        "id": strategy.id,
        "name": strategy.name,
        "version": strategy.version,
        "disclaimer": strategy.disclaimer,
    }
    summary = summarize_investigation(
        investigation,
        policy_decision,
        behavior.summary_next_actions,
    )
    return InvestigationResult(
        case_id=investigation.case_id,
        source=investigation.source,
        change=investigation.change,
        replay_summary=investigation.replay_summary,
        workflow_clusters=investigation.workflow_clusters,
        findings=investigation.findings,
        coverage_audit=investigation.coverage_audit,
        strategy=strategy_summary,
        policy_decision=policy_decision,
        human_decision_required=True,
        summary=summary,
    )


def summarize_investigation(
    investigation: InvestigationResult,
    policy_decision: PolicyDecision,
    next_actions: list[str],
) -> dict[str, Any]:
    findings = investigation.findings
    expected = [item for item in findings if item.classification == "expected_change"]
    regressions = [
        item for item in findings if item.classification == "confirmed_regression"
    ]
    return {
        "affected_workflows": len(investigation.workflow_clusters),
        "expected_changes": len(expected),
        "confirmed_regressions": len(regressions),
        "coverage_gaps": len(investigation.coverage_audit.uncovered_changed_branches),
        "recommendation": policy_decision.decision,
        "next_actions": next_actions,
    }


def affected_sessions(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        session
        for session in evidence.get("sessions", [])
        if session.get("differences") or session.get("visual_diff", {}).get("present")
    ]


def investigation_to_dict(investigation: InvestigationResult) -> dict[str, Any]:
    if investigation.policy_decision is None:
        raise StrategyError("Cannot serialize investigation before policy decision is set.")
    if investigation.summary is None:
        raise StrategyError("Cannot serialize investigation before summary is set.")
    return {
        "case_id": investigation.case_id,
        "source": investigation.source,
        "change": investigation.change,
        "replay_summary": investigation.replay_summary,
        "workflow_clusters": [
            _dataclass_dict(cluster) for cluster in investigation.workflow_clusters
        ],
        "findings": [_dataclass_dict(finding) for finding in investigation.findings],
        "coverage_audit": _dataclass_dict(investigation.coverage_audit),
        "strategy": investigation.strategy,
        "policy_decision": _dataclass_dict(investigation.policy_decision),
        "human_decision_required": investigation.human_decision_required,
        "summary": investigation.summary,
    }


def _classify_difference(
    diff: dict[str, Any],
    expectations: list[dict[str, Any]],
    rules: list[ClassificationRule],
) -> str:
    for rule in rules:
        if rule.diff_type is not None and diff.get("type") != rule.diff_type:
            continue
        if rule.expected is not None and diff.get("expected") is not rule.expected:
            continue
        if rule.severity is not None and diff.get("severity") != rule.severity:
            continue
        if rule.expectation_required and not _has_known_expectation(diff, expectations):
            continue
        return rule.classification
    return "insufficient_evidence"


def _has_known_expectation(diff: dict[str, Any], expectations: list[dict[str, Any]]) -> bool:
    if diff.get("expected") is True:
        return True
    return any(
        diff.get("expectation_id") and diff.get("expectation_id") == expectation.get("id")
        for expectation in expectations
    )


def _policy_metrics(investigation: InvestigationResult) -> dict[str, Any]:
    findings = investigation.findings
    confirmed = [item for item in findings if item.classification == "confirmed_regression"]
    expected = [item for item in findings if item.classification == "expected_change"]
    visual_diff_ids = {
        diff_id
        for finding in findings
        if "visual" in finding.diff_types
        for diff_id in finding.diff_ids
    }
    expected_diff_ids = {
        diff_id for finding in expected for diff_id in finding.diff_ids
    }
    coverage = investigation.coverage_audit
    replay_summary = investigation.replay_summary
    selected = int(replay_summary.get("sessions_selected", 0))
    affected = int(replay_summary.get("sessions_affected", 0))
    completeness = 1.0 if selected else 0.0
    if affected and len(investigation.workflow_clusters) == 0:
        completeness = 0.0

    return {
        "confirmed_regressions": len(confirmed),
        "functional_regressions": len(confirmed),
        "uncovered_changed_branches": len(coverage.uncovered_changed_branches),
        "all_visual_differences_expected": bool(visual_diff_ids)
        and visual_diff_ids.issubset(expected_diff_ids),
        "coverage_risk": coverage.coverage_risk,
        "evidence_completeness": completeness,
    }


def _rule_matches(conditions: dict[str, Any], metrics: dict[str, Any]) -> bool:
    for key, expected in conditions.items():
        if key.endswith("_min"):
            metric_key = key.removesuffix("_min")
            if metrics.get(metric_key, 0) < expected:
                return False
        elif key.endswith("_below"):
            metric_key = key.removesuffix("_below")
            if metrics.get(metric_key, 0) >= expected:
                return False
        elif metrics.get(key) != expected:
            return False
    return True


def _difference_signature(diff: dict[str, Any]) -> str:
    if diff.get("root_cause_candidate"):
        return f"{diff.get('type', 'unknown')}|{diff['root_cause_candidate']}"
    return "|".join(
        [
            str(diff.get("type", "unknown")),
            str(diff.get("location", "unknown")),
            str(diff.get("base_value", "")),
            str(diff.get("head_value", "")),
        ]
    )


def _cluster_key(session: dict[str, Any], features: list[str]) -> tuple[str, tuple[str, ...]]:
    workflow_slug = _slug(str(session.get("workflow_hint", "unknown-workflow")))
    parts: list[str] = []
    for feature in features:
        value = session.get(feature)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif value is not None:
            parts.append(str(value))
    return (workflow_slug, tuple(parts))


def _cluster_confidence(sessions: list[dict[str, Any]]) -> float:
    if not sessions:
        return 0.0
    route_sequences = {tuple(session.get("route_sequence", [])) for session in sessions}
    labels = {str(session.get("workflow_hint", "")) for session in sessions}
    base = 0.7
    if len(route_sequences) == 1:
        base += 0.15
    if len(labels) == 1:
        base += 0.09
    return min(base, 0.99)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unknown"


def _string_list(value: object, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise StrategyError(f"Strategy field '{field_name}' must be a list of strings.")
    return value


def _dataclass_dict(item: Any) -> dict[str, Any]:
    return {field_name: getattr(item, field_name) for field_name in item.__dataclass_fields__}


def _parse_simple_yaml(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    data: dict[str, Any] = {}
    index = 0
    while index < len(lines):
        raw = lines[index]
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if line.startswith("  - "):
            raise StrategyError(f"Unexpected list item in {path}: {line}")
        if ":" not in line:
            raise StrategyError(f"Unsupported YAML line in {path}: {line}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value == ">":
            block: list[str] = []
            index += 1
            while index < len(lines) and (lines[index].startswith("  ") or not lines[index].strip()):
                block.append(lines[index].strip())
                index += 1
            data[key] = " ".join(part for part in block if part).strip()
            continue
        if raw_value:
            data[key] = _yaml_scalar(raw_value)
            index += 1
            continue
        index += 1
        if index < len(lines) and lines[index].startswith("  - "):
            items: list[Any] = []
            while index < len(lines) and lines[index].startswith("  - "):
                items.append(_yaml_scalar(lines[index][4:].strip()))
                index += 1
            data[key] = items
            continue
        if index < len(lines) and lines[index].startswith("  "):
            nested: dict[str, Any] = {}
            while index < len(lines) and lines[index].startswith("  "):
                nested_line = lines[index].strip()
                if not nested_line or nested_line.startswith("#"):
                    index += 1
                    continue
                nested_key, nested_value = nested_line.split(":", 1)
                nested[nested_key.strip()] = _yaml_scalar(nested_value.strip())
                index += 1
            data[key] = nested
            continue
        data[key] = None
    return data


def _yaml_scalar(value: str) -> Any:
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value.strip('"').strip("'")
