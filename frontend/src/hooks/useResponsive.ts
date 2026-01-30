import { useState, useEffect, useCallback } from 'react';

export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';

interface ResponsiveState {
  breakpoint: Breakpoint;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  width: number;
  height: number;
  orientation: 'portrait' | 'landscape';
  isTouch: boolean;
}

const breakpoints = {
  xs: 0,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
};

function getBreakpoint(width: number): Breakpoint {
  if (width >= breakpoints['2xl']) return '2xl';
  if (width >= breakpoints.xl) return 'xl';
  if (width >= breakpoints.lg) return 'lg';
  if (width >= breakpoints.md) return 'md';
  if (width >= breakpoints.sm) return 'sm';
  return 'xs';
}

/**
 * Hook for responsive design utilities
 * Provides current breakpoint, device type, and screen dimensions
 */
export function useResponsive(): ResponsiveState {
  const [state, setState] = useState<ResponsiveState>(() => {
    const width = typeof window !== 'undefined' ? window.innerWidth : 1024;
    const height = typeof window !== 'undefined' ? window.innerHeight : 768;

    return {
      breakpoint: getBreakpoint(width),
      isMobile: width < breakpoints.md,
      isTablet: width >= breakpoints.md && width < breakpoints.lg,
      isDesktop: width >= breakpoints.lg,
      width,
      height,
      orientation: width > height ? 'landscape' : 'portrait',
      isTouch: typeof window !== 'undefined' && 'ontouchstart' in window,
    };
  });

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;

      setState({
        breakpoint: getBreakpoint(width),
        isMobile: width < breakpoints.md,
        isTablet: width >= breakpoints.md && width < breakpoints.lg,
        isDesktop: width >= breakpoints.lg,
        width,
        height,
        orientation: width > height ? 'landscape' : 'portrait',
        isTouch: 'ontouchstart' in window,
      });
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
    };
  }, []);

  return state;
}

/**
 * Hook to check if current viewport matches a media query
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);

    const handler = (e: MediaQueryListEvent) => {
      setMatches(e.matches);
    };

    setMatches(mediaQuery.matches);
    mediaQuery.addEventListener('change', handler);

    return () => mediaQuery.removeEventListener('change', handler);
  }, [query]);

  return matches;
}

/**
 * Hook for viewport height (excluding browser UI on mobile)
 * Addresses the "100vh" issue on mobile browsers
 */
export function useViewportHeight(): number {
  const [height, setHeight] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.innerHeight;
    }
    return 768;
  });

  useEffect(() => {
    const updateHeight = () => {
      // Use visualViewport API if available (better mobile support)
      if (window.visualViewport) {
        setHeight(window.visualViewport.height);
      } else {
        setHeight(window.innerHeight);
      }

      // Update CSS custom property for use in styles
      document.documentElement.style.setProperty('--vh', `${window.innerHeight * 0.01}px`);
    };

    updateHeight();

    window.addEventListener('resize', updateHeight);
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', updateHeight);
    }

    return () => {
      window.removeEventListener('resize', updateHeight);
      if (window.visualViewport) {
        window.visualViewport.removeEventListener('resize', updateHeight);
      }
    };
  }, []);

  return height;
}

/**
 * Hook for performance monitoring
 * Tracks key web vitals and performance metrics
 */
export function usePerformanceMetrics() {
  const [metrics, setMetrics] = useState<{
    fcp: number | null;
    lcp: number | null;
    cls: number | null;
    fid: number | null;
    ttfb: number | null;
  }>({
    fcp: null,
    lcp: null,
    cls: null,
    fid: null,
    ttfb: null,
  });

  useEffect(() => {
    // First Contentful Paint
    const fcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const fcpEntry = entries.find((e) => e.name === 'first-contentful-paint');
      if (fcpEntry) {
        setMetrics((prev) => ({ ...prev, fcp: fcpEntry.startTime }));
      }
    });

    // Largest Contentful Paint
    const lcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      if (lastEntry) {
        setMetrics((prev) => ({ ...prev, lcp: lastEntry.startTime }));
      }
    });

    // Cumulative Layout Shift
    let clsValue = 0;
    const clsObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        if (!(entry as unknown as { hadRecentInput: boolean }).hadRecentInput) {
          clsValue += (entry as unknown as { value: number }).value;
        }
      });
      setMetrics((prev) => ({ ...prev, cls: clsValue }));
    });

    // First Input Delay
    const fidObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const fidEntry = entries[0];
      if (fidEntry) {
        setMetrics((prev) => ({
          ...prev,
          fid: (fidEntry as unknown as { processingStart: number }).processingStart - fidEntry.startTime,
        }));
      }
    });

    try {
      fcpObserver.observe({ type: 'paint', buffered: true });
      lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
      clsObserver.observe({ type: 'layout-shift', buffered: true });
      fidObserver.observe({ type: 'first-input', buffered: true });
    } catch (e) {
      console.log('Performance monitoring not supported:', e);
    }

    // Time to First Byte
    const navigationEntries = performance.getEntriesByType('navigation');
    if (navigationEntries.length > 0) {
      const navEntry = navigationEntries[0] as PerformanceNavigationTiming;
      setMetrics((prev) => ({
        ...prev,
        ttfb: navEntry.responseStart - navEntry.requestStart,
      }));
    }

    return () => {
      fcpObserver.disconnect();
      lcpObserver.disconnect();
      clsObserver.disconnect();
      fidObserver.disconnect();
    };
  }, []);

  return metrics;
}

/**
 * Hook for lazy loading images with IntersectionObserver
 */
export function useLazyLoad(
  ref: React.RefObject<HTMLElement>,
  options: {
    threshold?: number;
    rootMargin?: string;
  } = {}
): boolean {
  const [isVisible, setIsVisible] = useState(false);

  const { threshold = 0.1, rootMargin = '50px' } = options;

  useEffect(() => {
    if (!ref.current) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold, rootMargin }
    );

    observer.observe(ref.current);

    return () => observer.disconnect();
  }, [ref, threshold, rootMargin]);

  return isVisible;
}

/**
 * Hook for debounced window resize
 * Prevents excessive re-renders on resize
 */
export function useDebouncedResize(delay: number = 250): {
  width: number;
  height: number;
} {
  const [dimensions, setDimensions] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 1024,
    height: typeof window !== 'undefined' ? window.innerHeight : 768,
  });

  useEffect(() => {
    let timeoutId: number;

    const handleResize = () => {
      clearTimeout(timeoutId);
      timeoutId = window.setTimeout(() => {
        setDimensions({
          width: window.innerWidth,
          height: window.innerHeight,
        });
      }, delay);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      clearTimeout(timeoutId);
    };
  }, [delay]);

  return dimensions;
}

/**
 * Hook for responsive image srcset generation
 */
export function useResponsiveImage(
  baseSrc: string,
  sizes: number[] = [320, 640, 768, 1024, 1280]
): {
  srcSet: string;
  sizes: string;
} {
  const generateSrcSet = useCallback(() => {
    const extension = baseSrc.split('.').pop();
    const baseWithoutExt = baseSrc.replace(`.${extension}`, '');

    const srcSet = sizes
      .map((size) => `${baseWithoutExt}-${size}.${extension} ${size}w`)
      .join(', ');

    const sizesAttr = sizes
      .map((size, index) => {
        if (index === sizes.length - 1) {
          return `${size}px`;
        }
        return `(max-width: ${sizes[index + 1]}px) ${size}px`;
      })
      .join(', ');

    return { srcSet, sizes: sizesAttr };
  }, [baseSrc, sizes]);

  return generateSrcSet();
}

/**
 * Hook for network connection quality
 * Helps with adaptive loading based on connection speed
 */
export function useNetworkQuality(): {
  effectiveType: '4g' | '3g' | '2g' | 'slow-2g' | 'unknown';
  downlink: number;
  rtt: number;
  saveData: boolean;
} {
  const [quality, setQuality] = useState<{
    effectiveType: '4g' | '3g' | '2g' | 'slow-2g' | 'unknown';
    downlink: number;
    rtt: number;
    saveData: boolean;
  }>({
    effectiveType: 'unknown',
    downlink: 10,
    rtt: 50,
    saveData: false,
  });

  useEffect(() => {
    const connection = (navigator as unknown as { connection?: NetworkInformation }).connection;

    interface NetworkInformation {
      effectiveType: '4g' | '3g' | '2g' | 'slow-2g';
      downlink: number;
      rtt: number;
      saveData: boolean;
      addEventListener: (type: string, listener: EventListener) => void;
      removeEventListener: (type: string, listener: EventListener) => void;
    }

    if (connection) {
      const updateQuality = () => {
        setQuality({
          effectiveType: connection.effectiveType || 'unknown',
          downlink: connection.downlink || 10,
          rtt: connection.rtt || 50,
          saveData: connection.saveData || false,
        });
      };

      updateQuality();
      connection.addEventListener('change', updateQuality);

      return () => connection.removeEventListener('change', updateQuality);
    }
  }, []);

  return quality;
}
