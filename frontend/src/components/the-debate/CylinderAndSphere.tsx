/**
 * CylinderAndSphere — one simile, two conclusions, neither settled.
 *
 * Chrysippus answers the charge that fate makes assent empty with a cylinder:
 * the push starts it, but it rolls by its own shape, and the shape is its own.
 * Alexander answers with a sphere on a slope: if a thing's nature settles what
 * it does, then "up to us" has been explained away rather than explained.
 *
 * This is the only animated argument on the page, and it is animated because
 * the argument is about motion under a push. Both bodies take the SAME push.
 * The cylinder decelerates and stops inside its frame. The sphere accelerates
 * and leaves. A reader who watches once has the disagreement before reading
 * the captions, which is the test any motion on this page has to pass.
 *
 * Physically honest drawing: a rolling body's silhouette does not change, only
 * its surface marks turn. So the outline translates and the cross inside it
 * rotates, at the rate the travel demands. No slipping.
 *
 * Reduced motion is not a degraded version. It is a strobe photograph: start
 * ghosted, end solid, travel measured by a rule. Arguably the clearer figure.
 */

import { useEffect, useRef, useState } from 'react';
import { motion, useInView, useReducedMotion } from 'framer-motion';

import { cn } from '../../utils/cn';
import { TONE } from './tone';

export interface CylinderAndSphereProps {
  heading?: string;
  /** Stated as a standing disagreement. Never as a verdict. */
  standoff?: string;
  cylinder?: BodyCopy;
  sphere?: BodyCopy;
  className?: string;
}

export interface BodyCopy {
  title: string;
  attribution: string;
  claim: string;
  /** A single attested word, set in the source language. Verify before use. */
  word?: string;
  wordLang?: 'grc' | 'la';
  wordGloss?: string;
}

const CYLINDER: BodyCopy = {
  title: 'The cylinder',
  attribution: 'Chrysippus, reported by Cicero, De fato 42 to 43',
  claim:
    'Push it and it moves. But it rolls because of the shape it already had, and the shape is its own. The push gave the motion its beginning, not its manner.',
  word: 'volubilitas',
  wordLang: 'la',
  wordGloss: 'its own rollability',
};

const SPHERE: BodyCopy = {
  title: 'The sphere',
  attribution: 'Alexander of Aphrodisias, De fato, Bruns 185.21',
  claim:
    'Give a sphere its nature and a slope, and there is nothing else it could have done. A nature that settles the outcome has explained "up to us" away, not explained it.',
  word: 'σφαίρᾳ',
  wordLang: 'grc',
  wordGloss: 'to a sphere',
};

const R = 22;
const FLAT_TRAVEL = 158;
const SLOPE_TRAVEL = 352;
const SLOPE_DROP = 34;
const degPerUnit = 180 / Math.PI / R;

export function CylinderAndSphere({
  heading = 'The same image, turned against its author',
  standoff = 'Two readings of one simile. Both attested, and the disagreement is still open.',
  cylinder = CYLINDER,
  sphere = SPHERE,
  className,
}: CylinderAndSphereProps) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, amount: 0.5 });
  const [pushes, setPushes] = useState(0);

  useEffect(() => {
    if (inView) setPushes((n) => (n === 0 ? 1 : n));
  }, [inView]);

  const pushed = pushes > 0;
  const still = reduce || !pushed;

  return (
    <section
      ref={ref}
      className={cn('relative', className)}
      aria-labelledby="cyl-sphere-heading"
    >
      <h2
        id="cyl-sphere-heading"
        className="font-display text-[clamp(2rem,1.3rem+2.2vw,3.25rem)] leading-[1.05] tracking-[-0.015em] text-stone-900 max-w-[18ch]"
      >
        {heading}
      </h2>

      <p className="mt-5 max-w-[52ch] font-garamond text-[1.125rem] leading-[1.6] text-stone-600">
        {standoff}
      </p>

      <div className="mt-12 grid gap-x-14 gap-y-14 lg:grid-cols-2">
        <BodyPanel
          copy={cylinder}
          tone="latin"
          still={still}
          pushes={pushes}
          variant="cylinder"
        />
        <BodyPanel
          copy={sphere}
          tone="greek"
          still={still}
          pushes={pushes}
          variant="sphere"
        />
      </div>

      <div className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-3">
        <button
          type="button"
          onClick={() => setPushes((n) => n + 1)}
          className={cn(
            'inline-flex min-h-11 items-center gap-2 rounded-none border-b border-stone-400 pb-1',
            'font-body text-[0.9375rem] text-stone-700 transition-colors duration-200',
            'hover:border-stone-900 hover:text-stone-900 motion-reduce:transition-none',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#B44A12]/60 focus-visible:ring-offset-4 focus-visible:ring-offset-parchment-50',
          )}
        >
          {pushes > 1 ? 'Push both again' : 'Push both'}
        </button>
        {pushes > 1 && (
          <p className="font-body text-[0.8125rem] text-stone-500" role="status">
            Same push. Same outcome. That is rather the objection.
          </p>
        )}
      </div>
    </section>
  );
}

interface BodyPanelProps {
  copy: BodyCopy;
  tone: 'greek' | 'latin';
  variant: 'cylinder' | 'sphere';
  still: boolean;
  pushes: number;
}

function BodyPanel({ copy, tone, variant, still, pushes }: BodyPanelProps) {
  const t = TONE[tone];
  const isSphere = variant === 'sphere';
  const travel = isSphere ? SLOPE_TRAVEL : FLAT_TRAVEL;
  const drop = isSphere ? SLOPE_DROP : 0;
  const startX = isSphere ? 58 : 74;
  const startY = isSphere ? 118 : 128;

  return (
    <figure className="min-w-0">
      <svg
        viewBox="0 0 420 200"
        className="h-auto w-full overflow-visible"
        aria-hidden
        focusable="false"
      >
        {/* Ground. Flat for the cylinder, a slope for the sphere: the slope is
            Alexander's addition and it is doing all the work. */}
        <line
          x1={20}
          y1={150}
          x2={400}
          y2={isSphere ? 150 + SLOPE_DROP : 150}
          className="stroke-stone-300"
          strokeWidth={1}
        />

        {/* Strobe: where it started, kept as a ghost so the travel is measurable. */}
        <g className="opacity-30">
          <Silhouette
            variant={variant}
            x={startX}
            y={startY}
            toneStroke="stroke-stone-400"
          />
        </g>

        {still ? (
          <g>
            <Silhouette
              variant={variant}
              x={startX + travel}
              y={startY + drop}
              toneStroke={t.stroke}
              marks
            />
            <line
              x1={startX}
              y1={192}
              x2={startX + travel}
              y2={192}
              className="stroke-stone-300"
              strokeWidth={1}
              strokeDasharray="2 4"
            />
          </g>
        ) : (
          <motion.g
            key={pushes}
            initial={{ x: 0, y: 0 }}
            animate={{ x: travel, y: drop }}
            transition={{
              duration: isSphere ? 2.1 : 1.35,
              // The cylinder decelerates into rest. The sphere never does.
              ease: isSphere ? [0.7, 0, 0.84, 0] : [0.16, 1, 0.3, 1],
            }}
          >
            <g transform={`translate(${startX} ${startY})`}>
              <SilhouetteLocal variant={variant} toneStroke={t.stroke} />
              <motion.g
                initial={{ rotate: 0 }}
                animate={{ rotate: travel * degPerUnit }}
                transition={{
                  duration: isSphere ? 2.1 : 1.35,
                  ease: isSphere ? [0.7, 0, 0.84, 0] : [0.16, 1, 0.3, 1],
                }}
              >
                <SurfaceMarks toneStroke={t.stroke} />
              </motion.g>
            </g>
          </motion.g>
        )}
      </svg>

      <figcaption className="mt-6">
        <h3
          className={cn(
            'font-display text-[1.75rem] leading-[1.1] tracking-[-0.01em]',
            t.ink,
          )}
        >
          {copy.title}
        </h3>
        <p className="mt-1.5 font-body text-[0.8125rem] text-stone-500">
          {copy.attribution}
        </p>
        <p className="mt-4 max-w-[46ch] font-garamond text-[1.0625rem] leading-[1.65] text-stone-700">
          {copy.claim}
        </p>
        {copy.word && (
          <p className="mt-4 font-body text-[0.875rem] text-stone-500">
            <span
              lang={copy.wordLang}
              className={cn('font-garamond text-[1.125rem]', t.ink)}
            >
              {copy.word}
            </span>
            {copy.wordGloss ? `, ${copy.wordGloss}` : null}
          </p>
        )}
        {isSphere && !still && pushes > 0 && (
          <p className="mt-4 font-body text-[0.8125rem] text-stone-500">
            It has left the frame. It was always going to.
          </p>
        )}
      </figcaption>
    </figure>
  );
}

/** Outline only: a rolling body keeps its silhouette. */
function SilhouetteLocal({
  variant,
  toneStroke,
}: {
  variant: 'cylinder' | 'sphere';
  toneStroke: string;
}) {
  if (variant === 'cylinder') {
    return (
      <g fill="none" strokeWidth={1.25} className={toneStroke}>
        <path d={`M 0 ${-R} L -30 ${-R - 11} M 0 ${R} L -30 ${R - 11}`} />
        <ellipse cx={-30} cy={-11} rx={R * 0.5} ry={R} className="opacity-50" />
        <circle cx={0} cy={0} r={R} />
      </g>
    );
  }
  return (
    <g fill="none" strokeWidth={1.25} className={toneStroke}>
      <circle cx={0} cy={0} r={R} />
      <ellipse cx={0} cy={0} rx={R * 0.42} ry={R} className="opacity-45" />
    </g>
  );
}

function SurfaceMarks({ toneStroke }: { toneStroke: string }) {
  return (
    <g fill="none" strokeWidth={1} className={cn(toneStroke, 'opacity-70')}>
      <line x1={-R} y1={0} x2={R} y2={0} />
      <line x1={0} y1={-R} x2={0} y2={R} className="opacity-45" />
    </g>
  );
}

function Silhouette({
  variant,
  x,
  y,
  toneStroke,
  marks = false,
}: {
  variant: 'cylinder' | 'sphere';
  x: number;
  y: number;
  toneStroke: string;
  marks?: boolean;
}) {
  return (
    <g transform={`translate(${x} ${y})`}>
      <SilhouetteLocal variant={variant} toneStroke={toneStroke} />
      {marks && <SurfaceMarks toneStroke={toneStroke} />}
    </g>
  );
}

export default CylinderAndSphere;
