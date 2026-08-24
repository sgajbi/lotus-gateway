# Scripts Guide

## Responsibility

`scripts/` owns deterministic repo-native automation for quality gates, migration checks, demo
certification, cleanup, runtime helpers, and evidence validation.

## Boundary Rules

| Area | Rule | Evidence |
| --- | --- | --- |
| Determinism | Scripts should fail clearly and avoid hidden external state unless documented. | `Makefile` |
| Safety | Cleanup or filesystem scripts must guard repo-root scope before deletion. | `scripts/clean_generated_artifacts.py` |
| CI fit | Add scripts to Make targets when they are low-noise and suitable for local or CI gates. | `Makefile` |
| Evidence | Scripts that generate evidence should write under ignored `output/` unless source truth is intended. | `.gitignore` |
| Upstream contract drift | `check_proposal_decision_vocabulary.py` validates the packaged snapshot locally and reconciles the current public Advise artifact when its governed URL is supplied. | `make proposal-decision-vocabulary-gate` |

## Validation

Run the script directly with focused inputs, then run the Make target that owns it. Add unit tests
for parsers, validators, cleanup safety, and other deterministic behavior.

## Update Triggers

Update this guide and operations docs when scripts add or change generated artifacts, cleanup scope,
CI lane placement, validation evidence, or operator-visible commands.
