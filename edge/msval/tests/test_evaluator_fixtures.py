"""Conformance tests pinning the evaluator contract (Phase F)."""

from msval_edge.evaluation.evaluator import PythonRuleEvaluator
from msval_edge.evaluation.fixtures import (
    build_bad_request,
    expected_bad_tuples,
)


def _tuple(finding: dict) -> tuple:
    return (
        finding["rule_id"],
        finding["object_reference"],
        finding["field_path"],
    )


def test_bad_input_produces_pinned_findings_in_order():
    result = PythonRuleEvaluator().evaluate(build_bad_request())

    actual = [_tuple(finding) for finding in result.findings]

    assert actual == expected_bad_tuples()


def test_pinned_findings_severities_match_catalog():
    from msval_edge.policy.catalog import get_policy_bundle

    bundle = get_policy_bundle()
    result = PythonRuleEvaluator().evaluate(build_bad_request())

    for finding in result.findings:
        assert finding["severity"] == bundle.rules[finding["rule_id"]].severity

    # The fixture input is designed to fail with blocking findings:
    assert any(
        finding["severity"] == "BLOCK"
        for finding in result.findings
    )


def test_repeated_evaluation_is_byte_identical():
    evaluator = PythonRuleEvaluator()

    first = evaluator.evaluate(build_bad_request())
    second = evaluator.evaluate(build_bad_request())

    assert first.findings == second.findings
