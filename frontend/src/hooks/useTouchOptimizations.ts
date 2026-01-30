/**
 * useTouchOptimizations Hook
 * Provides touch gesture utilities and optimizations for mobile devices
 * Part of EleutherIA mobile UI redesign - Week 3 Performance
 */

import { useRef, useCallback } from 'react';
import { useDevice } from '../context/DeviceContext';

/**
 * Touch gesture configuration
 */
interface TouchGestureConfig {
  /** Minimum distance in pixels to register as a swipe */
  swipeThreshold?: number;

  /** Maximum time in ms for a tap */
  tapThreshold?: number;

  /** Minimum scale change to register as pinch */
  pinchThreshold?: number;

  /** Enable haptic feedback */
  enableHaptics?: boolean;
}

/**
 * Touch gesture callbacks
 */
interface TouchGestureHandlers {
  onTap?: (x: number, y: number) => void;
  onDoubleTap?: (x: number, y: number) => void;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  onPinchStart?: (scale: number) => void;
  onPinch?: (scale: number) => void;
  onPinchEnd?: (scale: number) => void;
  onLongPress?: (x: number, y: number) => void;
}

/**
 * useTouchGestures Hook
 * Detects common touch gestures on an element
 */
export function useTouchGestures(
  handlers: TouchGestureHandlers = {},
  config: TouchGestureConfig = {}
) {
  const { isTouchDevice } = useDevice();
  const touchStartRef = useRef<{ x: number; y: number; time: number } | null>(null);
  const lastTapRef = useRef<number>(0);
  const longPressTimerRef = useRef<number | null>(null);
  const initialDistanceRef = useRef<number>(0);

  const {
    swipeThreshold = 50,
    tapThreshold = 300,
    pinchThreshold = 0.1,
    enableHaptics = true,
  } = config;

  // Haptic feedback utility
  const triggerHaptic = useCallback((type: 'light' | 'medium' | 'heavy' = 'light') => {
    if (!enableHaptics || !isTouchDevice) return;

    // Use Vibration API (fallback for browsers without Haptic API)
    if ('vibrate' in navigator) {
      const patterns = {
        light: 10,
        medium: 20,
        heavy: 30,
      };
      navigator.vibrate(patterns[type]);
    }
  }, [enableHaptics, isTouchDevice]);

  const handleTouchStart = useCallback((e: TouchEvent) => {
    const touch = e.touches[0];
    touchStartRef.current = {
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now(),
    };

    // Setup long press detection
    if (handlers.onLongPress) {
      longPressTimerRef.current = window.setTimeout(() => {
        if (touchStartRef.current) {
          triggerHaptic('medium');
          handlers.onLongPress?.(touchStartRef.current.x, touchStartRef.current.y);
        }
      }, 500);
    }

    // Handle pinch start (two fingers)
    if (e.touches.length === 2) {
      const touch1 = e.touches[0];
      const touch2 = e.touches[1];
      const distance = Math.hypot(
        touch2.clientX - touch1.clientX,
        touch2.clientY - touch1.clientY
      );
      initialDistanceRef.current = distance;
      handlers.onPinchStart?.(1.0);
    }
  }, [handlers, triggerHaptic]);

  const handleTouchMove = useCallback((e: TouchEvent) => {
    // Cancel long press if finger moves
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }

    // Handle pinch gesture
    if (e.touches.length === 2 && initialDistanceRef.current > 0) {
      const touch1 = e.touches[0];
      const touch2 = e.touches[1];
      const distance = Math.hypot(
        touch2.clientX - touch1.clientX,
        touch2.clientY - touch1.clientY
      );
      const scale = distance / initialDistanceRef.current;

      if (Math.abs(scale - 1) > pinchThreshold) {
        handlers.onPinch?.(scale);
      }
    }
  }, [handlers, pinchThreshold]);

  const handleTouchEnd = useCallback((e: TouchEvent) => {
    // Clear long press timer
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }

    if (!touchStartRef.current) return;

    const touch = e.changedTouches[0];
    const deltaX = touch.clientX - touchStartRef.current.x;
    const deltaY = touch.clientY - touchStartRef.current.y;
    const deltaTime = Date.now() - touchStartRef.current.time;
    const distance = Math.hypot(deltaX, deltaY);

    // Handle pinch end
    if (initialDistanceRef.current > 0) {
      handlers.onPinchEnd?.(1.0);
      initialDistanceRef.current = 0;
      return;
    }

    // Tap or swipe?
    if (deltaTime < tapThreshold && distance < 10) {
      // Check for double tap
      const now = Date.now();
      if (now - lastTapRef.current < 300) {
        triggerHaptic('light');
        handlers.onDoubleTap?.(touch.clientX, touch.clientY);
        lastTapRef.current = 0;
      } else {
        triggerHaptic('light');
        handlers.onTap?.(touch.clientX, touch.clientY);
        lastTapRef.current = now;
      }
    } else if (distance > swipeThreshold) {
      // Determine swipe direction
      const isHorizontal = Math.abs(deltaX) > Math.abs(deltaY);

      if (isHorizontal) {
        if (deltaX > 0) {
          triggerHaptic('medium');
          handlers.onSwipeRight?.();
        } else {
          triggerHaptic('medium');
          handlers.onSwipeLeft?.();
        }
      } else {
        if (deltaY > 0) {
          triggerHaptic('medium');
          handlers.onSwipeDown?.();
        } else {
          triggerHaptic('medium');
          handlers.onSwipeUp?.();
        }
      }
    }

    touchStartRef.current = null;
  }, [handlers, tapThreshold, swipeThreshold, triggerHaptic]);

  return {
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    triggerHaptic,
  };
}

/**
 * useCytoscapeTouchOptimizations Hook
 * Optimizes Cytoscape.js for touch devices
 */
export function useCytoscapeTouchOptimizations() {
  const { isTouchDevice } = useDevice();

  const getCytoscapeConfig = useCallback(() => {
    if (!isTouchDevice) {
      return {};
    }

    return {
      // Touch optimizations
      touchTapThreshold: 8,
      desktopTapThreshold: 4,

      // Smoother panning on touch
      minZoom: 0.1,
      maxZoom: 5,
      wheelSensitivity: 0.15,

      // Better touch interaction
      boxSelectionEnabled: false, // Disable on mobile for better single-node selection
      selectionType: 'single',

      // Performance optimizations
      hideEdgesOnViewport: true, // Hide edges during pan/zoom for performance
      textureOnViewport: true, // Use texture rendering during pan/zoom
      motionBlur: false, // Disable motion blur on mobile for performance
      pixelRatio: 'auto',
    };
  }, [isTouchDevice]);

  return { getCytoscapeConfig, isTouchDevice };
}

/**
 * Haptic feedback utility
 * Provides standardized haptic feedback across the app
 */
export function useHapticFeedback() {
  const { isTouchDevice } = useDevice();

  const triggerHaptic = useCallback((type: 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error' = 'light') => {
    if (!isTouchDevice) return;

    // Map feedback types to vibration patterns
    const patterns: Record<string, number | number[]> = {
      light: 10,
      medium: 20,
      heavy: 30,
      success: [10, 50, 10],
      warning: [20, 50, 20],
      error: [30, 100, 30, 100, 30],
    };

    if ('vibrate' in navigator) {
      navigator.vibrate(patterns[type]);
    }
  }, [isTouchDevice]);

  return { triggerHaptic };
}
