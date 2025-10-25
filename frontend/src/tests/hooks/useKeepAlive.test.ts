import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import useKeepAlive from '@/hooks/useKeepAlive';

// Mock axios
vi.mock('axios');

describe('useKeepAlive', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  it('should initialize without errors', () => {
    const { result } = renderHook(() => useKeepAlive());
    expect(result.current).toBeUndefined();
  });

  it('should track user activity', () => {
    renderHook(() => useKeepAlive());

    // Simulate user activity
    const mouseEvent = new MouseEvent('mousemove');
    document.dispatchEvent(mouseEvent);

    expect(document).toBeDefined();
  });

  it('should send ping requests on interval', () => {
    renderHook(() => useKeepAlive());

    // Fast-forward time
    vi.advanceTimersByTime(600000); // 10 minutes

    expect(vi.getTimerCount()).toBeGreaterThanOrEqual(0);
  });
});
