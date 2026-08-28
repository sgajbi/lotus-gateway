# Validation and CI

This page is the current operator and engineering map for `lotus-gateway` validation lanes,
release evidence, and progressive enterprise-hardening gates. It records implementation-backed
checks and the current measured quality baseline; it is not a replacement for GitHub check truth.

Route guidance is in [API Surface](API-Surface); only the product-owned `/api/v1/portfolio/*`
family is current. Per-branch refactoring history is in the commit log, not on this page — see
[Where the per-branch refactor history went](#where-the-per-branch-refactor-history-went).

## Reader Map

| Reader | First Question | Use This Evidence |
| --- | --- | --- |
| Developer | What should I run before committing? | `make check` for lint, type, contract, and unit proof |
| Reviewer | Which gate proves PR readiness? | `make ci` plus GitHub PR Merge Gate |
| Release/operator | What proves image and metadata posture? | Main Releasability and container release manifests |
| Future agent | What quality ceiling must not regress? | Agent quality evidence: `315/49`, current hotspot `src/app/contracts/dpm_pm_operating_quality.py` |

## Lane model

`lotus-gateway` uses:

1. `Remote Feature Lane`
2. `Pull Request Merge Gate`
3. `Main Releasability Gate`
4. platform-facing validation for cross-app experience changes
5. `Quality Baseline`
   blocking no-regression evidence for refactor thresholds, workflow governance, and artifact
   integrity, duplicate-code fingerprints, and progressive enterprise-readiness gates
6. `Upstream Contract Drift`
   scheduled and operator-dispatched reconciliation of the packaged proposal decision policy with
   the current Advise producer artifact

## Local command mapping

- `make check`
  lint, monetary-float governance, refactor thresholds, workflow action-runtime governance,
  agent quality evidence governance, typecheck, OpenAPI contract proof, unit tests
- `make ci`
  migration smoke, integration tests, coverage, security audit, and the pinned duplicate-code
  ratchet over production Python sources
- `make pr-issue-lifecycle`
  fail-closed PR title/body lifecycle validation. Set `LOTUS_PR_TITLE` and `LOTUS_PR_BODY` first;
  intended auto-close work uses a standalone `Closes #123` body line, while partial work uses
  `Keep #123 open`. The Pull Request Merge Gate runs the same command from environment variables,
  rejecting negated or malformed closing references before product validation begins and rerunning
  the evidence after a PR title/body edit without restarting the heavy lane for a draft-state-only
  change. GitHub issue URLs are rejected as closing references; use the explicit `#` form only.
  Manual dispatches receive a distinct non-satisfying lifecycle-check name because they have no PR
  metadata.
- `make duplicate-code`
  pinned jscpd scan, stable-finding ratchet, and repeated-run candidate-set check using
  `quality/package-lock.json`; the protected baseline is generated/enforced on Ubuntu/Node 20 and
  the detector must select the same normalized candidates and aggregate metrics twice. The local
  repeated-run check proves same-environment determinism; cross-operating-system equivalence remains
  unclaimed and must not be hidden by a union baseline
- `make duplicate-code-protected`
  supported local fallback when host selection differs: runs the same duplicate-code scans and
  ratchets in the pinned Linux/Node 20 image using a checkout-specific Compose project, then removes
  only that project; it does not touch the canonical Gateway runtime. It mounts the checkout
  read-only at a dedicated source root, keeps writable dependency and output volumes outside that
  mount, and copies the scan report before
  teardown into a run-unique caller-created `output/duplicate-code-protected/` directory, so a
  native Linux run cannot leave root-owned artifacts while mismatch diagnostics remain available.
- `make ci-local`
  local feature-lane validation
- `make ci-local-docker`
  Docker parity for the integration boundary
- `make ci-local-docker-down`
  cleanup scoped to the stable checkout-specific Compose project derived by
  `scripts/ci_local_compose_project.py`; `CI_LOCAL_COMPOSE_PROJECT` may override it with a unique
  identity, and cleanup must not remove an active product Gateway container
- `make proposal-decision-vocabulary-gate`
  requires and reconciles the current Advise proposal decision vocabulary; protected CI supplies
  the official producer URL so changed decision/action/gate pairings fail with the source blob
  revision rather than silently comparing the packaged snapshot with itself
- `make proposal-decision-vocabulary-snapshot-check`
  explicitly validates packaged snapshot integrity for offline diagnosis; it is not producer-drift
  evidence and is never used by protected CI
- Memo contract fitness tests require every memo-family data schema to be explicitly closed
  (`additionalProperties: false`), expose named top-level properties, recursively close nested
  memo-owned models, reject nested `additionalProperties: true`, preserve typed scalar maps, and
  reject contradictory audit-event counts. This keeps OpenAPI contract drift and envelope-only
  typing out of the PR gate rather than relying on review discovery.
- `make clean`
  removes disposable local generated artifacts and caches, including `output/`, `.codex-logs/`,
  coverage outputs, Python bytecode caches, package metadata, and `gateway-*.log`; publish or
  preserve required evidence before cleanup

## HTTPX retry taxonomy

Gateway retries only an explicit allow-list of request failures: enabled timeouts, network errors,
and remote protocol disconnects. Redirect loops, unsupported protocols, local protocol errors, and
unclassified `RequestError` values are terminal. Terminal request errors must remain immediate
communication failures in result polling; they must not consume the elapsed analytics deadline or
be relabelled as source calculation unavailability. The taxonomy is covered by unit tests for the
JSON transport and the analytics polling boundary.

The caller-scoped Archive access-preflight on report-batch status is an explicit exception: it is an
advisory, fail-closed status enrichment, so it makes one request only and does not retry a timeout.
Its `ARCHIVE_ACCESS_PREFLIGHT_TIMEOUT_SECONDS` setting is capped at three seconds. This prevents one
unavailable Archive dependency from multiplying downstream calls or delaying a Report-owned status
response; it does not define a total endpoint SLO.

## PR auto-merge posture

PR auto-merge is rebase-only for linear history. The `Queue Auto Merge` helper uses
`LOTUS_AUTOMERGE_TOKEN` with `gh pr merge --auto --rebase --delete-branch`; when that token is not
available, the helper emits a warning and exits successfully so an authorized human or release actor
can perform the rebase merge without leaving a false red CI check.

Merged PRs into `main` also trigger the `Merged PR Main Releasability Dispatch` workflow. It listens
only to closed pull-request events, verifies that the pull request was merged into `main`, and then
dispatches `main-releasability.yml` through an immutable `main-releasability-<sha>` tag. That keeps
exact-main release evidence available for authorized human merges and release-actor merges, not only
token-backed auto-merge. The dispatcher passes `source_branch=main`, so build metadata, provenance,
manifests, and `/version` describe the merged mainline source rather than the synthetic dispatch tag.
`main-releasability.yml` is intentionally `workflow_dispatch`-only so this dispatcher is the single
automatic post-merge path and does not race or cancel a duplicate push-triggered release run. Manual
dispatches intentionally have no `source_branch` default; release metadata inherits the selected
workflow ref unless an operator explicitly provides a source branch override. Concurrency is
isolated by the checked-out GitHub SHA; `expected_sha` is validation-only, so only reruns of the
same actual revision may supersede one another.

## What the gates protect

- workbench-facing contract integrity
- startup and migration truth
- upstream composition safety
- Advise proposal decision/action/gate vocabulary drift before a changed producer contract reaches
  Gateway runtime publication
- live integration-boundary parity
- CI action-runtime compatibility with the platform baseline:
  `actions/checkout@v6`, `actions/setup-python@v6`, `actions/setup-node@v5`, and
  `actions/upload-artifact@v7`
- Workflow-level Node 24 JavaScript action runtime opt-in through
  `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`
- main release evidence retention for coverage, workflow governance, agent quality, security,
  OpenAPI, and demo-certification artifacts
- duplicate-code clone count, duplicated-line percentage, and stable source-pair/normalised-
  fragment occurrence fingerprints must not regress beyond the reviewed production baseline;
  removed pairs must be banked through a
  reviewed baseline update before they can be reintroduced
- the duplicate detector must also produce the same normalized candidate identities, including
  source locations, and aggregate metrics on two identical invocations; detector failures,
  missing status evidence, or candidate drift are hard quality failures
- duplicate fingerprints include Python-version-independent normalized AST scope context and
  occurrence ordering so line shifts, adjacent source edits, or non-local scope-body edits do not
  invalidate unrelated clones; cross-scope replacements remain visible, while same-scope
  relocation is an explicit identity trade-off; the canonical source side is used when the
  detector reports the same clone in reverse order; reported column boundaries are honored so
  unrelated same-line prefixes do not change the fragment; quoted literal contents are preserved
  during fragment normalization, including stable reconstruction of Python 3.11 versus 3.12+
  f-string token spans; the detector input root is explicitly `src/app` with a `**/*.py` pattern
  so repeated protected runs do not inherit checkout-root traversal order
- duplicate-code ratchet failures remain hard merge gates, but are enforced after baseline evidence
  collection and artifact upload so diagnostics from later quality producers are retained
- incomplete duplicate detector slices are never fingerprinted from partial token streams; the
  structural delimiter check and comment-safe lexical fallback normalize formatting while
  preserving literals, comments, and interpreter-independent identity; complete f-string
  expressions receive the same layout normalization on the token path while conversion,
  debug-expression, and format-specification text remains preserved
- duplicate-code ratchet output reports `--update-baseline` as blocked when unexpected findings,
  metric regressions, or detector failures remain, instead of directing an operator to an unusable
  update path
- container supply-chain evidence for Gateway images: Git-SHA tags, OCI labels, SBOM, Trivy scan,
  release manifest, digest-pinned Kubernetes reference, main-only GHCR push, cosign signature, and
  provenance attestation

## Container release evidence

Main Releasability concurrency is keyed only by the checked-out GitHub SHA. The optional
`expected_sha` dispatch input is verified after checkout but never controls cancellation identity,
so an invalid operator input cannot cancel release evidence for another revision.

PR Merge Gate builds `ghcr.io/<owner>/lotus-gateway:${{ github.sha }}` locally, also tags
`lotus-gateway:ci-test` for Docker parity, generates an SBOM with pinned `anchore/syft:v1.42.3`,
runs a pinned `aquasec/trivy:0.72.0` image scan that fails on fixable HIGH/CRITICAL findings,
writes `output/container-security/image-release-manifest.json`, validates it with
`scripts/check_container_release_evidence.py --allow-unsigned`, and uploads
`pr-container-release-evidence`. The scan artifact still records unfixed vendor findings for
operator review. PR images are not pushed or signed.

Main Releasability builds the same Git-SHA tag, generates the SBOM, runs the Trivy scan before any
push, and pushes the passing image to GHCR from CI. A transient GHCR `unknown blob` response receives
at most two retries (three total attempts) with 5/10-second backoff and a retained log per attempt;
any other push failure is immediately a hard release-gate failure. Only a successful push permits
digest capture, signing the digest-pinned image with cosign, provenance attestation, and validation
of the same manifest without
`--allow-unsigned`, and uploads `main-container-release-evidence`. Kubernetes deployment promotion
must use the manifest `image.digest_ref`; do not deploy mutable tags.

The `/version` endpoint exposes the same non-secret build and deployment metadata recorded in the
release manifest: Git commit SHA, branch, build timestamp, repo URL, image digest, CI run ID, and
version. Build-time OCI labels carry only metadata known before image creation. Image digest is
captured after push and must be supplied by deployment/runtime configuration; do not bake an
`unknown` digest into Docker build args, ENV, or OCI labels. Credentials are not passed through
Docker build args or runtime environment metadata.

## Quality baseline lane

The Quality Baseline workflow keeps current advisory findings visible, but it is no longer a
pure report-only lane. It blocks refactor-threshold regression, workflow-governance drift, agent
quality evidence drift through `scripts/check_agent_quality_evidence.py`, measured quality
regression through `scripts/check_quality_baseline_ratchet.py`, and missing required evidence
before uploading artifacts. The agent quality evidence gate keeps the executable
 315/49 ratchet, the current evidence-selected
`src/app/contracts/dpm_pm_operating_quality.py` hotspot, and durable
scorecard/context guidance synchronized for future agent development. It installs the optional
`quality` dependency group and records evidence for:

- complexity and maintainability through `radon` and `xenon`
- high-confidence dead-code candidates through `vulture`
- dependency hygiene through `deptry`, with the local `app` and `tests` namespaces classified as
  first-party so shared test fixtures do not create false missing-dependency regressions
- the dependency-findings ratchet is currently 21; a later Quality Baseline result of 22 fails
  rather than spending the measured post-#645 improvement
- security findings through `bandit` and `pip-audit`
- import-boundary contracts through `import-linter`
- docstring baseline through `interrogate`
- OpenAPI governance through Spectral and `.spectral.yaml`
- proposal-memo OpenAPI fitness through source-faithful typed response references and stale-shape
  rejection in `tests/contract/test_proposals_contract.py`; memo-family `data` payloads may not
  regress to an unconstrained `dict[str, Any]`, and recursively reachable memo objects may not
  reintroduce `additionalProperties: true`; bounded typed scalar maps remain valid. The same
  contract gate rejects incomplete or contradictory lineage evidence, while service tests require
  malformed successful Advise memo payloads to map to `ADVISE_PROPOSAL_MEMO_CONTRACT_INVALID`
  rather than a generic 500
- Advisor Cockpit action contract fitness through typed list/detail response references, closed
  nested action schemas, bounded page collections, rejection of invented free-form fields, and
  integration proof that malformed successful Advise action data maps to
  `ADVISE_COCKPIT_ACTION_CONTRACT_INVALID`
- Gateway demo certification through `make demo-certification`, currently report-only, writing
  `output/demo-certification/gateway-demo-certification.json` and
  `output/quality-baseline/demo-certification.txt`

The checked-in ratchet records coverage, import-boundary, complexity, dead-code, dependency,
security, documentation, and Spectral problem thresholds in `quality/quality_ratchet.json`.
Every run publishes current value, baseline, delta, threshold, and a remediation command in
`output/quality-baseline/quality-ratchet.txt`. CI never updates this file automatically; a reviewed
baseline update must use the explicit `--update-baseline` command after inspecting the underlying
tool findings. This prevents new AI-generated or accidental quality regressions without claiming
that all existing findings are already resolved.

Every report-producing quality log also carries exactly one
`QUALITY_COMMAND_STATUS=<non-negative integer>` marker from the producer process exit status.
Missing, malformed, or duplicate markers fail artifact validation because the measurement is not
trustworthy. A non-zero status alongside reviewed baseline findings remains explicit trend evidence;
a tool failure without a parseable result cannot be counted as zero findings.

The workflow has one authoritative automated feature event: `pull_request` targeting `main`.
Feature-branch pushes do not create a duplicate Quality Baseline run; opening or synchronizing a
PR produces the protected check for that head SHA. Manual dispatch remains available for explicit
revalidation. The concurrency key uses the pull-request number to cancel stale in-progress work
across synchronized revisions, while manual dispatch uses a unique run ID. The complete push-only,
PR, updated-PR, and manual event matrix is documented in
`docs/quality-baseline-event-matrix.md`.

The lane must not replace `make check` or `make ci`. It exists to classify current baseline
findings, prove the blocking no-regression checks, then promote only agreed additional checks into
blocking Feature Lane and PR Merge Gate enforcement.

Current baseline truth lives in:

- [quality/baseline_report.md](https://github.com/sgajbi/lotus-gateway/blob/main/quality/baseline_report.md)
- [quality/quality_scorecard.md](https://github.com/sgajbi/lotus-gateway/blob/main/quality/quality_scorecard.md)
- [quality/architecture_rules.md](https://github.com/sgajbi/lotus-gateway/blob/main/quality/architecture_rules.md)
- [quality/api_governance_rules.md](https://github.com/sgajbi/lotus-gateway/blob/main/quality/api_governance_rules.md)


### Current ratchet values

These are the enforced thresholds, read from
[`quality/quality_ratchet.json`](https://github.com/sgajbi/lotus-gateway/blob/main/quality/quality_ratchet.json).
That file is the authority; if this table disagrees with it, the file is right and this table is a
bug.

| Metric | Threshold | Direction | Measured from |
|---|---|---|---|
| `coverage_percent` | 94.77 | must not fall below | `coverage.txt` |
| `architecture_import_contract_failures` | 11 | must not exceed | `import-linter.txt` |
| `complexity_xenon_blocks` | 2 | must not exceed | `complexity.txt` |
| `dead_code_findings` | 24 | must not exceed | `vulture.txt` |
| `dependency_findings` | 21 | must not exceed | `deptry.txt` |
| `security_undefined_findings` | 0 | must not exceed | `security.txt` |
| `security_low_findings` | 2 | must not exceed | `security.txt` |
| `security_medium_findings` | 1 | must not exceed | `security.txt` |
| `security_high_findings` | 0 | must not exceed | `security.txt` |
| `documentation_percent` | 1.6 | must not fall below | `interrogate.txt` |
| `openapi_spectral_problems` | 4 | must not exceed | `spectral.txt` |

A ratchet is set at the measured value with no headroom, so an improvement cannot go unbanked and a
regression cannot be absorbed silently. Each metric carries its own remediation string in the JSON,
which the failure message prints — read that first when a gate blocks.

### Agent quality evidence

`scripts/check_agent_quality_evidence.py` is the gate that keeps agent-facing quality documentation
aligned with what CI actually measures. It enforces two structural ceilings:

| Ceiling | Current value |
|---|---|
| Largest source file | **315** lines — `src/app/contracts/dpm_pm_operating_quality.py` |
| Largest function | **49** lines — `get_portfolio_transactions` in `src/app/clients/lotus_core_portfolio_query_client.py` |

The pair is written `315/49` wherever it appears, and the gate requires that exact string, the
current hotspot path, and a reference to the script itself in every document listed in
`REQUIRED_DOCUMENTS` — including this page. Those thresholds are **equality** checks, not upper
bounds: a branch that reduces the largest source file must also update the recorded value, or the
gate fails. That is deliberate, and it is why the numbers here are trustworthy.

The workflow fragments are checked too, so `--max-source-file-lines` and `--max-function-lines` in
`.github/workflows/quality-baseline.yml` cannot drift from the script's defaults.

### When a quality gate blocks you

1. Read the metric name and its remediation string in the failure output.
2. Reproduce locally with the tool named in the table above, against the same paths CI uses.
3. Fix the finding. If it genuinely cannot be fixed now, a baseline update is a **reviewed,
   explicit** action — `--update-baseline` after inspecting the underlying findings — never an
   automatic step and never a way to absorb a regression.
4. If the ratchet blocks because the tree *improved*, bank the improvement by updating the recorded
   value in the same PR.

### Where the per-branch refactor history went

This section previously carried roughly 1,400 lines of per-branch refactoring narrative — one
paragraph per extraction branch, each recording the source-file and function thresholds as they
stood at that moment. Every one of those numbers is superseded by the current ratchet above, and
the narrative itself is already in the commit history, where it is searchable and attributable.

It was removed rather than kept: a page where 85% of the content is superseded measurements is not
a page a reader can use, and a stale threshold sitting next to a live one is the kind of detail that
gets cited by mistake. For the history of any particular extraction, use
`git log --follow` on the module concerned.
