import { useRef, useState, useCallback } from 'react';

interface VirtualScrollOptions {
  itemHeight: number | ((index: number) => number);
  containerHeight: number;
  buffer?: number;
  overscan?: number;
}

interface VirtualScrollResult<T> {
  virtualItems: Array<{
    index: number;
    start: number;
    size: number;
    item: T;
  }>;
  totalHeight: number;
  scrollToIndex: (index: number) => void;
  containerProps: {
    onScroll: (e: React.UIEvent<HTMLElement>) => void;
    style: React.CSSProperties;
  };
  wrapperProps: {
    style: React.CSSProperties;
  };
}

export function useVirtualScroll<T>(
  items: T[],
  options: VirtualScrollOptions
): VirtualScrollResult<T> {
  const {
    itemHeight,
    containerHeight,
    overscan = 3,
  } = options;

  const scrollRef = useRef<HTMLElement>(null);
  const [scrollTop, setScrollTop] = useState(0);

  const getItemHeight = useCallback(
    (index: number) => {
      return typeof itemHeight === 'function'
        ? itemHeight(index)
        : itemHeight;
    },
    [itemHeight]
  );

  const getItemOffset = useCallback(
    (index: number) => {
      let offset = 0;
      for (let i = 0; i < index; i++) {
        offset += getItemHeight(i);
      }
      return offset;
    },
    [getItemHeight]
  );

  const totalHeight = items.reduce(
    (sum, _, index) => sum + getItemHeight(index),
    0
  );

  const startIndex = Math.max(
    0,
    Math.floor(scrollTop / getItemHeight(0)) - overscan
  );

  const endIndex = Math.min(
    items.length - 1,
    Math.ceil((scrollTop + containerHeight) / getItemHeight(0)) + overscan
  );

  const virtualItems = [];
  for (let i = startIndex; i <= endIndex; i++) {
    virtualItems.push({
      index: i,
      start: getItemOffset(i),
      size: getItemHeight(i),
      item: items[i],
    });
  }

  const handleScroll = useCallback((e: React.UIEvent<HTMLElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  const scrollToIndex = useCallback((index: number) => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = getItemOffset(index);
    }
  }, [getItemOffset]);

  return {
    virtualItems,
    totalHeight,
    scrollToIndex,
    containerProps: {
      onScroll: handleScroll,
      style: {
        height: containerHeight,
        overflow: 'auto',
      },
    },
    wrapperProps: {
      style: {
        height: totalHeight,
        position: 'relative' as const,
      },
    },
  };
}
