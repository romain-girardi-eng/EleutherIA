'use client';

import { useCallback, useRef, useState } from 'react';
import { prepare, layout } from '@chenglou/pretext';
import type { PageConfig } from './types';

interface CalibrationResult {
  correctionRatio: number;
  calibrated: boolean;
}

interface UseCalibrationReturn extends CalibrationResult {
  calibrate: (sampleText: string) => void;
  hiddenRef: React.RefCallback<HTMLDivElement>;
}

// Build a CSS font string from config, matching what Pretext expects.
function buildFont(fontSize: number, fontFamily: string): string {
  return `${fontSize}px ${fontFamily}`;
}

export function useCalibration(config: PageConfig): UseCalibrationReturn {
  const [result, setResult] = useState<CalibrationResult>({
    correctionRatio: 1,
    calibrated: false,
  });
  const sampleTextRef = useRef<string>('');
  const hiddenElRef = useRef<HTMLDivElement | null>(null);

  const performCalibration = useCallback(
    (el: HTMLDivElement, text: string) => {
      // Measure DOM height by rendering the sample text in a hidden element
      // styled to match the exact layout conditions.
      el.style.cssText = `
        position: absolute;
        visibility: hidden;
        pointer-events: none;
        width: ${config.width}px;
        font-family: ${config.fontFamily};
        font-size: ${config.fontSize}px;
        line-height: ${config.lineHeight};
        white-space: pre-wrap;
        word-wrap: break-word;
      `;
      el.textContent = text;
      const domHeight = el.getBoundingClientRect().height;

      // Measure with Pretext: prepare() segments and measures widths via canvas,
      // layout() computes line count and height using pure arithmetic.
      const font = buildFont(config.fontSize, config.fontFamily);
      const lineHeightPx = config.fontSize * config.lineHeight;
      const prepared = prepare(text, font);
      const { height: pretextHeight } = layout(prepared, config.width, lineHeightPx);

      // Avoid division by zero; fall back to ratio 1 if Pretext reports nothing.
      const ratio = pretextHeight > 0 ? domHeight / pretextHeight : 1;
      setResult({ correctionRatio: ratio, calibrated: true });
    },
    [config.width, config.fontSize, config.lineHeight, config.fontFamily],
  );

  const hiddenRef = useCallback<React.RefCallback<HTMLDivElement>>(
    (node) => {
      hiddenElRef.current = node;
      if (node && sampleTextRef.current) {
        performCalibration(node, sampleTextRef.current);
      }
    },
    // Re-run when config changes so the hidden element gets re-measured.
    [performCalibration],
  );

  const calibrate = useCallback(
    (sampleText: string) => {
      sampleTextRef.current = sampleText;
      if (hiddenElRef.current) {
        performCalibration(hiddenElRef.current, sampleText);
      }
    },
    [performCalibration],
  );

  return { ...result, calibrate, hiddenRef };
}
