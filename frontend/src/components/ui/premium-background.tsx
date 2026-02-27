/**
 * PremiumBackground — Ancient × Futuristic animated texture layers
 *
 * Layered ambient effects with motion: drifting orbs, sweeping light,
 * pulsing data grids, and breathing contours.
 */

import { useMemo } from 'react';
import { cn } from '@/lib/utils';

interface PremiumBackgroundProps {
  className?: string;
}

/** Safari renders filter:blur, 1px radial-gradients and SVG patterns with
 *  visible banding / anti-aliasing artifacts. Detect once at module level. */
const isSafari =
  typeof navigator !== 'undefined' &&
  /Safari/.test(navigator.userAgent) &&
  !/Chrome/.test(navigator.userAgent);

export function PremiumBackground({ className }: PremiumBackgroundProps) {
  return (
    <div
      className={cn(
        'fixed inset-0 pointer-events-none overflow-hidden',
        className
      )}
      style={{ zIndex: 0 }}
      aria-hidden="true"
    >
      {/* ═══ LAYER 1: Drifting warm orbs ═══ */}

      <div
        className="absolute rounded-full animate-orb-drift-1"
        style={{
          width: '60vw',
          height: '60vw',
          maxWidth: '900px',
          maxHeight: '900px',
          background: 'radial-gradient(circle at center, hsla(36, 50%, 72%, 0.25) 0%, hsla(36, 40%, 72%, 0.08) 40%, transparent 70%)',
          filter: 'blur(60px)',
          top: '-20%',
          right: '-10%',
        }}
      />

      <div
        className="absolute rounded-full animate-orb-drift-2"
        style={{
          width: '50vw',
          height: '50vw',
          maxWidth: '750px',
          maxHeight: '750px',
          background: 'radial-gradient(circle at center, hsla(25, 45%, 70%, 0.20) 0%, hsla(30, 35%, 70%, 0.06) 45%, transparent 70%)',
          filter: 'blur(50px)',
          bottom: '-15%',
          left: '-10%',
        }}
      />

      <div
        className="absolute rounded-full animate-orb-drift-3"
        style={{
          width: '40vw',
          height: '40vw',
          maxWidth: '600px',
          maxHeight: '600px',
          background: 'radial-gradient(circle at center, hsla(42, 55%, 75%, 0.18) 0%, hsla(40, 40%, 72%, 0.05) 50%, transparent 70%)',
          filter: 'blur(40px)',
          top: '25%',
          right: '5%',
        }}
      />

      <div
        className="absolute rounded-full animate-orb-drift-2"
        style={{
          width: '35vw',
          height: '35vw',
          maxWidth: '500px',
          maxHeight: '500px',
          background: 'radial-gradient(circle at center, hsla(30, 20%, 68%, 0.14) 0%, transparent 65%)',
          filter: 'blur(55px)',
          top: '10%',
          left: '5%',
          animationDelay: '-20s',
          animationDuration: '50s',
        }}
      />

      {/* ═══ LAYER 2: Sweeping light beam ═══ */}
      {/* Sunlight crossing a reading desk / data scanner sweep */}
      <div
        className="absolute inset-0 animate-light-sweep"
        style={{
          background: 'linear-gradient(105deg, transparent 0%, transparent 40%, hsla(38, 50%, 80%, 0.08) 45%, hsla(38, 50%, 85%, 0.12) 50%, hsla(38, 50%, 80%, 0.08) 55%, transparent 60%, transparent 100%)',
        }}
      />

      {/* ═══ LAYER 3: Animated dot matrix grid ═══ */}
      {/* Dots with a wandering spotlight reveal — data nodes activating */}
      {/* Safari: 1px radial-gradient dots render with visible anti-aliasing artifacts */}
      {!isSafari && (
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: 'radial-gradient(circle, rgba(160,140,110,0.14) 1px, transparent 1px)',
            backgroundSize: '32px 32px',
            maskImage: 'radial-gradient(ellipse 80% 70% at 50% 50%, black 20%, transparent 70%)',
            WebkitMaskImage: 'radial-gradient(ellipse 80% 70% at 50% 50%, black 20%, transparent 70%)',
          }}
        />
      )}
      {/* Spotlight moving over the dot grid — reveals dots more brightly as it passes */}
      {!isSafari && (
        <div
          className="absolute animate-grid-spotlight"
          style={{
            width: '50vw',
            height: '50vw',
            maxWidth: '700px',
            maxHeight: '700px',
            background: 'radial-gradient(circle at center, rgba(160,140,110,0.10) 0%, transparent 50%)',
            filter: 'blur(20px)',
          }}
        />
      )}

      {/* ═══ LAYER 4: Fine grid lines ═══ */}
      {/* Safari: sub-pixel grid lines render with different anti-aliasing */}
      {!isSafari && (
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `
              linear-gradient(90deg, rgba(160,140,110,0.04) 1px, transparent 1px),
              linear-gradient(0deg, rgba(160,140,110,0.03) 1px, transparent 1px)
            `,
            backgroundSize: '64px 64px',
            maskImage: 'radial-gradient(ellipse 90% 80% at 50% 50%, black 10%, transparent 65%)',
            WebkitMaskImage: 'radial-gradient(ellipse 90% 80% at 50% 50%, black 10%, transparent 65%)',
          }}
        />
      )}

      {/* ═══ LAYER 5: Drifting philosophical terms ═══ */}
      {/* Ancient Greek & Latin terms on free will, fate, causation — scholarly watermark */}
      {(() => {
        const terms = [
          'ἐλευθερία',    // freedom / liberty
          'εἱμαρμένη',    // fate / destiny
          'πρόνοια',      // providence
          'ἀνάγκη',       // necessity
          'αὐτεξούσιον',  // free will / self-determination
          'ἀρετή',        // virtue
          'λόγος',        // reason / logos
          'ψυχή',         // soul
          'τύχη',         // fortune / chance
          'αἰτία',        // cause
          'συγκατάθεσις', // assent (Stoic)
          'ἐφ᾽ ἡμῖν',     // up to us / in our power
          'fatum',        // fate (Latin)
          'voluntas',     // will (Latin)
          'libertas',     // freedom (Latin)
          'providentia',  // providence (Latin)
          'virtus',       // virtue (Latin)
          'necessitas',   // necessity (Latin)
        ];
        const positions = [
          { left: '6%', top: '10%', size: 15, rotation: -12, delay: 0 },
          { left: '24%', top: '6%', size: 13, rotation: 18, delay: -5 },
          { left: '48%', top: '4%', size: 14, rotation: -6, delay: -10 },
          { left: '72%', top: '12%', size: 12, rotation: 22, delay: -3 },
          { left: '88%', top: '22%', size: 14, rotation: -15, delay: -8 },
          { left: '10%', top: '30%', size: 16, rotation: 8, delay: -13 },
          { left: '38%', top: '26%', size: 13, rotation: -20, delay: -2 },
          { left: '65%', top: '35%', size: 12, rotation: 14, delay: -7 },
          { left: '85%', top: '45%', size: 15, rotation: -10, delay: -11 },
          { left: '4%', top: '52%', size: 13, rotation: 25, delay: -4 },
          { left: '30%', top: '58%', size: 14, rotation: -8, delay: -9 },
          { left: '55%', top: '50%', size: 12, rotation: 16, delay: -1 },
          { left: '78%', top: '62%', size: 14, rotation: -18, delay: -6 },
          { left: '15%', top: '72%', size: 13, rotation: 10, delay: -14 },
          { left: '42%', top: '78%', size: 15, rotation: -22, delay: -3 },
          { left: '68%', top: '80%', size: 12, rotation: 12, delay: -8 },
          { left: '90%', top: '75%', size: 13, rotation: -5, delay: -12 },
          { left: '25%', top: '90%', size: 14, rotation: 15, delay: -6 },
        ];
        return positions.map((pos, i) => (
          <div
            key={`term-${i}`}
            className="absolute animate-letter-drift select-none whitespace-nowrap"
            style={{
              left: pos.left,
              top: pos.top,
              fontSize: `${pos.size}px`,
              fontFamily: '"Palatino Linotype", "Book Antiqua", Palatino, Georgia, serif',
              fontStyle: 'italic',
              color: `rgba(160, 142, 112, ${0.14 + (i % 4) * 0.03})`,
              transform: `rotate(${pos.rotation}deg)`,
              animationDelay: `${pos.delay}s`,
              animationDuration: `${24 + (i % 5) * 5}s`,
            }}
          >
            {terms[i % terms.length]}
          </div>
        ));
      })()}

      {/* ═══ LAYER 6: Annotation crosses ═══ */}
      {/* Safari: SVG data-URL patterns render with sub-pixel artifacts */}
      {!isSafari && (
        <div
          className="absolute inset-0 animate-grid-fade"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='120' height='120' viewBox='0 0 120 120' xmlns='http://www.w3.org/2000/svg'%3E%3Cg stroke='rgba(160,140,110,0.08)' stroke-width='0.5'%3E%3Cline x1='57' y1='55' x2='63' y2='55'/%3E%3Cline x1='60' y1='52' x2='60' y2='58'/%3E%3C/g%3E%3C/svg%3E")`,
            backgroundSize: '120px 120px',
            maskImage: 'radial-gradient(ellipse 70% 60% at 50% 50%, black 30%, transparent 70%)',
            WebkitMaskImage: 'radial-gradient(ellipse 70% 60% at 50% 50%, black 30%, transparent 70%)',
          }}
        />
      )}

      {/* ═══ LAYER 7: Floating dust motes ═══ */}
      {/* Library dust / data particles — small bright dots that drift upward */}
      {Array.from({ length: 12 }).map((_, i) => (
        <div
          key={i}
          className="absolute rounded-full animate-dust-float"
          style={{
            width: `${2 + (i % 3)}px`,
            height: `${2 + (i % 3)}px`,
            background: `rgba(${180 + (i * 5)}, ${160 + (i * 3)}, ${120 + (i * 4)}, ${0.15 + (i % 4) * 0.05})`,
            left: `${8 + (i * 7.5)}%`,
            bottom: `${-5 - (i * 3)}%`,
            animationDuration: `${18 + (i * 4)}s`,
            animationDelay: `${-(i * 2.5)}s`,
          }}
        />
      ))}

      {/* ═══ LAYER 8: Breathing vignette ═══ */}
      <div
        className="absolute inset-0 animate-vignette-breathe"
        style={{
          background: 'radial-gradient(ellipse 70% 55% at 50% 45%, transparent 25%, rgba(180,165,145,0.07) 100%)',
        }}
      />
    </div>
  );
}
