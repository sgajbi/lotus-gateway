# Roadmap

## Current phase

- active experience API for `lotus-workbench`
- foundation, workbench, reporting, proposal, and platform capability contracts are live

## Intentional limitations

- some thin pass-through and transitional route shapes still exist
- parameter conventions are not fully uniform across all route families
- gateway is not the authority for upstream domain methodology

## Next priorities

1. keep replacing thin pass-through surfaces with clearer product contracts
2. continue implementing RFC-0098 as the strategic DPM command-center composition contract for
   Workbench,
   preserving domain ownership across core, manage, risk, performance, report, archive, and AI.
   The RFC now includes RFC-0041 rebalance-wave realization so Gateway can plan wave preview,
   source-check, simulation, selection, approval, staging, handoff, and supportability composition
   without becoming the wave authority. It also includes RFC-0042 post-trade outcome-review
   realization; the first implementation-backed outcome-review BFF route family is active under
   `/api/v1/dpm/command-center/outcome-reviews*`, run lookup, and wave lookup routes, preserving
   manage source-lineage, supportability, report-input, and AI-evidence truth without recomputing
   expected-versus-realized outcomes. RFC-0039 construction alternative-set composition is also
   implementation-backed under `/api/v1/dpm/command-center/construction/alternative-sets*`,
   preserving manage-owned alternatives, diagnostics, supportability, and selection decisions
   without Gateway optimization or recomputation.
3. preserve RFC-0082 boundary discipline as integrations evolve
4. keep request-convention and runtime guidance explicit for operators and future agents
