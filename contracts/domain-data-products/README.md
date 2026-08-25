# Domain Data Product Consumer Contracts

This directory owns Gateway's repo-native RFC-0084 consumer declarations. Gateway remains an
experience API: these declarations record its approved upstream dependencies and do not make it a
producer or domain authority.

The canonical validation owner is `lotus-platform`'s domain-data-product validator and federated
discovery generator. Gateway's unit lane protects the checked-in dependency semantics:

```powershell
python -m pytest tests/unit/test_domain_data_product_consumer_contract.py -q
```

The consumer gate checks declaration parity in both directions. It validates the route inventory
against the declared products and statically discovers `/integration/` route arguments passed as
either `path=` or `url=` in async or sync functions under `src/app/clients/lotus_core*.py`,
resolving direct, local, and module-level route assignments, including normalized f-string and
`.format(...)` templates. The comparison includes the normalized route identity, not only the
client method, so an already-inventoried method cannot hide an additional endpoint. Unresolved
public route construction remains fail-closed. Every Core client module must also expose at least
one statically resolvable transport route; the explicit `lotus_core_transaction_params.py`
exemption is a parameter/DTO-only module with no transport surface. The three explicitly classified
Core control-plane/snapshot operations (`capabilities`, `policy`, and `core-snapshot`) are outside
RFC-0084 domain-product scope. Any new Core integration route outside that narrow boundary is
treated as a domain-product read and must be added to `lotus-gateway-core-route-inventory.v1.json`
before the gate passes.
