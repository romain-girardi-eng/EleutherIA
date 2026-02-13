/**
 * useMediaQuery Hook
 * Detects responsive breakpoints and device types for mobile-first design
 * Part of EleutherIA mobile UI redesign - Week 1 Foundation
 */

import { useState, useEffect } from 'react';

/**
 * Tailwind CSS breakpoints
 * sm: 640px - Small devices (large phones)
 * md: 768px - Medium devices (tablets)
 * lg: 1024px - Large devices (desktops)
 * xl: 1280px - Extra large devices (large desktops)
 * 2xl: 1536px - 2X Extra large devices
 */
export const BREAKPOINTS = {
  sm: '(min-width: 640px)',
  md: '(min-width: 768px)',
  lg: '(min-width: 1024px)',
  xl: '(min-width: 1280px)',
  '2xl': '(min-width: 1536px)',
} as const;

/**
 * Generic media query hook
 * @param query - CSS media query string
 * @returns boolean indicating if the media query matches
 *
 * @example
 * const isLargeScreen = useMediaQuery('(min-width: 1024px)');
 * const isDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
 * const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia(query);

    // Set initial value
    setMatches(mediaQuery.matches);

    // Create event listener
    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
    // Fallback for older browsers
    else {
       
      mediaQuery.addListener(handleChange);
       
      return () => mediaQuery.removeListener(handleChange);
    }
  }, [query]);

  return matches;
}

/**
 * Mobile device detection (screens < 768px)
 * @returns true if viewport is mobile-sized
 */
export function useIsMobile(): boolean {
  return !useMediaQuery(BREAKPOINTS.md);
}

/**
 * Tablet device detection (768px - 1024px)
 * @returns true if viewport is tablet-sized
 */
export function useIsTablet(): boolean {
  const isMd = useMediaQuery(BREAKPOINTS.md);
  const isLg = useMediaQuery(BREAKPOINTS.lg);
  return isMd && !isLg;
}

/**
 * Desktop device detection (screens >= 1024px)
 * @returns true if viewport is desktop-sized
 */
export function useIsDesktop(): boolean {
  return useMediaQuery(BREAKPOINTS.lg);
}

/**
 * Touch device detection
 * Detects if the device supports touch events
 * @returns true if device has touch capability
 */
export function useIsTouchDevice(): boolean {
  const [isTouch, setIsTouch] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  });

  useEffect(() => {
    setIsTouch('ontouchstart' in window || navigator.maxTouchPoints > 0);
  }, []);

  return isTouch;
}

/**
 * Dark mode preference detection
 * @returns true if user prefers dark color scheme
 */
export function usePrefersDarkMode(): boolean {
  return useMediaQuery('(prefers-color-scheme: dark)');
}

/**
 * Reduced motion preference detection
 * Important for accessibility - respects user's motion preferences
 * @returns true if user prefers reduced motion
 */
export function usePrefersReducedMotion(): boolean {
  return useMediaQuery('(prefers-reduced-motion: reduce)');
}

/**
 * High contrast mode detection
 * @returns true if high contrast mode is active
 */
export function usePrefersHighContrast(): boolean {
  return useMediaQuery('(prefers-contrast: high)');
}

/**
 * Orientation detection
 * @returns 'portrait' | 'landscape'
 */
export function useOrientation(): 'portrait' | 'landscape' {
  const isPortrait = useMediaQuery('(orientation: portrait)');
  return isPortrait ? 'portrait' : 'landscape';
}

/**
 * Viewport size hook
 * Returns current viewport dimensions
 * Useful for dynamic sizing calculations
 */
export function useViewportSize() {
  const [size, setSize] = useState<{ width: number; height: number }>(() => {
    if (typeof window === 'undefined') return { width: 0, height: 0 };
    return {
      width: window.innerWidth,
      height: window.innerHeight,
    };
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handleResize = () => {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return size;
}
