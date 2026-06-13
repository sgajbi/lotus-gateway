from __future__ import annotations

import ast
from pathlib import Path

from app.observability.analytics_ui import (
    ANALYTICS_UI_ALLOWED_LABELS,
    ANALYTICS_UI_FORBIDDEN_FIELDS,
    GATEWAY_ANALYTICS_UI_METRIC_LABEL_CONTRACTS,
)

APP_ROOT = Path(__file__).resolve().parents[2] / "src" / "app"
PROMETHEUS_COLLECTORS = {"Counter", "Enum", "Gauge", "Histogram", "Info", "Summary"}


def test_gateway_prometheus_metric_labels_are_registered_and_bounded() -> None:
    discovered = _discover_prometheus_metric_label_contracts()

    assert discovered == GATEWAY_ANALYTICS_UI_METRIC_LABEL_CONTRACTS

    for metric_name, labels in discovered.items():
        assert metric_name.startswith("lotus_gateway_")
        assert labels
        assert set(labels) <= ANALYTICS_UI_ALLOWED_LABELS
        assert not set(labels) & ANALYTICS_UI_FORBIDDEN_FIELDS
        assert not any(_is_high_cardinality_label(label) for label in labels)


def _discover_prometheus_metric_label_contracts() -> dict[str, tuple[str, ...]]:
    discovered: dict[str, tuple[str, ...]] = {}
    for path in sorted(APP_ROOT.rglob("*.py")):
        module = ast.parse(path.read_text(encoding="utf-8"))
        constants = _module_string_tuple_constants(module)
        aliases = _prometheus_collector_aliases(module)
        for node in ast.walk(module):
            if not isinstance(node, ast.Call):
                continue
            collector_name = _call_name(node)
            if collector_name not in aliases:
                continue
            metric_name = _metric_name(node)
            labels = _metric_labels(node, constants)
            assert labels, f"{path}: {metric_name} must declare explicit labels"
            discovered[metric_name] = labels
    return discovered


def _module_string_tuple_constants(module: ast.Module) -> dict[str, tuple[str, ...]]:
    constants: dict[str, tuple[str, ...]] = {}
    for node in module.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name):
            value = _string_tuple(node.value, constants)
            if value is not None:
                constants[target.id] = value
    return constants


def _prometheus_collector_aliases(module: ast.Module) -> set[str]:
    aliases: set[str] = set()
    for node in module.body:
        if not isinstance(node, ast.ImportFrom) or node.module != "prometheus_client":
            continue
        for alias in node.names:
            if alias.name in PROMETHEUS_COLLECTORS:
                aliases.add(alias.asname or alias.name)
    return aliases


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    return None


def _metric_name(node: ast.Call) -> str:
    if node.args:
        value = _string_literal(node.args[0])
        if value is not None:
            return value
    for keyword in node.keywords:
        if keyword.arg == "name":
            value = _string_literal(keyword.value)
            if value is not None:
                return value
    raise AssertionError("Prometheus collector must declare a literal metric name")


def _metric_labels(
    node: ast.Call,
    constants: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    if len(node.args) >= 3:
        labels = _string_tuple(node.args[2], constants)
        if labels is not None:
            return labels
    for keyword in node.keywords:
        if keyword.arg == "labelnames":
            labels = _string_tuple(keyword.value, constants)
            if labels is not None:
                return labels
    raise AssertionError("Prometheus collector must declare labels as a literal or named tuple")


def _string_tuple(
    node: ast.AST,
    constants: dict[str, tuple[str, ...]],
) -> tuple[str, ...] | None:
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    if not isinstance(node, ast.Tuple):
        return None
    values: list[str] = []
    for item in node.elts:
        value = _string_literal(item)
        if value is None:
            return None
        values.append(value)
    return tuple(values)


def _string_literal(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _is_high_cardinality_label(label: str) -> bool:
    tokens = {
        "account",
        "body",
        "client",
        "correlation",
        "document",
        "holding",
        "instrument",
        "output",
        "portfolio",
        "prompt",
        "request",
        "response",
        "session",
        "trace",
        "transaction",
        "upload",
    }
    normalized = label.lower()
    return any(token in normalized for token in tokens)
