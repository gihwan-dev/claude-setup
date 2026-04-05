<!-- Status: placeholder -->
<!-- Confidence: low -->
<!-- doc_type: security-privacy -->

# Security & Privacy: <TITLE>

## Sensitive Data Inventory

[QUESTION][must-answer] What PII or sensitive data does this touch?

| Data field | Category | Storage | Lifetime | Owner |
|-----------|----------|---------|----------|-------|
| ... | PII / financial / auth / etc. | ... | ... | ... |

## Data Flow (Security View)

[ASSUMPTION][candidate] Data flows:

1. Entry point: <where data enters system>
2. Transformations: <where data is decrypted, combined, masked>
3. Storage: <at-rest encryption, retention>
4. Exit: <where data leaves system>

## Authentication

- **Who authenticates**: [QUESTION][must-answer] ...
- **Mechanism**: [ASSUMPTION][candidate] ...
- **Session model**: [DECISION-CANDIDATE] cookie | JWT | opaque-token

## Authorization

- **Authz model**: [QUESTION][must-answer] RBAC, ABAC, per-resource?
- **Default deny?**: [ASSUMPTION][candidate] yes
- **Delegation / impersonation**: [QUESTION][nice-to-have]

## Threat Model

Threats identified via decomposition of the data flow above.

| Threat | Attack surface | Impact | Likelihood | Mitigation |
|--------|----------------|--------|-----------|------------|
| [QUESTION][must-answer] What is the worst realistic threat? | ... | ... | ... | ... |

## Privacy

- **Lawful basis** (if GDPR applies): [QUESTION][must-answer]
- **Data subject rights**: access / export / deletion — [QUESTION][must-answer]
- **Retention policy**: [ASSUMPTION][candidate] ...
- **Cross-border transfer**: [QUESTION][nice-to-have]

## Audit Logging

- **What is logged**: [QUESTION][must-answer]
- **Where**: [ASSUMPTION][candidate] ...
- **Retention**: [ASSUMPTION][candidate] ...

## Secrets Management

- **Where secrets live**: [ASSUMPTION][candidate] ...
- **Rotation**: [QUESTION][nice-to-have]

## Incident Response

[QUESTION][nice-to-have] What's the playbook if this surface is breached?

## Open Questions

(Moved here during refine.)

## References

- PRD: `../PRD.md`
- ADRs: `../adr/`
