import { useEffect, useRef } from 'react';

interface AccessibilityViolation {
  id: string;
  impact: 'critical' | 'serious' | 'moderate' | 'minor';
  description: string;
  help: string;
  helpUrl: string;
  nodes: Array<{
    target: string[];
    html: string;
    failureSummary: string;
  }>;
}

interface AuditReport {
  violations: AccessibilityViolation[];
  passes: number;
  incomplete: number;
  timestamp: Date;
}

/**
 * Hook to run axe-core accessibility audits in development
 * Reports violations to console and optionally to a callback
 */
export function useAccessibilityAudit(
  options: {
    enabled?: boolean;
    onReport?: (report: AuditReport) => void;
    runInterval?: number; // milliseconds
  } = {}
) {
  const { enabled = process.env.NODE_ENV === 'development', onReport, runInterval = 0 } = options;

  const lastRunRef = useRef<number>(0);
  const timeoutRef = useRef<number | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const runAudit = async () => {
      // Dynamically import axe-core only in development
      const axe = await import('@axe-core/react');
      const React = await import('react');
      const ReactDOM = await import('react-dom');

      // Run axe audit
      await axe.default(React, ReactDOM, 1000);
    };

    // Initial audit after page load
    const initialTimeout = setTimeout(() => {
      runAudit().catch(console.error);
      lastRunRef.current = Date.now();
    }, 2000);

    // Optional periodic audits
    if (runInterval > 0) {
      timeoutRef.current = window.setInterval(() => {
        runAudit().catch(console.error);
      }, runInterval);
    }

    return () => {
      clearTimeout(initialTimeout);
      if (timeoutRef.current) {
        clearInterval(timeoutRef.current);
      }
    };
  }, [enabled, runInterval, onReport]);
}

/**
 * Manual accessibility audit runner
 * Can be called programmatically
 */
export async function runAccessibilityAudit(): Promise<AuditReport | null> {
  if (typeof window === 'undefined') return null;

  try {
    const axeCore = await import('axe-core');

    const results = await axeCore.default.run(document.body, {
      rules: {
        // Focus on WCAG 2.1 AA compliance
        'color-contrast': { enabled: true },
        'heading-order': { enabled: true },
        'image-alt': { enabled: true },
        'label': { enabled: true },
        'link-name': { enabled: true },
        'button-name': { enabled: true },
        'landmark-one-main': { enabled: true },
        'region': { enabled: true },
        'bypass': { enabled: true },
      },
    });

    const report: AuditReport = {
      violations: results.violations.map((v) => ({
        id: v.id,
        impact: v.impact as AccessibilityViolation['impact'],
        description: v.description,
        help: v.help,
        helpUrl: v.helpUrl,
        nodes: v.nodes.map((n) => ({
          target: n.target as string[],
          html: n.html,
          failureSummary: n.failureSummary || '',
        })),
      })),
      passes: results.passes.length,
      incomplete: results.incomplete.length,
      timestamp: new Date(),
    };

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      if (report.violations.length > 0) {
        console.group('🔴 Accessibility Violations Found');
        report.violations.forEach((v) => {
          console.group(`${v.impact.toUpperCase()}: ${v.help}`);
          console.log('Description:', v.description);
          console.log('Help URL:', v.helpUrl);
          console.log('Affected elements:', v.nodes.length);
          v.nodes.forEach((n) => {
            console.log('  - Element:', n.target.join(' > '));
            console.log('    Issue:', n.failureSummary);
          });
          console.groupEnd();
        });
        console.groupEnd();
      } else {
        console.log('✅ No accessibility violations found!');
      }
      console.log(`Passed: ${report.passes}, Incomplete: ${report.incomplete}`);
    }

    return report;
  } catch (error) {
    console.error('Failed to run accessibility audit:', error);
    return null;
  }
}

/**
 * Check if reduced motion is preferred
 */
export function usePrefersReducedMotion(): boolean {
  const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  return mediaQuery.matches;
}

/**
 * Check if high contrast is preferred
 */
export function usePrefersHighContrast(): boolean {
  const mediaQuery = window.matchMedia('(prefers-contrast: more)');
  return mediaQuery.matches;
}

/**
 * Check if user prefers dark mode
 */
export function usePrefersDarkMode(): boolean {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  return mediaQuery.matches;
}

/**
 * Focus trap for modals and dialogs
 */
export function useFocusTrap(containerRef: React.RefObject<HTMLElement>, isActive: boolean) {
  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const container = containerRef.current;
    const focusableElements = container.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);

    // Focus first element when trap is activated
    firstElement.focus();

    return () => {
      container.removeEventListener('keydown', handleKeyDown);
    };
  }, [containerRef, isActive]);
}

/**
 * Announce message to screen readers
 */
export function announceToScreenReader(
  message: string,
  priority: 'polite' | 'assertive' = 'polite'
) {
  const announcement = document.createElement('div');
  announcement.setAttribute('role', 'status');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;

  document.body.appendChild(announcement);

  // Remove after announcement is read
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
}
