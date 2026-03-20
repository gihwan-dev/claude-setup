# Browser Testing Patterns

Practical guidance tailored to the repository's Vitest Browser Mode + Portable Stories setup.

## 1. Environment Overview

| Item | Setting |
|------|------|
| Engine | Vitest Browser Mode (Playwright-based, headless) |
| File pattern | `*.browser.test.tsx` |
| Run command | `pnpm test:browser` |
| Viewport | 1280×720 |

## 2. Portable Stories Pattern

Use `composeStories` to turn Storybook stories into test components. **Story args are the test data**, so do not create separate data directly inside the test file.

```typescript
import { composeStories } from '@storybook/react-vite';
import * as stories from './<Feature>.stories';

const { Default, Controlled, Uncontrolled } = composeStories(stories);
```

- If a story does not exist, **create the story first**
- Options not supplied by `args` may be overridden in the test: `<Default options={{ sortable: { use: true } }} />`

## 3. Page Object Model Pattern

Encapsulate DOM queries in helper classes.

**Rules:**
- Do not use `querySelector` directly inside test code
- If a needed method does not exist, **add it to the helper first and then use it**
- When selectors change, updating the helper should update all tests

```typescript
// ❌ Direct query inside the test
const header = container.querySelector('[role="columnheader"]');

// ✅ Access through the helper
const tester = new SomeTester(container);
const header = tester.getHeaderByText('Name');
```

## 4. Rendering and Stabilization

```typescript
const { container } = render(<Default />);
await wait(RENDER_WAIT_TIME); // DOM stabilization (for example, virtualized tables)
const tester = new SomeTester(container);
```

- Use `wait` when the DOM needs to stabilize because of virtualization or async rendering
- Avoid unnecessary `wait` usage; use it only when required
- Declare `RENDER_WAIT_TIME` as a constant near the top of the `describe` block

## 5. User Interaction Patterns

### Click / Keyboard

```typescript
import { fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Click
fireEvent.click(element);

// Typing
await userEvent.type(input, 'search text');

// Keyboard
await userEvent.keyboard('{Enter}');
```

### Drag (Pointer Events)

```typescript
// pointerDown -> pointerMove -> pointerUp sequence
fireEvent.pointerDown(element, {
  pointerId: 1, clientX: 100, clientY: 100,
  button: 0, pointerType: 'mouse',
});
fireEvent.pointerMove(document, {
  pointerId: 1, clientX: 100, clientY: 200,
});
fireEvent.pointerUp(document, {
  pointerId: 1, clientX: 100, clientY: 200,
});
```

- For drag flows, target `pointerMove` and `pointerUp` at `document` (per dnd-kit behavior)
- Always provide `pointerId`, `button`, and `pointerType`

## 6. Controlled vs Uncontrolled Mode Tests

These two modes must be tested separately.

| Mode | Validation points |
|------|-----------|
| Controlled | Synchronization with external state, `onChange` callback invocation |
| Uncontrolled | `initial*` defaults applied, internal state changes |

```typescript
describe('controlled mode', () => {
  it('reflects external state changes in the table', async () => { /* ... */ });
  it('calls the onChange callback', async () => { /* ... */ });
});

describe('uncontrolled mode', () => {
  it('applies the initial value', async () => { /* ... */ });
  it('updates state through user interaction', async () => { /* ... */ });
});
```

## 7. Style / Computed Property Verification

```typescript
// Verify computed styles
const styles = window.getComputedStyle(element);
expect(styles.left).not.toBe('auto');
expect(styles.position).toBe('sticky');

// Verify data attributes
expect(element).toHaveAttribute('data-pinned', 'true');

// Verify aria attributes
expect(header).toHaveAttribute('aria-sort', 'ascending');
```

## 8. Test Structure Template

```typescript
import { composeStories } from '@storybook/react-vite';
import { fireEvent, render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

// Helper imports (adjust to the project)
import * as stories from './<Feature>.stories';

const { Default, Controlled, Uncontrolled } = composeStories(stories);

describe('<Feature Name>', () => {
  const RENDER_WAIT_TIME = 100;

  describe('default behavior', () => {
    it('<core behavior description>', async () => {
      const { container } = render(<Default />);
      await wait(RENDER_WAIT_TIME);
      // Arrange -> Act -> Assert
    });
  });

  describe('controlled mode', () => {
    it('stays in sync with external state', async () => { /* ... */ });
  });

  describe('uncontrolled mode', () => {
    it('applies the initial value', async () => { /* ... */ });
  });

  describe('feature compatibility', () => {
    it('[controlled] feature A + feature B', async () => { /* ... */ });
    it('[uncontrolled] feature A + feature B', async () => { /* ... */ });
  });
});
```
