# Verified principal pilot

Gateway can enforce verified principal admission on the exact-portfolio tax-lot read when its
deployment selects the verified pilot and supplies authoritative identity adapters. This is a
bounded consumer capability, not estate-wide authentication or production IAM certification.

| Boundary | Implemented behavior |
| --- | --- |
| Operation | `GET /api/v1/portfolio/portfolios/{portfolio_id}/positions/{security_id}/lots` |
| Credential | Signed Ed25519 compact JWS; configured issuer/key, audience `lotus-gateway`, time and revocation checks |
| Authorization | Tenant membership, `portfolio.read`, exact portfolio; delegated person/application intersection |
| Caller headers | Cannot select posture or widen verified authority |
| Unavailable identity | Refuse before protected Core calls; no header fallback |
| Core ownership | Lot identity, quantities, cost and lineage remain source-owned |

The grant store and revocation source are injected ports. Persistent hosting, bank operator
designation, key custody and identity provisioning remain unclaimed under Platform #775. Other
Gateway routes retain their existing admission. A portfolio grant never implies composite-member
authority. Header-trust is permitted only in local/dev for this pilot.

Engineers and operators should use the
[deployment wiring, caller example and proof guide](https://github.com/sgajbi/lotus-gateway/blob/main/docs/verified-principal-pilot.md).
The controlled registered-route suite measures all 13 denial classes with real signed bytes and
zero protected calls, valid delegated admission and concurrent isolation. Its Core HTTP transport
and authority stores are controlled fixtures; it does not establish bank identity or live access.

Return to [Security and Governance](Security-and-Governance), [API Surface](API-Surface), or [Home](Home).
