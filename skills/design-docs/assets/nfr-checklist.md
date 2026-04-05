<!-- Status: placeholder -->
<!-- Confidence: low -->
<!-- doc_type: nfr-checklist -->

# Non-Functional Requirements: <TITLE>

## Performance Targets

- **Latency**: [QUESTION][must-answer] p50, p95, p99 targets?
- **Throughput**: [QUESTION][must-answer] QPS / concurrent load?
- **Payload size**: [ASSUMPTION][candidate] ...

## Scalability

- **Expected load at launch**: [QUESTION][must-answer]
- **Expected load at 6 months**: [QUESTION][nice-to-have]
- **Scaling model**: [ASSUMPTION][candidate] horizontal / vertical / ...

## Availability

- **SLO**: [QUESTION][must-answer] e.g. 99.9%?
- **Degradation mode**: [ASSUMPTION][candidate] ...

## Reliability

- **Retry strategy**: [ASSUMPTION][candidate] ...
- **Timeout defaults**: [ASSUMPTION][candidate] ...
- **Failure domains**: [DECISION-CANDIDATE] single-region | multi-region | ...

## Observability

- **Metrics**: [QUESTION][must-answer] What must be visible on dashboards?
- **Logs**: [ASSUMPTION][candidate] structured JSON at INFO/WARN/ERROR
- **Traces**: [QUESTION][nice-to-have] Distributed tracing required?
- **Alerts**: [QUESTION][must-answer] What signals page on-call?

## Cost

- **Budget envelope**: [QUESTION][nice-to-have] ...
- **Cost per request / per user**: [ASSUMPTION][candidate] ...

## Compliance

[QUESTION][must-answer] Which regulations apply (GDPR, SOC2, HIPAA, etc.)?

## Capacity Planning

[ASSUMPTION][candidate] ...

## Open Questions

(Moved here during refine.)

## References

- PRD: `../PRD.md`
- ADRs: `../adr/`
