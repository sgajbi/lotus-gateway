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
   The RFC now includes implementation-backed RFC-0041 rebalance-wave realization under
   `/api/v1/dpm/command-center/waves*` for wave preview, create, search, detail, item list,
   source-check, simulation, selection, approval, staging, handoff, cancellation, proof-pack
   posture, supportability, and campaign-definition discovery/upsert composition without becoming
   the wave or cohort authority. It also includes
   RFC-0042 post-trade outcome-review realization; the first implementation-backed outcome-review
   BFF route family is active under
   `/api/v1/dpm/command-center/outcome-reviews*`, run lookup, and wave lookup routes, preserving
   manage source-lineage, supportability, report-input, and AI-evidence truth without recomputing
   expected-versus-realized outcomes. RFC-0039 construction alternative-set composition is also
   implementation-backed under `/api/v1/dpm/command-center/construction/alternative-sets*`,
   preserving manage-owned alternatives, diagnostics, supportability, and selection decisions
   without Gateway optimization or recomputation. RFC-0040 proof-pack composition is
   implementation-backed under `/api/v1/dpm/command-center/proof-packs*`, preserving manage-owned
   proof-pack ids, section states, reason codes, hashes, Markdown, report-input payloads, and
   AI-evidence payloads without Gateway proof-pack reconstruction. RFC40-WTBD-010
   portfolio-memory Gateway composition is implementation-backed under
   `/api/v1/dpm/command-center/portfolios/{portfolio_id}/memory`, preserving manage-owned event
   order, source systems, source refs, artifact refs, reason codes, supportability, bounded
   metadata, and content hash without Gateway timeline reconstruction. PM operating quality
   Gateway composition is implementation-backed under
   `/api/v1/dpm/command-center/pm-operating-quality/*`, preserving manage-owned policy
   configuration, score-run lifecycle evidence, fairness-analysis evidence, review-action
   evidence, bounded rationale, target content hashes, governance evidence, source refs, reason
   codes, content hashes, and forbidden-use posture without Gateway PM scoring, fairness
   recomputation, review-rationale reinterpretation, ranking, local policy administration, HR,
   compensation, conduct-enforcement, approval, client-contact, OMS, or execution decisions.
3. preserve RFC-0082 boundary discipline as integrations evolve
4. keep request-convention and runtime guidance explicit for operators and future agents
