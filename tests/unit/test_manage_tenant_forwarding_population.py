"""Every lotus-manage operation that needs a tenant must take one.

This asserts over the *population* of client methods rather than a list of them.
Two successive enumerations each missed operations: #763 named 23 call sites and
was correct for the lotus-manage revision it was taken from; #770 found four wave
workflow commands that gained a required header one commit later; #771 found
twenty-two campaign operations whose requirement never appears in the served
OpenAPI at all, because lotus-manage enforces it through a dependency that reads
`request.headers` rather than through a declared parameter.

A list would have passed in all three cases. Walking the client classes fails
when a method is added without a tenant, which is the failure that actually
happened three times.

The families below are the measured state of lotus-manage, not a preference:
some manage aggregates genuinely carry no tenant, and asserting a tenant on those
would make Gateway invent scope its caller never asserted.
"""

import ast
from pathlib import Path

CLIENTS = Path(__file__).resolve().parents[2] / "src" / "app" / "clients"

# Client modules whose every public method reaches a lotus-manage route that
# refuses a request without a tenant.
TENANT_REQUIRED_CLIENTS = (
    "dpm_wave_campaign_definition_client.py",
    "dpm_wave_campaign_workflow_client.py",
)

# Wave commands lotus-manage guards with `WaveTenantIdHeader`, which is declared
# as a bare `str` and therefore required.
TENANT_REQUIRED_WAVE_OPERATIONS = frozenset(
    {
        "preview_wave",
        "create_wave",
        "list_waves",
        "get_wave",
        "get_wave_items",
        "source_check_wave",
        "simulate_wave",
        "select_wave_item",
        "approve_wave",
        "stage_wave",
        "handoff_wave",
        "cancel_wave",
        "get_wave_proof_pack_posture",
        "get_wave_supportability",
        "get_wave_report_input",
    }
)


def _public_async_methods(filename: str) -> dict[str, frozenset[str]]:
    """Method name -> its parameter names, parsed rather than pattern-matched.

    A regex over these modules merges adjacent method bodies: it reported
    `approve_wave` as already carrying a tenant because `stage_wave`'s parameters
    fell inside the match. The parser does not have that failure mode.
    """
    tree = ast.parse((CLIENTS / filename).read_text(encoding="utf-8"))
    methods: dict[str, frozenset[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for member in node.body:
            if not isinstance(member, ast.AsyncFunctionDef):
                continue
            if member.name.startswith("_"):
                continue
            args = member.args.args + member.args.kwonlyargs
            methods[member.name] = frozenset(argument.arg for argument in args)
    return methods


def test_every_campaign_client_method_takes_a_tenant() -> None:
    missing: list[str] = []
    total = 0
    for filename in TENANT_REQUIRED_CLIENTS:
        for name, parameters in _public_async_methods(filename).items():
            total += 1
            if "tenant_id" not in parameters:
                missing.append(f"{filename}::{name}")

    assert total >= 24, (
        "expected the campaign clients to expose at least the 24 operations "
        f"measured against lotus-manage, found {total}"
    )
    assert missing == [], (
        "lotus-manage refuses campaign requests without X-Tenant-Id "
        "(campaign_trusted_context_required, 44 references across 18 routers). "
        f"These send none: {missing}"
    )


def test_every_tenant_guarded_wave_command_takes_a_tenant() -> None:
    methods = _public_async_methods("dpm_wave_core_client.py")

    unknown = sorted(TENANT_REQUIRED_WAVE_OPERATIONS - methods.keys())
    assert unknown == [], (
        "these operations are named as tenant-guarded but no longer exist on the "
        f"client, so the list has drifted from the code: {unknown}"
    )

    missing = sorted(
        name for name in TENANT_REQUIRED_WAVE_OPERATIONS if "tenant_id" not in methods[name]
    )
    assert missing == [], (
        "lotus-manage declares WaveTenantIdHeader as a bare `str` on these "
        f"commands, so an absent header is refused. These send none: {missing}"
    )


def test_the_campaign_seam_is_the_only_way_campaign_calls_reach_manage() -> None:
    """If a campaign method stops using the shared helpers, the header is optional again.

    The tenant is threaded through `_get_campaign_workflow_read` and
    `_post_campaign_workflow_write` rather than through each call site. That is
    only safe while every call site uses them: a method that calls `self._get`
    directly would type-check, pass the parameter test above by declaring an
    unused argument, and still send no header.
    """
    for filename in TENANT_REQUIRED_CLIENTS:
        source = (CLIENTS / filename).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            for member in node.body:
                if not isinstance(member, ast.AsyncFunctionDef):
                    continue
                if member.name.startswith("_"):
                    continue
                called = {
                    child.func.attr
                    for child in ast.walk(member)
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
                }
                direct = called & {"_get", "_post", "_put"}
                if not direct:
                    continue
                # A direct transport call is allowed only where it demonstrably
                # builds the header itself. `put_campaign_definition` needs `_put`,
                # which the campaign helpers do not offer -- it declared a tenant
                # and sent `self._headers(correlation_id)`, which type-checked and
                # was still refused. That is the case this branch exists to catch.
                body = ast.get_source_segment(source, member) or ""
                assert '"X-Tenant-Id": tenant_id' in body, (
                    f"{filename}::{member.name} calls {sorted(direct)} directly "
                    "rather than through the campaign helpers, and does not build "
                    "the tenant header itself, so it sends no tenant"
                )
