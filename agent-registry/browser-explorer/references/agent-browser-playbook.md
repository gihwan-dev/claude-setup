# agent-browser Playbook

## Prerequisites

Verify installation before any browser work:

```bash
which agent-browser || echo "Install: npm i -g agent-browser && agent-browser install"
```

## Core Workflow

Every investigation follows this cycle:

1. **Open** — `agent-browser open <url>`
2. **Snapshot** — `agent-browser snapshot -i` (interactive elements with refs)
3. **Interact** — use refs to click, fill, type, select
4. **Re-snapshot** — after any DOM change, get fresh refs

The browser persists between commands via a background daemon. Chain with `&&` when intermediate parsing is unnecessary.

## Investigation Commands

### Reproduction

```bash
agent-browser open "http://localhost:3000/target-page"
agent-browser snapshot -i                    # get element refs
agent-browser click @e3                      # interact with ref
agent-browser fill @e5 "test input"          # fill form field
agent-browser type "search query"            # type into focused element
agent-browser select @e7 "option-value"      # select dropdown
agent-browser press Enter                    # keyboard input
agent-browser wait --load networkidle         # wait for async operations
agent-browser snapshot -i                    # re-snapshot after changes
```

### Evidence Collection

```bash
agent-browser screenshot                     # viewport capture
agent-browser screenshot --full              # full page capture
agent-browser get text @e2                   # extract element text
agent-browser get url                        # current URL
agent-browser get title                      # page title
agent-browser network requests                # list tracked requests
agent-browser network har start              # begin HAR recording
agent-browser network har stop ./capture.har # save HAR file
```

### State Inspection

```bash
agent-browser eval "document.querySelector('.modal').dataset.state"
agent-browser eval "window.__STORE__.getState()"
agent-browser snapshot                       # full accessibility tree (no -i)
agent-browser diff snapshot                  # compare with previous snapshot
agent-browser diff screenshot               # visual diff with previous
```

### Environment Variation

```bash
agent-browser set viewport 375 812           # mobile dimensions
agent-browser set viewport 768 1024          # tablet
agent-browser set viewport 1280 800          # desktop
agent-browser set device "iPhone 14"         # device emulation with UA
```

## Ref Lifecycle

Refs (`@e1`, `@e2`, etc.) are **invalidated** when:

- Page navigates to a new URL
- Form submission triggers a page reload
- Dynamic content updates the DOM (SPA route change, modal open/close, list re-render)

**Rule: always re-snapshot after any action that changes the DOM.** Using a stale ref produces silent failures or targets the wrong element.

## Session Isolation

Use named sessions for clean reproduction:

```bash
agent-browser open "http://localhost:3000" --session "clean-repro"
# ... reproduce steps ...
agent-browser close --session "clean-repro"
```

- Named sessions isolate cookies, localStorage, and browser state
- Use a fresh session when verifying that a bug reproduces without existing state
- Compare behavior between a clean session and a profile-based session to identify state-dependent bugs
- Always close sessions when done to avoid leaked processes

## Authentication Patterns

For authenticated flows:

```bash
# Persistent profile — retains login across sessions
agent-browser open "http://localhost:3000" --profile "dev-account"

# Session save/restore — snapshot auth state for reuse
agent-browser state save auth-state.json
agent-browser state load auth-state.json
```

Use persistent profiles for repeated investigation of authenticated pages. Use state save/restore when sharing reproduction steps with other agents.

## Error Recovery

| Symptom | Cause | Action |
|---------|-------|--------|
| "Element not found" after click | Stale ref | Re-snapshot, use new ref |
| Timeout on `wait` | Page never reaches expected state | Check network tab, verify URL |
| Wrong element targeted | Ref shifted after partial DOM update | Re-snapshot, verify ref visually |
| "No browser session" | Daemon not running or session closed | Re-open with `agent-browser open` |

## Headless vs Real Chrome

| Mode | When to use |
|------|------------|
| Headless (default) | CI-like environments, automated evidence collection |
| `--headed` | Debugging visual issues, testing with extensions, persistent profiles |

In headless mode, screenshots are the primary visual evidence. In real Chrome mode, the investigator can also observe the browser directly.
