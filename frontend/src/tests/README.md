# Frontend Tests

Comprehensive test suite for the Ancient Free Will Database frontend.

## Structure

```
src/tests/
├── setup.ts                  # Test setup and global mocks
├── utils/                    # Utility function tests
│   └── api.test.ts
├── components/               # Component tests
│   └── HomePage.test.tsx
├── hooks/                    # Custom hook tests
│   └── useKeepAlive.test.ts
└── README.md                 # This file
```

## Running Tests

### All Tests
```bash
npm test
```

### Watch Mode
```bash
npm test -- --watch
```

### UI Mode
```bash
npm run test:ui
```

### Coverage Report
```bash
npm run test:coverage
```

Then open `coverage/index.html` in your browser.

### Specific Test File
```bash
npm test src/tests/components/HomePage.test.tsx
```

## Writing Tests

### Component Test Example

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MyComponent from '@/components/MyComponent';

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('should handle user interaction', async () => {
    const { user } = render(<MyComponent />);
    await user.click(screen.getByRole('button'));
    expect(screen.getByText('Clicked')).toBeInTheDocument();
  });
});
```

### Hook Test Example

```tsx
import { renderHook } from '@testing-library/react';
import useMyHook from '@/hooks/useMyHook';

describe('useMyHook', () => {
  it('should return initial value', () => {
    const { result } = renderHook(() => useMyHook());
    expect(result.current.value).toBe(0);
  });
});
```

### Async Test Example

```tsx
import { waitFor } from '@testing-library/react';

it('should load data', async () => {
  render(<DataComponent />);

  await waitFor(() => {
    expect(screen.getByText('Loaded')).toBeInTheDocument();
  });
});
```

## Testing Library Queries

Priority order (use higher priority when possible):

1. `getByRole` - Accessibility-friendly
2. `getByLabelText` - Forms
3. `getByPlaceholderText` - Forms
4. `getByText` - Non-interactive content
5. `getByTestId` - Last resort

## Mocking

### Mock API Calls

```tsx
import { vi } from 'vitest';
import axios from 'axios';

vi.mock('axios');

(axios.get as any).mockResolvedValue({ data: mockData });
```

### Mock Router

```tsx
import { BrowserRouter } from 'react-router-dom';

render(
  <BrowserRouter>
    <Component />
  </BrowserRouter>
);
```

### Mock Context

```tsx
import { AuthContext } from '@/contexts/AuthContext';

const mockAuthValue = {
  user: { id: 1, username: 'test' },
  login: vi.fn(),
  logout: vi.fn(),
};

render(
  <AuthContext.Provider value={mockAuthValue}>
    <Component />
  </AuthContext.Provider>
);
```

## Coverage Goals

- **Components**: >70% coverage
- **Utilities**: >80% coverage
- **Hooks**: >75% coverage

## Best Practices

1. **Accessibility**: Test with roles and labels
2. **User Behavior**: Test user interactions, not implementation
3. **Isolation**: Each test should be independent
4. **Cleanup**: Tests clean up automatically via setup.ts
5. **Async**: Use `waitFor` and `findBy` for async operations
6. **Mocks**: Mock external dependencies (API, localStorage, etc.)

## Troubleshooting

### Tests failing with "not wrapped in act(...)"

Use `waitFor` or `findBy` for async updates:
```tsx
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument();
});
```

### Canvas/D3 errors

Mock D3 visualizations:
```tsx
vi.mock('d3', () => ({
  select: vi.fn(() => ({ ... })),
}));
```

### Router errors

Wrap components in `<BrowserRouter>`:
```tsx
render(
  <BrowserRouter>
    <Component />
  </BrowserRouter>
);
```

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Testing Library Queries](https://testing-library.com/docs/queries/about)
- [Common Mistakes](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
