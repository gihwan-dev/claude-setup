<!-- Status: placeholder -->
<!-- Confidence: low -->
<!-- doc_type: ux-flow -->

# UX Flow: <TITLE>

## Entry Points

[QUESTION][must-answer] Where does the user start this flow from?

- Entry 1:
- Entry 2:

## Primary Flow

Ordered steps with decision points. Each step names: the user action, the
system response, and the visible state change.

1. **Step**: [ASSUMPTION][candidate] User does X → system shows Y
2. **Decision point**: [DECISION-CANDIDATE] branch A | branch B | branch C
3. **Step**: ...

## Empty State

[QUESTION][nice-to-have] What does the user see when there's no data yet?

## Error States

- **Input validation error**: [ASSUMPTION][candidate] inline field error
- **Network / server error**: [ASSUMPTION][candidate] banner + retry
- **Permission denied**: [QUESTION][must-answer] Does this flow need authz?

## Success Confirmation

[QUESTION][nice-to-have] How does the user know it worked?

## Accessibility Considerations

(Populated if `accessibility` doc is in the bundle; otherwise inline.)

- Keyboard navigation: [ASSUMPTION][candidate] tab order follows visual order
- Screen reader: [ASSUMPTION][candidate] all interactive elements labeled
- Color contrast: [ASSUMPTION][candidate] WCAG AA

## Open Questions

(Moved here during refine.)

## References

- PRD: `../PRD.md`
- ADRs: `../adr/`
