import type { Variants, Transition } from 'framer-motion';

/**
 * Default transition settings
 */
export const defaultTransition: Transition = {
  type: 'spring',
  stiffness: 100,
  damping: 15,
};

export const smoothTransition: Transition = {
  type: 'spring',
  stiffness: 300,
  damping: 30,
};

export const snappyTransition: Transition = {
  type: 'spring',
  stiffness: 400,
  damping: 25,
};

/**
 * Fade animations
 */
export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.3 }
  },
  exit: {
    opacity: 0,
    transition: { duration: 0.2 }
  },
};

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: defaultTransition
  },
  exit: {
    opacity: 0,
    y: -20,
    transition: { duration: 0.2 }
  },
};

export const fadeInDown: Variants = {
  hidden: { opacity: 0, y: -20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: defaultTransition
  },
  exit: {
    opacity: 0,
    y: 20,
    transition: { duration: 0.2 }
  },
};

export const fadeInLeft: Variants = {
  hidden: { opacity: 0, x: -20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: defaultTransition
  },
  exit: {
    opacity: 0,
    x: 20,
    transition: { duration: 0.2 }
  },
};

export const fadeInRight: Variants = {
  hidden: { opacity: 0, x: 20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: defaultTransition
  },
  exit: {
    opacity: 0,
    x: -20,
    transition: { duration: 0.2 }
  },
};

/**
 * Slide animations
 */
export const slideInLeft: Variants = {
  hidden: { x: '-100%', opacity: 0 },
  visible: {
    x: 0,
    opacity: 1,
    transition: smoothTransition
  },
  exit: {
    x: '-100%',
    opacity: 0,
    transition: { duration: 0.3 }
  },
};

export const slideInRight: Variants = {
  hidden: { x: '100%', opacity: 0 },
  visible: {
    x: 0,
    opacity: 1,
    transition: smoothTransition
  },
  exit: {
    x: '100%',
    opacity: 0,
    transition: { duration: 0.3 }
  },
};

export const slideInUp: Variants = {
  hidden: { y: '100%', opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: smoothTransition
  },
  exit: {
    y: '100%',
    opacity: 0,
    transition: { duration: 0.3 }
  },
};

export const slideInDown: Variants = {
  hidden: { y: '-100%', opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: smoothTransition
  },
  exit: {
    y: '-100%',
    opacity: 0,
    transition: { duration: 0.3 }
  },
};

/**
 * Scale animations
 */
export const scaleIn: Variants = {
  hidden: { scale: 0.8, opacity: 0 },
  visible: {
    scale: 1,
    opacity: 1,
    transition: defaultTransition
  },
  exit: {
    scale: 0.8,
    opacity: 0,
    transition: { duration: 0.2 }
  },
};

export const scaleInCenter: Variants = {
  hidden: { scale: 0, opacity: 0 },
  visible: {
    scale: 1,
    opacity: 1,
    transition: snappyTransition
  },
  exit: {
    scale: 0,
    opacity: 0,
    transition: { duration: 0.2 }
  },
};

export const popIn: Variants = {
  hidden: { scale: 0, opacity: 0 },
  visible: {
    scale: 1,
    opacity: 1,
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 20,
    },
  },
  exit: {
    scale: 0,
    opacity: 0,
    transition: { duration: 0.15 }
  },
};

export const bounceIn: Variants = {
  hidden: { scale: 0, opacity: 0 },
  visible: {
    scale: [0, 1.1, 0.95, 1],
    opacity: 1,
    transition: {
      duration: 0.6,
      times: [0, 0.5, 0.75, 1],
      ease: 'easeInOut',
    },
  },
};

/**
 * Rotate animations
 */
export const rotateIn: Variants = {
  hidden: { rotate: -180, opacity: 0 },
  visible: {
    rotate: 0,
    opacity: 1,
    transition: smoothTransition
  },
  exit: {
    rotate: 180,
    opacity: 0,
    transition: { duration: 0.3 }
  },
};

export const flipIn: Variants = {
  hidden: { rotateY: -90, opacity: 0 },
  visible: {
    rotateY: 0,
    opacity: 1,
    transition: smoothTransition
  },
  exit: {
    rotateY: 90,
    opacity: 0,
    transition: { duration: 0.3 }
  },
};

/**
 * Stagger animations for lists
 */
export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
  exit: {
    opacity: 0,
    transition: {
      staggerChildren: 0.05,
      staggerDirection: -1,
    },
  },
};

export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: defaultTransition,
  },
  exit: {
    opacity: 0,
    y: -20,
    transition: { duration: 0.2 },
  },
};

/**
 * Create custom stagger container with configurable delay
 */
export const createStaggerContainer = (
  staggerDelay: number = 0.1,
  delayChildren: number = 0
): Variants => ({
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: staggerDelay,
      delayChildren: delayChildren,
    },
  },
});

/**
 * Create custom fade animation with configurable distance
 */
export const createFadeInUp = (distance: number = 20): Variants => ({
  hidden: { opacity: 0, y: distance },
  visible: {
    opacity: 1,
    y: 0,
    transition: defaultTransition
  },
  exit: {
    opacity: 0,
    y: -distance,
    transition: { duration: 0.2 }
  },
});

/**
 * Page transition animations
 */
export const pageTransition: Variants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: 'easeInOut',
    },
  },
  exit: {
    opacity: 0,
    y: -30,
    transition: {
      duration: 0.3,
      ease: 'easeInOut',
    },
  },
};

/**
 * Modal/overlay animations
 */
export const modalOverlay: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.3 }
  },
  exit: {
    opacity: 0,
    transition: { duration: 0.2 }
  },
};

export const modalContent: Variants = {
  hidden: { opacity: 0, scale: 0.95, y: 10 },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: smoothTransition,
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    y: 10,
    transition: { duration: 0.2 },
  },
};

/**
 * Drawer animations
 */
export const drawerLeft: Variants = {
  hidden: { x: '-100%' },
  visible: {
    x: 0,
    transition: smoothTransition,
  },
  exit: {
    x: '-100%',
    transition: { duration: 0.3 },
  },
};

export const drawerRight: Variants = {
  hidden: { x: '100%' },
  visible: {
    x: 0,
    transition: smoothTransition,
  },
  exit: {
    x: '100%',
    transition: { duration: 0.3 },
  },
};

export const drawerBottom: Variants = {
  hidden: { y: '100%' },
  visible: {
    x: 0,
    transition: smoothTransition,
  },
  exit: {
    y: '100%',
    transition: { duration: 0.3 },
  },
};

/**
 * Hover animations
 */
export const hoverScale = {
  whileHover: { scale: 1.05 },
  whileTap: { scale: 0.95 },
  transition: defaultTransition,
};

export const hoverBrighten = {
  whileHover: { filter: 'brightness(1.1)' },
  whileTap: { filter: 'brightness(0.9)' },
};

export const hoverLift = {
  whileHover: { y: -5, boxShadow: '0 10px 30px rgba(0,0,0,0.2)' },
  whileTap: { y: 0 },
  transition: defaultTransition,
};

/**
 * Loading animation
 */
export const pulse: Variants = {
  hidden: { opacity: 0.5 },
  visible: {
    opacity: 1,
    transition: {
      duration: 0.8,
      repeat: Infinity,
      repeatType: 'reverse',
    },
  },
};

/**
 * Typing animation for chat/messages
 */
export const typingDots: Variants = {
  hidden: { opacity: 0 },
  visible: (i: number) => ({
    opacity: 1,
    transition: {
      delay: i * 0.1,
      repeat: Infinity,
      repeatType: 'reverse',
      duration: 0.6,
    },
  }),
};

/**
 * Accordion/collapse animation
 */
export const collapse: Variants = {
  hidden: {
    height: 0,
    opacity: 0,
    overflow: 'hidden'
  },
  visible: {
    height: 'auto',
    opacity: 1,
    overflow: 'visible',
    transition: {
      height: smoothTransition,
      opacity: { duration: 0.2, delay: 0.1 },
    },
  },
  exit: {
    height: 0,
    opacity: 0,
    overflow: 'hidden',
    transition: {
      height: smoothTransition,
      opacity: { duration: 0.2 },
    },
  },
};

/**
 * Progress bar animation
 */
export const progressBar: Variants = {
  hidden: { width: 0 },
  visible: (progress: number) => ({
    width: `${progress}%`,
    transition: {
      duration: 0.5,
      ease: 'easeInOut',
    },
  }),
};

/**
 * Notification animations
 */
export const notificationSlide: Variants = {
  hidden: { x: '100%', opacity: 0 },
  visible: {
    x: 0,
    opacity: 1,
    transition: snappyTransition,
  },
  exit: {
    x: '100%',
    opacity: 0,
    transition: { duration: 0.2 },
  },
};

/**
 * Tab indicator animation
 */
export const tabIndicator: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.3 },
  },
};

/**
 * Skeleton loading animation
 */
export const shimmer = {
  animate: {
    backgroundPosition: ['200% 0', '-200% 0'],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: 'linear',
    },
  },
};

/**
 * Create custom spring animation
 */
export const createSpring = (
  stiffness: number = 300,
  damping: number = 30
): Transition => ({
  type: 'spring',
  stiffness,
  damping,
});

/**
 * Create custom tween animation
 */
export const createTween = (
  duration: number = 0.3,
  ease: [number, number, number, number] | 'linear' | 'easeIn' | 'easeOut' | 'easeInOut' | 'circIn' | 'circOut' | 'circInOut' | 'backIn' | 'backOut' | 'backInOut' | 'anticipate' = 'easeInOut'
): Transition => ({
  type: 'tween',
  duration,
  ease,
});
