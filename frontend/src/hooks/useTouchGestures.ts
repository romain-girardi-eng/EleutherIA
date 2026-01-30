import { useRef, useEffect, useCallback } from 'react';

interface TouchGestureOptions {
  onPinchZoom?: (scale: number, center: { x: number; y: number }) => void;
  onPan?: (dx: number, dy: number) => void;
  onDoubleTap?: (position: { x: number; y: number }) => void;
  onLongPress?: (position: { x: number; y: number }) => void;
  onSwipe?: (direction: 'left' | 'right' | 'up' | 'down') => void;
  longPressDelay?: number;
  swipeThreshold?: number;
}

interface TouchState {
  lastTouchEnd: number;
  touchStartTime: number;
  initialDistance: number;
  initialScale: number;
  lastPanPosition: { x: number; y: number } | null;
  longPressTimer: number | null;
  touchStartPosition: { x: number; y: number } | null;
}

export function useTouchGestures(
  elementRef: React.RefObject<HTMLElement>,
  options: TouchGestureOptions = {}
) {
  const {
    onPinchZoom,
    onPan,
    onDoubleTap,
    onLongPress,
    onSwipe,
    longPressDelay = 500,
    swipeThreshold = 50,
  } = options;

  const state = useRef<TouchState>({
    lastTouchEnd: 0,
    touchStartTime: 0,
    initialDistance: 0,
    initialScale: 1,
    lastPanPosition: null,
    longPressTimer: null,
    touchStartPosition: null,
  });

  const getDistance = useCallback((touches: TouchList): number => {
    if (touches.length < 2) return 0;
    const dx = touches[0].clientX - touches[1].clientX;
    const dy = touches[0].clientY - touches[1].clientY;
    return Math.sqrt(dx * dx + dy * dy);
  }, []);

  const getCenter = useCallback((touches: TouchList): { x: number; y: number } => {
    if (touches.length < 2) {
      return { x: touches[0].clientX, y: touches[0].clientY };
    }
    return {
      x: (touches[0].clientX + touches[1].clientX) / 2,
      y: (touches[0].clientY + touches[1].clientY) / 2,
    };
  }, []);

  const clearLongPressTimer = useCallback(() => {
    if (state.current.longPressTimer !== null) {
      clearTimeout(state.current.longPressTimer);
      state.current.longPressTimer = null;
    }
  }, []);

  const handleTouchStart = useCallback(
    (e: TouchEvent) => {
      clearLongPressTimer();
      state.current.touchStartTime = Date.now();
      state.current.touchStartPosition = {
        x: e.touches[0].clientX,
        y: e.touches[0].clientY,
      };

      if (e.touches.length === 2) {
        // Pinch zoom start
        state.current.initialDistance = getDistance(e.touches);
      } else if (e.touches.length === 1) {
        // Single touch - start pan and long press detection
        state.current.lastPanPosition = {
          x: e.touches[0].clientX,
          y: e.touches[0].clientY,
        };

        if (onLongPress) {
          state.current.longPressTimer = window.setTimeout(() => {
            if (state.current.touchStartPosition) {
              onLongPress(state.current.touchStartPosition);
            }
          }, longPressDelay);
        }
      }
    },
    [getDistance, onLongPress, longPressDelay, clearLongPressTimer]
  );

  const handleTouchMove = useCallback(
    (e: TouchEvent) => {
      clearLongPressTimer();

      if (e.touches.length === 2 && onPinchZoom) {
        // Pinch zoom
        e.preventDefault();
        const currentDistance = getDistance(e.touches);
        if (state.current.initialDistance > 0) {
          const scale = currentDistance / state.current.initialDistance;
          const center = getCenter(e.touches);
          onPinchZoom(scale, center);
        }
      } else if (e.touches.length === 1 && onPan && state.current.lastPanPosition) {
        // Pan
        const dx = e.touches[0].clientX - state.current.lastPanPosition.x;
        const dy = e.touches[0].clientY - state.current.lastPanPosition.y;
        onPan(dx, dy);
        state.current.lastPanPosition = {
          x: e.touches[0].clientX,
          y: e.touches[0].clientY,
        };
      }
    },
    [getDistance, getCenter, onPinchZoom, onPan, clearLongPressTimer]
  );

  const handleTouchEnd = useCallback(
    (e: TouchEvent) => {
      clearLongPressTimer();

      const touchEndTime = Date.now();
      const touchDuration = touchEndTime - state.current.touchStartTime;

      // Handle double tap
      if (onDoubleTap && e.changedTouches.length === 1) {
        const timeSinceLastTap = touchEndTime - state.current.lastTouchEnd;
        if (timeSinceLastTap < 300 && touchDuration < 150) {
          e.preventDefault();
          onDoubleTap({
            x: e.changedTouches[0].clientX,
            y: e.changedTouches[0].clientY,
          });
        }
      }

      // Handle swipe
      if (onSwipe && state.current.touchStartPosition && touchDuration < 300) {
        const dx = e.changedTouches[0].clientX - state.current.touchStartPosition.x;
        const dy = e.changedTouches[0].clientY - state.current.touchStartPosition.y;

        if (Math.abs(dx) > swipeThreshold || Math.abs(dy) > swipeThreshold) {
          if (Math.abs(dx) > Math.abs(dy)) {
            onSwipe(dx > 0 ? 'right' : 'left');
          } else {
            onSwipe(dy > 0 ? 'down' : 'up');
          }
        }
      }

      state.current.lastTouchEnd = touchEndTime;
      state.current.initialDistance = 0;
      state.current.lastPanPosition = null;
      state.current.touchStartPosition = null;
    },
    [onDoubleTap, onSwipe, swipeThreshold, clearLongPressTimer]
  );

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    // Passive: false to allow preventDefault for pinch zoom
    element.addEventListener('touchstart', handleTouchStart, { passive: true });
    element.addEventListener('touchmove', handleTouchMove, { passive: false });
    element.addEventListener('touchend', handleTouchEnd, { passive: false });
    element.addEventListener('touchcancel', clearLongPressTimer);

    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
      element.removeEventListener('touchend', handleTouchEnd);
      element.removeEventListener('touchcancel', clearLongPressTimer);
      clearLongPressTimer();
    };
  }, [elementRef, handleTouchStart, handleTouchMove, handleTouchEnd, clearLongPressTimer]);
}
