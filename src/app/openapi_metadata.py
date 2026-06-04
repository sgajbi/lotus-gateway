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
        "name": "Composite Performance",
        "description": (
            "Gateway-facing composite performance operations backed by lotus-performance "
            "source-owned calculation, inspection, lineage, and evidence contracts."
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
        "name": "advisor-cockpit",
        "description": (
            "Gateway-facing advisor cockpit action, snapshot, supportability, and "
            "acknowledgement APIs backed by lotus-advise source truth."
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
