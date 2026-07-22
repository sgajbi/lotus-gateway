# Domain Data Product Consumer Contracts

This directory owns Gateway's repo-native RFC-0084 consumer declarations. Gateway remains an
experience API: these declarations record its approved upstream dependencies and do not make it a
producer or domain authority.

The canonical validation owner is `lotus-platform`'s domain-data-product validator and federated
discovery generator. Gateway's unit lane protects the checked-in dependency semantics:

```powershell
python -m pytest tests/unit/test_domain_data_product_consumer_contract.py -q
```
