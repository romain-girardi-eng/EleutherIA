"use client";

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence, type PanInfo } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Pause, Play } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface FeatureCardData {
  id: string;
  to: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  gradient: string;
  accentColor: string;
  stats?: { label: string; value: string };
}

interface FeatureCarouselProps {
  cards: FeatureCardData[];
  autoPlayInterval?: number;
  className?: string;
}

export function FeatureCarousel({
  cards,
  autoPlayInterval = 4000,
  className,
}: FeatureCarouselProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const totalCards = cards.length;

  // Auto-play logic
  useEffect(() => {
    if (!isAutoPlaying || isPaused) return;

    const timer = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % totalCards);
    }, autoPlayInterval);

    return () => clearInterval(timer);
  }, [isAutoPlaying, isPaused, totalCards, autoPlayInterval]);

  const goToNext = useCallback(() => {
    setActiveIndex((prev) => (prev + 1) % totalCards);
  }, [totalCards]);

  const goToPrev = useCallback(() => {
    setActiveIndex((prev) => (prev - 1 + totalCards) % totalCards);
  }, [totalCards]);

  const goToIndex = useCallback((index: number) => {
    setActiveIndex(index);
  }, []);

  // Handle drag end
  const handleDragEnd = (_: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    const threshold = 50;
    if (info.offset.x > threshold) {
      goToPrev();
    } else if (info.offset.x < -threshold) {
      goToNext();
    }
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') goToPrev();
      if (e.key === 'ArrowRight') goToNext();
    };

    const container = containerRef.current;
    container?.addEventListener('keydown', handleKeyDown);
    return () => container?.removeEventListener('keydown', handleKeyDown);
  }, [goToNext, goToPrev]);

  // Get visible cards (previous, current, next for 3D effect)
  const getCardPosition = (index: number) => {
    const diff = index - activeIndex;
    if (diff === 0) return 'center';
    if (diff === 1 || diff === -(totalCards - 1)) return 'right';
    if (diff === -1 || diff === totalCards - 1) return 'left';
    if (diff === 2 || diff === -(totalCards - 2)) return 'far-right';
    if (diff === -2 || diff === totalCards - 2) return 'far-left';
    return 'hidden';
  };

  const cardVariants = {
    center: {
      x: 0,
      scale: 1,
      zIndex: 30,
      rotateY: 0,
      opacity: 1,
      filter: 'blur(0px)',
    },
    left: {
      x: -280,
      scale: 0.8,
      zIndex: 20,
      rotateY: 25,
      opacity: 0.8,
      filter: 'blur(1px)',
    },
    right: {
      x: 280,
      scale: 0.8,
      zIndex: 20,
      rotateY: -25,
      opacity: 0.8,
      filter: 'blur(1px)',
    },
    'far-left': {
      x: -500,
      scale: 0.6,
      zIndex: 10,
      rotateY: 40,
      opacity: 0.4,
      filter: 'blur(2px)',
    },
    'far-right': {
      x: 500,
      scale: 0.6,
      zIndex: 10,
      rotateY: -40,
      opacity: 0.4,
      filter: 'blur(2px)',
    },
    hidden: {
      x: 0,
      scale: 0.5,
      zIndex: 0,
      rotateY: 0,
      opacity: 0,
      filter: 'blur(4px)',
    },
  };

  return (
    <div
      ref={containerRef}
      className={cn('relative w-full py-12 overflow-visible', className)}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      tabIndex={0}
      role="region"
      aria-label="Feature carousel"
    >
      {/* Background Glow Effect */}
      <div className="absolute inset-0 pointer-events-none" style={{ overflow: 'visible' }}>
        <motion.div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full opacity-30"
          style={{
            background: `radial-gradient(ellipse, ${cards[activeIndex]?.accentColor || 'rgba(99, 102, 241, 0.3)'} 0%, transparent 70%)`,
          }}
          animate={{
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      </div>

      {/* Cards Container with 3D Perspective */}
      <div
        className="relative h-[420px] md:h-[480px] flex items-center justify-center overflow-visible"
        style={{ perspective: '1200px', perspectiveOrigin: '50% 50%' }}
      >
        <AnimatePresence mode="sync">
          {cards.map((card, index) => {
            const position = getCardPosition(index);
            if (position === 'hidden') return null;

            return (
              <motion.div
                key={card.id}
                className="absolute w-[320px] md:w-[400px] cursor-grab active:cursor-grabbing"
                style={{
                  transformStyle: 'preserve-3d',
                }}
                variants={cardVariants}
                initial={position}
                animate={position}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{
                  type: 'spring',
                  stiffness: 300,
                  damping: 30,
                }}
                drag={position === 'center' ? 'x' : false}
                dragConstraints={{ left: 0, right: 0 }}
                dragElastic={0.1}
                onDragEnd={handleDragEnd}
                onClick={() => position !== 'center' && goToIndex(index)}
              >
                <FeatureCard
                  card={card}
                  isActive={position === 'center'}
                />
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Navigation Controls */}
      <div className="flex items-center justify-center gap-6 mt-8">
        {/* Previous Button */}
        <motion.button
          onClick={goToPrev}
          className="p-3 rounded-full bg-white/80 backdrop-blur-sm border border-white/20 shadow-lg hover:bg-white hover:shadow-xl transition-all"
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          aria-label="Previous card"
        >
          <ChevronLeft className="w-5 h-5 text-gray-700" />
        </motion.button>

        {/* Dot Indicators */}
        <div className="flex items-center gap-2">
          {cards.map((_, index) => (
            <motion.button
              key={index}
              onClick={() => goToIndex(index)}
              className={cn(
                'relative h-2 rounded-full transition-all duration-300',
                index === activeIndex ? 'w-8 bg-primary-600' : 'w-2 bg-gray-300 hover:bg-gray-400'
              )}
              whileHover={{ scale: 1.2 }}
              aria-label={`Go to card ${index + 1}`}
              aria-current={index === activeIndex ? 'true' : 'false'}
            >
              {index === activeIndex && isAutoPlaying && (
                <motion.div
                  className="absolute inset-0 bg-primary-400 rounded-full origin-left"
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: isPaused ? 0 : 1 }}
                  transition={{
                    duration: autoPlayInterval / 1000,
                    ease: 'linear',
                  }}
                  key={activeIndex}
                />
              )}
            </motion.button>
          ))}
        </div>

        {/* Next Button */}
        <motion.button
          onClick={goToNext}
          className="p-3 rounded-full bg-white/80 backdrop-blur-sm border border-white/20 shadow-lg hover:bg-white hover:shadow-xl transition-all"
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          aria-label="Next card"
        >
          <ChevronRight className="w-5 h-5 text-gray-700" />
        </motion.button>

        {/* Play/Pause Button */}
        <motion.button
          onClick={() => setIsAutoPlaying(!isAutoPlaying)}
          className="p-3 rounded-full bg-white/80 backdrop-blur-sm border border-white/20 shadow-lg hover:bg-white hover:shadow-xl transition-all ml-4"
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          aria-label={isAutoPlaying ? 'Pause autoplay' : 'Resume autoplay'}
        >
          {isAutoPlaying ? (
            <Pause className="w-4 h-4 text-gray-700" />
          ) : (
            <Play className="w-4 h-4 text-gray-700" />
          )}
        </motion.button>
      </div>

      {/* Card Counter */}
      <div className="text-center mt-4 text-sm text-gray-500">
        <span className="font-semibold text-primary-600">{activeIndex + 1}</span>
        <span> / {totalCards}</span>
      </div>
    </div>
  );
}

// Individual Feature Card Component
function FeatureCard({
  card,
  isActive,
}: {
  card: FeatureCardData;
  isActive: boolean;
}) {
  return (
    <Link
      to={card.to}
      className="block"
      onClick={(e) => !isActive && e.preventDefault()}
      tabIndex={isActive ? 0 : -1}
    >
      <motion.div
        className={cn(
          'relative h-[380px] md:h-[420px] rounded-3xl overflow-hidden',
          'bg-white/70 backdrop-blur-xl border border-white/30',
          'shadow-2xl transition-shadow duration-500',
          isActive && 'hover:shadow-3xl'
        )}
        whileHover={isActive ? { y: -8 } : {}}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      >
        {/* Animated Gradient Background */}
        <motion.div
          className={cn(
            'absolute inset-0 opacity-60',
            `bg-gradient-to-br ${card.gradient}`
          )}
          animate={isActive ? {
            backgroundPosition: ['0% 0%', '100% 100%', '0% 0%'],
          } : {}}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: 'linear',
          }}
          style={{ backgroundSize: '200% 200%' }}
        />

        {/* Shimmer Effect */}
        {isActive && (
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
            initial={{ x: '-100%' }}
            animate={{ x: '100%' }}
            transition={{
              duration: 2,
              repeat: Infinity,
              repeatDelay: 3,
              ease: 'easeInOut',
            }}
          />
        )}

        {/* Content */}
        <div className="relative h-full p-8 flex flex-col">
          {/* Icon with Glow */}
          <motion.div
            className={cn(
              'w-20 h-20 rounded-2xl flex items-center justify-center mb-6',
              'bg-white/50 backdrop-blur-sm shadow-lg',
              'border border-white/40'
            )}
            animate={isActive ? {
              boxShadow: [
                '0 0 20px rgba(99, 102, 241, 0.2)',
                '0 0 40px rgba(99, 102, 241, 0.4)',
                '0 0 20px rgba(99, 102, 241, 0.2)',
              ],
            } : {}}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <div className="text-primary-600 scale-125">
              {card.icon}
            </div>
          </motion.div>

          {/* Title */}
          <h3 className="text-2xl md:text-3xl font-bold text-gray-900 mb-3">
            {card.title}
          </h3>

          {/* Description */}
          <p className="text-gray-600 leading-relaxed flex-grow text-base md:text-lg">
            {card.description}
          </p>

          {/* Stats Badge */}
          {card.stats && (
            <motion.div
              className="mt-6 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/60 backdrop-blur-sm border border-white/40 w-fit"
              initial={{ opacity: 0, y: 10 }}
              animate={isActive ? { opacity: 1, y: 0 } : { opacity: 0.5, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <span className="text-2xl font-bold text-primary-600">
                {card.stats.value}
              </span>
              <span className="text-sm text-gray-600">
                {card.stats.label}
              </span>
            </motion.div>
          )}

          {/* Explore CTA */}
          <motion.div
            className={cn(
              'mt-6 flex items-center gap-2 text-primary-600 font-semibold',
              'transition-all duration-300'
            )}
            initial={{ opacity: 0, x: -10 }}
            animate={isActive ? { opacity: 1, x: 0 } : { opacity: 0 }}
            transition={{ delay: 0.3 }}
          >
            <span>Explore</span>
            <motion.span
              animate={isActive ? { x: [0, 5, 0] } : {}}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              <ChevronRight className="w-5 h-5" />
            </motion.span>
          </motion.div>
        </div>

        {/* Corner Decoration */}
        <div className="absolute top-0 right-0 w-32 h-32 overflow-hidden">
          <div
            className={cn(
              'absolute top-0 right-0 w-48 h-48 -translate-y-1/2 translate-x-1/2 rounded-full opacity-20',
              `bg-gradient-to-br ${card.gradient}`
            )}
          />
        </div>
      </motion.div>
    </Link>
  );
}

export default FeatureCarousel;
