import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence, useInView } from 'framer-motion';
import type { Variants } from 'framer-motion';
import { cn } from '../../utils/cn';

interface AnimatedListProps<T> {
  /** Array of items to render */
  items: T[];
  /** Render function for each item */
  renderItem: (item: T, index: number) => React.ReactNode;
  /** Unique key extractor for each item */
  keyExtractor?: (item: T, index: number) => string | number;
  /** Animation variant */
  variant?: 'fade' | 'slide' | 'scale' | 'flip' | 'cascade' | 'custom';
  /** Custom animation variants */
  customVariants?: {
    container?: Variants;
    item?: Variants;
  };
  /** Stagger delay between items (in seconds) */
  staggerDelay?: number;
  /** Initial animation delay */
  initialDelay?: number;
  /** Whether to animate on scroll into view */
  animateOnScroll?: boolean;
  /** Additional CSS classes for container */
  className?: string;
  /** Layout type */
  layout?: 'list' | 'grid' | 'masonry';
  /** Grid columns (for grid layout) */
  columns?: number | { sm?: number; md?: number; lg?: number; xl?: number };
  /** Gap between items */
  gap?: number;
  /** Whether to show items in reverse order */
  reverse?: boolean;
  /** Empty state component */
  emptyState?: React.ReactNode;
  /** Loading state */
  loading?: boolean;
  /** Loading component */
  loadingComponent?: React.ReactNode;
  /** Whether to exit removed items with animation */
  exitAnimation?: boolean;
  /** Sort function */
  sortFn?: (a: T, b: T) => number;
  /** Filter function */
  filterFn?: (item: T) => boolean;
}

/**
 * Pre-defined animation variants
 */
const animationVariants = {
  fade: {
    container: {
      hidden: { opacity: 0 },
      visible: {
        opacity: 1,
        transition: {
          staggerChildren: 0.1,
        },
      },
    },
    item: {
      hidden: { opacity: 0 },
      visible: { opacity: 1 },
      exit: { opacity: 0 },
    },
  },
  slide: {
    container: {
      hidden: { opacity: 0 },
      visible: {
        opacity: 1,
        transition: {
          staggerChildren: 0.1,
        },
      },
    },
    item: {
      hidden: { opacity: 0, x: -20 },
      visible: { opacity: 1, x: 0 },
      exit: { opacity: 0, x: 20 },
    },
  },
  scale: {
    container: {
      hidden: { opacity: 0 },
      visible: {
        opacity: 1,
        transition: {
          staggerChildren: 0.1,
        },
      },
    },
    item: {
      hidden: { opacity: 0, scale: 0.8 },
      visible: { opacity: 1, scale: 1 },
      exit: { opacity: 0, scale: 0.8 },
    },
  },
  flip: {
    container: {
      hidden: { opacity: 0 },
      visible: {
        opacity: 1,
        transition: {
          staggerChildren: 0.1,
        },
      },
    },
    item: {
      hidden: { opacity: 0, rotateX: -90 },
      visible: { opacity: 1, rotateX: 0 },
      exit: { opacity: 0, rotateX: 90 },
    },
  },
  cascade: {
    container: {
      hidden: { opacity: 0 },
      visible: {
        opacity: 1,
        transition: {
          staggerChildren: 0.05,
          delayChildren: 0.2,
        },
      },
    },
    item: {
      hidden: { opacity: 0, y: 20, scale: 0.95 },
      visible: {
        opacity: 1,
        y: 0,
        scale: 1,
        transition: {
          type: 'spring',
          stiffness: 100,
          damping: 15,
        },
      },
      exit: {
        opacity: 0,
        y: -20,
        scale: 0.95,
        transition: { duration: 0.2 },
      },
    },
  },
};

/**
 * AnimatedList component for rendering animated collections
 *
 * @example
 * <AnimatedList
 *   items={data}
 *   renderItem={(item) => <Card>{item.name}</Card>}
 *   variant="cascade"
 *   layout="grid"
 *   columns={{ sm: 1, md: 2, lg: 3 }}
 * />
 */
export function AnimatedList<T = any>({
  items,
  renderItem,
  keyExtractor,
  variant = 'fade',
  customVariants,
  staggerDelay = 0.1,
  initialDelay = 0,
  animateOnScroll = false,
  className,
  layout = 'list',
  columns = 1,
  gap = 4,
  reverse = false,
  emptyState,
  loading = false,
  loadingComponent,
  exitAnimation = true,
  sortFn,
  filterFn,
}: AnimatedListProps<T>) {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: '-100px' });
  const [processedItems, setProcessedItems] = useState<T[]>([]);

  // Process items (filter and sort)
  useEffect(() => {
    let result = [...items];

    if (filterFn) {
      result = result.filter(filterFn);
    }

    if (sortFn) {
      result.sort(sortFn);
    }

    if (reverse) {
      result.reverse();
    }

    setProcessedItems(result);
  }, [items, filterFn, sortFn, reverse]);

  // Get animation variants
  const variants = customVariants || (variant === 'custom' ? animationVariants.fade : animationVariants[variant]) || animationVariants.fade;

  // Update stagger delay in container variants
  const containerVariants: Variants = {
    ...variants.container,
    visible: {
      ...(typeof variants.container?.visible === 'object' && 'transition' in variants.container.visible
        ? variants.container.visible
        : {}),
      transition: {
        ...(typeof variants.container?.visible === 'object' && 'transition' in variants.container.visible
          ? (variants.container.visible as { transition?: Record<string, unknown> }).transition
          : {}),
        staggerChildren: staggerDelay,
        delayChildren: initialDelay,
      },
    },
  };

  // Generate grid classes
  const getGridClasses = () => {
    if (layout !== 'grid') return '';

    if (typeof columns === 'number') {
      return `grid-cols-${columns}`;
    }

    const classes: string[] = [];
    if (columns.sm) classes.push(`sm:grid-cols-${columns.sm}`);
    if (columns.md) classes.push(`md:grid-cols-${columns.md}`);
    if (columns.lg) classes.push(`lg:grid-cols-${columns.lg}`);
    if (columns.xl) classes.push(`xl:grid-cols-${columns.xl}`);

    return classes.join(' ');
  };

  // Layout classes
  const layoutClasses = {
    list: 'flex flex-col',
    grid: `grid ${getGridClasses()}`,
    masonry: 'columns-1 sm:columns-2 lg:columns-3 xl:columns-4',
  };

  // Loading state
  if (loading) {
    return (
      <div className={cn('flex items-center justify-center py-12', className)}>
        {loadingComponent || (
          <div className="flex flex-col items-center gap-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
            <span className="text-sm text-gray-500">Loading items...</span>
          </div>
        )}
      </div>
    );
  }

  // Empty state
  if (processedItems.length === 0 && emptyState) {
    return (
      <div className={cn('flex items-center justify-center py-12', className)}>
        {emptyState}
      </div>
    );
  }

  const shouldAnimate = !animateOnScroll || isInView;

  return (
    <motion.div
      ref={containerRef}
      variants={containerVariants}
      initial="hidden"
      animate={shouldAnimate ? 'visible' : 'hidden'}
      className={cn(
        layoutClasses[layout],
        `gap-${gap}`,
        className
      )}
    >
      <AnimatePresence mode={exitAnimation ? 'popLayout' : 'sync'}>
        {processedItems.map((item, index) => {
          const key = keyExtractor ? keyExtractor(item, index) : index;

          return (
            <motion.div
              key={key}
              variants={variants.item}
              layout={layout === 'masonry'}
              className={layout === 'masonry' ? 'break-inside-avoid mb-4' : ''}
            >
              {renderItem(item, index)}
            </motion.div>
          );
        })}
      </AnimatePresence>
    </motion.div>
  );
}

/**
 * VirtualizedAnimatedList for large datasets with virtualization
 */
interface VirtualizedAnimatedListProps<T> extends AnimatedListProps<T> {
  /** Item height (required for virtualization) */
  itemHeight: number | ((item: T) => number);
  /** Container height */
  height?: number | string;
  /** Overscan count (items to render outside visible area) */
  overscan?: number;
}

export function VirtualizedAnimatedList<T = any>({
  items,
  renderItem,
  itemHeight,
  height = 400,
  overscan = 3,
  className,
  ...rest
}: VirtualizedAnimatedListProps<T>) {
  const [scrollTop, setScrollTop] = useState(0);
  const [containerHeight, setContainerHeight] = useState(
    typeof height === 'number' ? height : 400
  );
  const containerRef = useRef<HTMLDivElement>(null);

  // Calculate visible range
  const getItemHeight = (item: T, _index: number) => {
    return typeof itemHeight === 'function' ? itemHeight(item) : itemHeight;
  };

  const getVisibleRange = () => {
    let accumulatedHeight = 0;
    let startIndex = 0;
    let endIndex = items.length - 1;

    // Find start index
    for (let i = 0; i < items.length; i++) {
      const h = getItemHeight(items[i], i);
      if (accumulatedHeight + h > scrollTop) {
        startIndex = Math.max(0, i - overscan);
        break;
      }
      accumulatedHeight += h;
    }

    // Find end index
    accumulatedHeight = 0;
    for (let i = startIndex; i < items.length; i++) {
      if (accumulatedHeight > containerHeight) {
        endIndex = Math.min(items.length - 1, i + overscan);
        break;
      }
      accumulatedHeight += getItemHeight(items[i], i);
    }

    return { startIndex, endIndex };
  };

  const { startIndex, endIndex } = getVisibleRange();
  const visibleItems = items.slice(startIndex, endIndex + 1);

  // Calculate total height and offset
  const totalHeight = items.reduce(
    (acc, item, i) => acc + getItemHeight(item, i),
    0
  );

  const offsetY = items
    .slice(0, startIndex)
    .reduce((acc, item, i) => acc + getItemHeight(item, i), 0);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  };

  useEffect(() => {
    if (containerRef.current) {
      setContainerHeight(containerRef.current.clientHeight);
    }
  }, [height]);

  return (
    <div
      ref={containerRef}
      className={cn('overflow-y-auto', className)}
      style={{ height }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div
          style={{
            transform: `translateY(${offsetY}px)`,
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
          }}
        >
          <AnimatedList
            {...rest}
            items={visibleItems}
            renderItem={renderItem}
            animateOnScroll={false}
          />
        </div>
      </div>
    </div>
  );
}

/**
 * AnimatedGrid - Specialized grid layout with animations
 */
interface AnimatedGridProps<T> extends Omit<AnimatedListProps<T>, 'layout'> {
  /** Number of columns */
  columns?: number | { sm?: number; md?: number; lg?: number; xl?: number };
  /** Aspect ratio for grid items */
  aspectRatio?: string;
}

export function AnimatedGrid<T = any>({
  columns = { sm: 1, md: 2, lg: 3, xl: 4 },
  aspectRatio,
  className,
  ...rest
}: AnimatedGridProps<T>) {
  return (
    <AnimatedList
      {...rest}
      layout="grid"
      columns={columns}
      className={cn(
        aspectRatio && `[&>*]:aspect-[${aspectRatio}]`,
        className
      )}
    />
  );
}

/**
 * AnimatedMasonry - Specialized masonry layout with animations
 */
interface AnimatedMasonryProps<T> extends Omit<AnimatedListProps<T>, 'layout'> {
  /** Number of columns */
  columns?: number;
}

export function AnimatedMasonry<T = any>({
  columns = 3,
  className,
  ...rest
}: AnimatedMasonryProps<T>) {
  return (
    <AnimatedList
      {...rest}
      layout="masonry"
      className={cn(`columns-${columns}`, className)}
    />
  );
}

/**
 * InfiniteAnimatedList - List with infinite scroll support
 */
interface InfiniteAnimatedListProps<T> extends AnimatedListProps<T> {
  /** Function to load more items */
  onLoadMore: () => Promise<void>;
  /** Whether more items are available */
  hasMore: boolean;
  /** Loading more indicator */
  loadingMore?: boolean;
  /** Threshold for triggering load (in pixels) */
  threshold?: number;
}

export function InfiniteAnimatedList<T = any>({
  onLoadMore,
  hasMore,
  loadingMore = false,
  threshold = 200,
  ...rest
}: InfiniteAnimatedListProps<T>) {
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!hasMore || loadingMore) return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          onLoadMore();
        }
      },
      { rootMargin: `${threshold}px` }
    );

    if (loadMoreRef.current) {
      observerRef.current.observe(loadMoreRef.current);
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [hasMore, loadingMore, onLoadMore, threshold]);

  return (
    <>
      <AnimatedList {...rest} />
      {hasMore && (
        <div ref={loadMoreRef} className="py-4 text-center">
          {loadingMore && (
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto" />
          )}
        </div>
      )}
    </>
  );
}
