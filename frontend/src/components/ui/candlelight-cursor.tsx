/**
 * CandlelightCursor — warm radiance that follows the mouse
 *
 * Simulates reading an ancient manuscript by oil lamp.
 * Desktop only (hover: hover). Respects prefers-reduced-motion.
 */

import { useEffect, useRef, useCallback } from 'react';

export function CandlelightCursor() {
  const elRef = useRef<HTMLDivElement>(null);
  const pos = useRef({ x: -1000, y: -1000 });
  const target = useRef({ x: -1000, y: -1000 });
  const raf = useRef(0);
  const started = useRef(false);

  const animate = useCallback(() => {
    pos.current.x += (target.current.x - pos.current.x) * 0.09;
    pos.current.y += (target.current.y - pos.current.y) * 0.09;

    if (elRef.current) {
      elRef.current.style.left = `${pos.current.x}px`;
      elRef.current.style.top = `${pos.current.y}px`;
    }

    raf.current = requestAnimationFrame(animate);
  }, []);

  useEffect(() => {
    if (!window.matchMedia('(hover: hover)').matches) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const el = elRef.current;
    if (!el) return;

    const onMove = (e: MouseEvent) => {
      target.current = { x: e.clientX, y: e.clientY };
      if (!started.current) {
        pos.current = { x: e.clientX, y: e.clientY };
        el.style.left = `${e.clientX}px`;
        el.style.top = `${e.clientY}px`;
        el.style.opacity = '1';
        started.current = true;
      }
    };
    const onLeave = () => { el.style.opacity = '0'; };
    const onEnter = () => { if (started.current) el.style.opacity = '1'; };

    window.addEventListener('mousemove', onMove, { passive: true });
    document.addEventListener('mouseleave', onLeave);
    document.addEventListener('mouseenter', onEnter);
    raf.current = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseleave', onLeave);
      document.removeEventListener('mouseenter', onEnter);
      cancelAnimationFrame(raf.current);
    };
  }, [animate]);

  return (
    <div
      ref={elRef}
      aria-hidden="true"
      className="animate-candle-flicker"
      style={{
        position: 'fixed',
        zIndex: 9998,
        pointerEvents: 'none',
        opacity: 0,
        transition: 'opacity 0.4s ease',
        width: '600px',
        height: '600px',
        marginLeft: '-300px',
        marginTop: '-300px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(255,200,120,0.18) 0%, rgba(240,180,100,0.10) 25%, rgba(220,160,80,0.04) 50%, transparent 70%)',
        filter: 'blur(2px)',
      }}
    />
  );
}
