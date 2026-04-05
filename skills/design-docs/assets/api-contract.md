<!-- Status: placeholder -->
<!-- Confidence: low -->
<!-- doc_type: api-contract -->

# API Contract: <TITLE>

## Surface

[QUESTION][must-answer] Is this HTTP, RPC, GraphQL, a client library, or
something else?

- **Style**:
- **Base path / package**:
- **Versioning scheme**: [ASSUMPTION][candidate] ...

## Endpoints / Operations

### <METHOD> <path> — <short purpose>

- **Request**:
  ```
  <schema sketch>
  ```
- **Response (success)**:
  ```
  <schema sketch>
  ```
- **Response (errors)**:
  - `4xx-code`: <when>
  - `5xx-code`: <when>
- **Idempotency**: [QUESTION][must-answer] Is this safe to retry?
- **Auth**: [QUESTION][must-answer] Who can call this?

## Auth Model

[ASSUMPTION][candidate] The auth scheme is ...

## Error Model

[ASSUMPTION][candidate] Errors follow shape: `{code, message, details}`

- **Error codes**:

## Rate Limiting

[QUESTION][nice-to-have] Per-caller limits? Global limits?

## Backward Compatibility

[QUESTION][must-answer] Can we break existing callers, or must we maintain
the current contract?

## Deprecation Policy

[ASSUMPTION][candidate] ...

## Open Questions

(Moved here during refine.)

## References

- PRD: `../PRD.md`
- ADRs: `../adr/`
