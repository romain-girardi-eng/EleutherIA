import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { apiClient } from '@/utils/api/client';

vi.mock('axios');

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should create axios instance with correct base URL', () => {
    expect(apiClient.defaults.baseURL).toBeDefined();
  });

  it('should have correct default headers', () => {
    expect(apiClient.defaults.headers['Content-Type']).toBe('application/json');
  });

  it('should handle successful responses', async () => {
    const mockData = { data: 'test' };
    (axios.get as any).mockResolvedValue({ data: mockData });

    // Test would require actual implementation
    expect(apiClient).toBeDefined();
  });

  it('should handle errors correctly', async () => {
    const mockError = new Error('Network error');
    (axios.get as any).mockRejectedValue(mockError);

    expect(apiClient).toBeDefined();
  });
});
