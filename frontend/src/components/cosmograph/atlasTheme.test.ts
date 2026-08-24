import { describe, expect, it } from 'vitest';

import { ATLAS_THEME } from './atlasTheme';

function rgb(hex: string): [number, number, number] {
  const normalized = hex.replace('#', '');
  return [0, 2, 4].map((offset) => Number.parseInt(normalized.slice(offset, offset + 2), 16)) as [
    number,
    number,
    number,
  ];
}

function luminance(hex: string): number {
  const channels = rgb(hex).map((channel) => {
    const value = channel / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrast(a: string, b: string): number {
  const [lighter, darker] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (lighter + 0.05) / (darker + 0.05);
}

describe('light Atlas colour contract', () => {
  it('keeps every semantic node signal above the non-text contrast floor', () => {
    Object.values(ATLAS_THEME.nodes).forEach((colour) => {
      expect(contrast(colour, ATLAS_THEME.surface)).toBeGreaterThanOrEqual(3);
    });
  });

  it('keeps primary ink at enhanced text contrast on both light surfaces', () => {
    expect(contrast(ATLAS_THEME.ink, ATLAS_THEME.surface)).toBeGreaterThanOrEqual(7);
    expect(contrast(ATLAS_THEME.ink, ATLAS_THEME.panel)).toBeGreaterThanOrEqual(7);
  });
});
