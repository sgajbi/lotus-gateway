OPENAPI_TAGS: list[dict[str, str]] = [
    {"name": "Reports", "description": "Gateway-facing reporting data and command APIs."},
    {
        "name": "Report Jobs",
        "description": ("Gateway-facing report job operations for status and support diagnostics."),
    },
    {
        "name": "Report Batches",
        "description": (
            "Gateway-facing report batch materialization, status, control, and bounded "
            "operator-run APIs."
        ),
    },
    {
        "name": "Report Batch Schedules",
        "description": "Gateway-facing report batch scheduler inspection and run APIs.",
    },
    {
        "name": "Archived Documents",
        "description": ("Gateway-facing archived document metadata and controlled download APIs."),
    },
    {
        "name": "Analytics Diagnostics",
        "description": (
            "Protected operator analytics UI diagnostics lookup with bounded audit posture."
        ),
    },
    {
        "name": "advisory-policy",
        "description": (
            "Gateway-facing advisory policy pack, evaluation, evidence, workflow, validation, "
            "and sign-off APIs backed by lotus-advise policy authority."
        ),
    },
    {
        "name": "advisory-workspaces",
        "description": (
            "Gateway-facing advisory workspace draft, comparison, rationale, handoff, replay, "
            "version, and assistant APIs backed by lotus-advise workspace authority."
        ),
    },
    {
        "name": "advisory-copilot",
        "description": (
            "Gateway-facing advisory copilot evidence-packet, action, review, supportability, "
            "and proposal-version run APIs backed by lotus-advise source truth."
        ),
    },
    {
        "name": "Composite Performance",
        "description": (
            "Gateway-facing composite performance operations backed by lotus-performance "
            "source-owned calculation, inspection, lineage, and evidence contracts."
        ),
    },
    {
        "name": "domain-products",
        "description": (
            "Gateway discovery facade for governed domain-product catalogs, detail, dependency "
            "graphs, and trust certification evidence."
        ),
    },
    {
        "name": "DPM Command Center",
        "description": (
            "Gateway BFF composition APIs for DPM command-center, construction, proof-pack, "
            "rebalance-wave, and post-trade outcome-review workflows backed by "
            "lotus-manage authority."
        ),
    },
    {
        "name": "Source Products",
        "description": (
            "Gateway source-consumer routes for source-owned products that Workbench may "
            "display as evidence or supportability posture without recalculating source truth."
        ),
    },
    {
        "name": "foundation",
        "description": (
            "Gateway-facing Foundation portfolio catalog and workspace APIs backed by source "
            "portfolio, identity, allocation, and reference-data truth."
        ),
    },
    {
        "name": "intake",
        "description": (
            "Gateway-facing intake package, upload, and commit APIs for governed front-office "
            "portfolio onboarding workflows."
        ),
    },
    {
        "name": "lookups",
        "description": (
            "Gateway-facing lookup catalogs for portfolio, instrument, currency, and related "
            "front-office selector data."
        ),
    },
    {
        "name": "advisor-cockpit",
        "description": (
            "Gateway-facing advisor cockpit action, snapshot, supportability, and "
            "acknowledgement APIs backed by lotus-advise source truth."
        ),
    },
    {
        "name": "platform",
        "description": (
            "Gateway-facing platform capability, shell bootstrap, and source health composition "
            "APIs for governed Workbench runtime discovery."
        ),
    },
    {
        "name": "portfolio",
        "description": (
            "Gateway-facing portfolio catalog, workspace, book, position, transaction, "
            "performance, readiness, workflow, and liquidity APIs backed by portfolio source truth."
        ),
    },
    {
        "name": "proposals",
        "description": (
            "Gateway-facing proposal creation, state transition, memo, lineage, execution, "
            "reporting, and workflow APIs backed by proposal source authority."
        ),
    },
    {
        "name": "workbench",
        "description": (
            "Gateway-facing Workbench overview, analytics, portfolio 360, performance, risk, "
            "sandbox, and advisor-brief composition APIs."
        ),
    },
    {
        "name": "bank-demo-proof",
        "description": (
            "Gateway-facing RFC-0028 bank-demo proof contract APIs backed by lotus-advise "
            "source-owned scenario, supported-claim, and sanitized proof-pack truth."
        ),
    },
    {
        "name": "Operations",
        "description": "Operational health, readiness, and Prometheus metrics endpoints.",
    },
]
