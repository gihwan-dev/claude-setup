# Table Component Testing

Testing patterns and rules specialized for the Table component (`packages/react/src/table`).

## 1. How to Use `TableTester`

**File location**: `packages/react/src/table/spec/helpers/TableTester.ts`

This helper class follows the Page Object Model pattern and encapsulates table-related DOM queries.

### Key API

| Category | API | Description |
|---------|-----|------|
| Base elements | `table` | `[role="table"]` element |
| | `headers` | `[role="columnheader"]` elements |
| | `cells` | `[role="cell"]`, `[role="gridcell"]` elements |
| | `scrollViewport` | Scroll viewport element |
| | `searchInput` | Search input |
| | `toolbar` | Table toolbar |
| | `optionsButton` | Options menu button |
| Row queries | `getRows(includeHeader?)` | Row elements (with or without header) |
| | `getRowCells(row)` | Cells in a specific row |
| | `renderedRowCount` | Number of rendered data rows (excluding header) |
| | `domNodeCount` | Total DOM node count |
| Header / sorting | `getHeaderByText(text)` | Find a header by text |
| | `getSortButton(headerText)` | Find a sort button |
| | `getAriaSortValue(headerText)` | Read the `aria-sort` value |
| | `getColumnValues(index)` | Extract all cell values from a column |
| Selection | `checkboxes` | Checkbox elements |
| | `radioButtons` | Radio button elements |
| | `isChecked(element)` | Check selected state |
| | `isIndeterminate(element)` | Check indeterminate state |
| Expansion | `expanders` | Expand buttons |
| Pinning | `getPinnedRows()` | Pinned rows |
| | `getUnpinnedRows()` | Unpinned rows |
| Row ordering | `getMoveUpButton()` | Move-up button |
| | `getMoveDownButton()` | Move-down button |
| | `hasCursorGrab(element)` | Whether drag cursor styling is present |
| Pagination | `pagination.nav` | Navigation element |
| | `pagination.prevButton` | Previous-page button |
| | `pagination.nextButton` | Next-page button |
| | `pagination.getPageButton(n)` | Page button `n` |
| Utilities | `getButtonByText(text)` | Find button by text |
| | `isAriaDisabled(element)` | Check `aria-disabled` |
| | `isScrollable(element)` | Check scrollability |

### Extension Rule

If `TableTester` does not expose a method you need, **do not implement it directly in the test. Add the method to `TableTester` first and then use it.**

## 2. Browser Tests — File Rules

### File location

```text
packages/react/src/table/spec/<Feature>/
├── <Feature>.stories.tsx          # Story (source of test data)
├── <Feature>.browser.test.tsx     # Browser test
└── <Feature>.mdx                  # Spec document (optional)
```

### Import pattern

```typescript
import { composeStories } from '@storybook/react-vite';
import { fireEvent, render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { TableTester, wait } from '../helpers';
import * as stories from './<Feature>.stories';

const { Default, Controlled, Uncontrolled } = composeStories(stories);
```

### Basic rendering pattern

```typescript
it('renders the table correctly', async () => {
  const { container } = render(<Default />);
  await wait(RENDER_WAIT_TIME);
  const tester = new TableTester(container);

  expect(tester.table).toBeInTheDocument();
  expect(tester.renderedRowCount).toBe(10);
});
```

## 3. Browser Tests — Feature Compatibility Matrix

### Principles

1. **Test only 1:1 combinations**: the current feature plus **one** other feature
   - O: RowOrdering + Sorting
   - X: RowOrdering + Sorting + Pagination (do not test triple combinations at once)

2. **Priority order**:

   | Priority | Standard | Example |
   |---------|------|------|
   | **Required** | Combinations marked △ (limited compatibility) | RowSelection + RowExpansion |
   | **Recommended** | Common combinations used together often | Sorting + Pagination |
   | **Optional** | Remaining O (fully compatible) combinations | Add if needed |

3. **Test controlled and uncontrolled modes separately**

4. **Expected test volume**: 5-7 combinations × 2 (controlled / uncontrolled) × 2 (basic + compatibility) = 20-28 tests per major feature

### Compatibility test structure

```typescript
describe('feature compatibility', () => {
  // △ limited compatibility — required
  it('[controlled] RowOrdering + Sorting work together', async () => {
    const { container } = render(
      <Controlled options={{ sortable: { use: true } }} />
    );
    await wait(RENDER_WAIT_TIME);
    const tester = new TableTester(container);
    // Verify that both features work without conflict
  });

  it('[uncontrolled] RowOrdering + Sorting work together', async () => {
    // Same verification in uncontrolled mode
  });
});
```

## 4. Unit Tests — Custom Feature Tests

### File location

```text
packages/react/src/table/features/__test__/<Feature>.spec.ts
```

### Mock Table / Row creation pattern

```typescript
function createMockRow(id: string, original: TestData) {
  return {
    id,
    original,
    index: Number.parseInt(id) - 1,
    getParentRow: () => null,
    // ... required methods
  };
}

function createMockTable(overrides = {}) {
  const data = overrides.data ?? defaultData;
  const rows = data.map((d) => createMockRow(String(d.id), d));

  const state = {
    // State fields for the feature
  };

  const onChangeCallback = vi.fn();

  const table = {
    getState: () => state,
    setState: vi.fn((updater) => {
      const newState = typeof updater === 'function' ? updater(state) : updater;
      Object.assign(state, newState);
    }),
    getRowModel: () => ({ flatRows: rows, rows }),
    options: {
      onFeatureChange: onChangeCallback,
    },
  };

  // Inject methods into the table through the feature's createTable
  featureCreateTable(table);

  return { table, onChangeCallback };
}
```

### Contravariance workaround

When passing a mock object into `createTable` under TanStack Table's type system:

```typescript
const featureCreateTable = Feature.createTable! as (table: any) => void;
```

### Test scope

| Target | Validation point |
|------|-----------|
| `getDefaultOptions` | Are the default option values correct? |
| State-change functions | Are `setState` and `onChange` callbacks called correctly? |
| Row methods | Do methods injected through `createRow` work correctly? |
| Edge conditions | First row, last row, empty data, tree structures, etc. |

## 5. Unit Tests — Utility Function Tests

### File location

```text
packages/react/src/table/utils/__test__/<util>.spec.ts
```

### Characteristics

- **Pure-function first** — validate inputs and outputs only
- Focus on edge cases: empty data, boundary values, overflow, tree structures, etc.
- Keep mocks minimal — create only the data needed to satisfy the function's parameter types

```typescript
describe('computeAllMerges', () => {
  it('returns an empty result for empty data', () => {
    const table = createMockTable({ rows: [] });
    const result = computeAllMerges(table);
    expect(result.rowSpanMap.size).toBe(0);
    expect(result.colSpanMap.size).toBe(0);
  });

  it('clamps rowSpan when it exceeds the number of rows', () => {
    const table = createMockTable({
      rows: [
        { id: '1', original: { colA: 'val', rowSpan: { colA: 5 } } },
        { id: '2', original: { colA: 'val' } },
      ],
    });
    const result = computeAllMerges(table);
    // rowSpan is 5, but only 2 rows exist, so it is clamped to 2
    expect(result.rowSpanMap.get('0:colA')).toBe(2);
  });
});
```

## 6. Shared Test Helper Utilities

Shared utilities provided in `packages/react/src/table/spec/helpers/`:

| Utility | Location | Purpose |
|---------|------|------|
| `TableTester` | `testHelpers.ts` | DOM query helper (Page Object Model) |
| `wait(ms)` | `testHelpers.ts` | Wait for DOM stabilization |
| `generateDeterministicEmployeeData(count)` | `utils.ts` | Generate deterministic test data |
| `generateEmployeeData(count)` | `utils.ts` | Generate random employee data |
| `generateHierarchicalData(levels, nodes)` | `utils.ts` | Generate tree-structured data |
| `BASIC_COLUMNS` | `utils.ts` | Basic column preset (ID, name, department, title) |
| `EMPLOYEE_COLUMNS` | `utils.ts` | Employee column preset (basic + email, salary, status) |
| `FULL_COLUMNS` | `utils.ts` | Full column preset (employee + phone number, hire date) |
| `useRowSelectionHandler` | `utils.ts` | Row selection state handler hook |
| `useSortingHandler` | `utils.ts` | Sorting state handler hook |
| `usePaginationHandler` | `utils.ts` | Pagination state handler hook |
| `useExpandedHandler` | `utils.ts` | Expanded-state handler hook |
| `COMPATIBILITY_MATRIX` | `compatibilityData.ts` | Feature compatibility matrix |
