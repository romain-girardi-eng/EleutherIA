import { useState, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../utils/cn';

// ─── Concept data ────────────────────────────────────────────────────────────

interface Concept {
  id: string;
  label: string;
  greek?: string;
  category: 'Stoic' | 'Epicurean' | 'Aristotelian' | 'Platonic' | 'Core';
  x: number; // 0–100 in viewBox units
  y: number;
}

const CONCEPTS: Concept[] = [
  // Stoic cluster — top-left
  { id: 'fate',        label: 'Fate',        greek: 'εἱμαρμένη',      category: 'Stoic',        x: 18, y: 22 },
  { id: 'providence',  label: 'Providence',  greek: 'πρόνοια',        category: 'Stoic',        x: 26, y: 14 },
  { id: 'logos',       label: 'Logos',       greek: 'λόγος',          category: 'Stoic',        x: 12, y: 34 },
  { id: 'assent',      label: 'Assent',      greek: 'συγκατάθεσις',   category: 'Stoic',        x: 30, y: 28 },

  // Epicurean cluster — bottom-left
  { id: 'swerve',      label: 'Swerve',      greek: 'clinamen',       category: 'Epicurean',    x: 14, y: 68 },
  { id: 'atoms',       label: 'Atoms',       greek: 'ἄτομοι',         category: 'Epicurean',    x: 24, y: 76 },
  { id: 'ataraxia',    label: 'Ataraxia',    greek: 'ἀταραξία',       category: 'Epicurean',    x: 10, y: 80 },
  { id: 'pleasure',    label: 'Pleasure',    greek: 'ἡδονή',          category: 'Epicurean',    x: 28, y: 62 },

  // Aristotelian cluster — top-right
  { id: 'choice',      label: 'Choice',      greek: 'προαίρεσις',     category: 'Aristotelian', x: 72, y: 18 },
  { id: 'virtue',      label: 'Virtue',      greek: 'ἀρετή',          category: 'Aristotelian', x: 82, y: 28 },
  { id: 'deliberation',label: 'Deliberation',greek: 'βούλευσις',      category: 'Aristotelian', x: 78, y: 12 },
  { id: 'phronesis',   label: 'Wisdom',      greek: 'φρόνησις',       category: 'Aristotelian', x: 86, y: 20 },

  // Platonic cluster — bottom-right
  { id: 'soul',        label: 'Soul',        greek: 'ψυχή',           category: 'Platonic',     x: 76, y: 70 },
  { id: 'forms',       label: 'Forms',       greek: 'εἶδος',          category: 'Platonic',     x: 86, y: 62 },
  { id: 'reason',      label: 'Reason',      greek: 'νοῦς',           category: 'Platonic',     x: 84, y: 78 },
  { id: 'justice',     label: 'Justice',     greek: 'δικαιοσύνη',     category: 'Platonic',     x: 72, y: 80 },

  // Core cluster — centre
  { id: 'free_will',   label: 'Free Will',   greek: "ἐφ' ἡμῖν",      category: 'Core',         x: 50, y: 42 },
  { id: 'necessity',   label: 'Necessity',   greek: 'ἀνάγκη',         category: 'Core',         x: 44, y: 54 },
  { id: 'responsibility', label: 'Responsibility', greek: 'αἰτία',    category: 'Core',         x: 56, y: 56 },
];

const CATEGORY_COLOR: Record<Concept['category'], string> = {
  Stoic:        '#60a5fa',
  Epicurean:    '#c084fc',
  Aristotelian: '#4ade80',
  Platonic:     '#f472b6',
  Core:         '#fb923c',
};

// ─── Keyword → cluster mapping ───────────────────────────────────────────────

type ClusterKey = Concept['category'];

interface ClusterMatch {
  cluster: ClusterKey;
  /** Where to place the user dot (average of cluster ± small offset) */
  anchorX: number;
  anchorY: number;
  /** IDs of 2–3 nearest concepts */
  nearest: string[];
}

const KEYWORD_MAP: { keywords: string[]; match: ClusterMatch }[] = [
  {
    keywords: ['fate', 'destiny', 'providence', 'logos', 'stoic', 'stoicism', 'determinism',
                'determinist', 'chrysippus', 'epictetus', 'marcus', 'aurelius', 'zeno',
                'impression', 'assent', 'god', 'divine', 'order', 'cosmos', 'cosmology'],
    match: { cluster: 'Stoic', anchorX: 38, anchorY: 46, nearest: ['fate', 'logos', 'assent'] },
  },
  {
    keywords: ['atom', 'atoms', 'swerve', 'clinamen', 'epicurus', 'epicurean', 'lucretius',
                'pleasure', 'pain', 'void', 'chance', 'random', 'randomness', 'ataraxia',
                'tranquility', 'freedom', 'indeterminism', 'matter', 'materialism'],
    match: { cluster: 'Epicurean', anchorX: 36, anchorY: 60, nearest: ['swerve', 'ataraxia', 'pleasure'] },
  },
  {
    keywords: ['virtue', 'choice', 'deliberation', 'aristotle', 'aristotelian', 'wisdom',
                'phronesis', 'ethics', 'moral', 'morality', 'action', 'agency', 'habit',
                'character', 'eudaimonia', 'happiness', 'mean', 'practical', 'rational'],
    match: { cluster: 'Aristotelian', anchorX: 64, anchorY: 38, nearest: ['choice', 'virtue', 'deliberation'] },
  },
  {
    keywords: ['soul', 'forms', 'form', 'idea', 'ideas', 'plato', 'platonic', 'reason',
                'nous', 'justice', 'republic', 'immortal', 'immortality', 'knowledge',
                'ideal', 'beauty', 'truth', 'goodness', 'transcend', 'transcendent'],
    match: { cluster: 'Platonic', anchorX: 64, anchorY: 62, nearest: ['soul', 'forms', 'reason'] },
  },
];

// fallback → Core cluster
const CORE_MATCH: ClusterMatch = {
  cluster: 'Core',
  anchorX: 50,
  anchorY: 48,
  nearest: ['free_will', 'necessity', 'responsibility'],
};

function classifyWord(word: string): ClusterMatch {
  const lower = word.toLowerCase().trim();
  for (const entry of KEYWORD_MAP) {
    if (entry.keywords.some((kw) => lower.includes(kw) || kw.includes(lower))) {
      return entry.match;
    }
  }
  return CORE_MATCH;
}

// Simulated similarity scores for nearest concepts
function similarityScore(index: number): string {
  const base = [0.91, 0.87, 0.82];
  return base[index]?.toFixed(2) ?? '0.70';
}

// ─── Suggested chips ─────────────────────────────────────────────────────────

const CHIPS = ['liberty', 'destiny', 'virtue', 'pleasure', 'soul', 'logos', 'agency'];

// ─── Component ───────────────────────────────────────────────────────────────

interface UserDot {
  word: string;
  x: number;
  y: number;
  cluster: ClusterMatch;
}

interface EmbeddingScatterPlotProps {
  className?: string;
}

export function EmbeddingScatterPlot({ className }: EmbeddingScatterPlotProps) {
  const { t } = useTranslation();
  const [input, setInput] = useState('');
  const [userDot, setUserDot] = useState<UserDot | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const embed = useCallback((word: string) => {
    const trimmed = word.trim();
    if (!trimmed) return;
    const match = classifyWord(trimmed);
    // Add a small jitter so repeated embeds don't stack
    const jitter = () => (Math.random() - 0.5) * 6;
    setUserDot({
      word: trimmed,
      x: match.anchorX + jitter(),
      y: match.anchorY + jitter(),
      cluster: match,
    });
    setInput('');
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') embed(input);
  };

  const nearestConcepts = userDot
    ? userDot.cluster.nearest
        .map((id) => CONCEPTS.find((c) => c.id === id))
        .filter(Boolean) as Concept[]
    : [];

  return (
    <div className={cn('flex flex-col gap-5', className)}>
      {/* SVG Scatter Plot */}
      <div className="relative rounded-2xl overflow-hidden border border-white/10 bg-zinc-900/60 backdrop-blur-sm">
        <svg
          viewBox="0 0 100 100"
          className="w-full"
          style={{ aspectRatio: '4/3' }}
          aria-label={t('howItWorksPage.embeddings.scatter.ariaLabel')}
        >
          {/* Subtle grid */}
          <defs>
            <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
              <path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="0.3" />
            </pattern>
          </defs>
          <rect width="100" height="100" fill="url(#grid)" />

          {/* Cluster label clouds */}
          {(
            [
              { label: 'Stoic', x: 20, y: 8,  color: CATEGORY_COLOR['Stoic']        },
              { label: 'Epicurean', x: 15, y: 57, color: CATEGORY_COLOR['Epicurean']   },
              { label: 'Aristotelian', x: 72, y: 6, color: CATEGORY_COLOR['Aristotelian'] },
              { label: 'Platonic', x: 74, y: 57, color: CATEGORY_COLOR['Platonic']     },
            ] as { label: string; x: number; y: number; color: string }[]
          ).map((cl) => (
            <text
              key={cl.label}
              x={cl.x}
              y={cl.y}
              fontSize="3.5"
              fontFamily="DM Sans, system-ui, sans-serif"
              fill={cl.color}
              opacity={0.45}
              fontWeight="600"
              letterSpacing="0.5"
            >
              {cl.label.toUpperCase()}
            </text>
          ))}

          {/* Connector lines from user dot to nearest */}
          {userDot &&
            nearestConcepts.map((c) => (
              <motion.line
                key={`conn-${c.id}`}
                x1={userDot.x}
                y1={userDot.y}
                x2={c.x}
                y2={c.y}
                stroke="#fb923c"
                strokeWidth="0.4"
                strokeDasharray="1.5 1"
                opacity={0}
                animate={{ opacity: 0.6 }}
                transition={{ duration: 0.4, delay: 0.2 }}
              />
            ))}

          {/* Static concept dots */}
          {CONCEPTS.map((c) => {
            const color = CATEGORY_COLOR[c.category];
            const isNearest = userDot?.cluster.nearest.includes(c.id);
            const isHovered = hoveredId === c.id;
            return (
              <g
                key={c.id}
                onMouseEnter={() => setHoveredId(c.id)}
                onMouseLeave={() => setHoveredId(null)}
                style={{ cursor: 'default' }}
              >
                {/* Glow ring on hover or when nearest */}
                {(isHovered || isNearest) && (
                  <circle
                    cx={c.x}
                    cy={c.y}
                    r={isHovered ? 4.5 : 3.5}
                    fill="none"
                    stroke={color}
                    strokeWidth="0.5"
                    opacity={0.4}
                  />
                )}
                <circle
                  cx={c.x}
                  cy={c.y}
                  r={isHovered ? 2.2 : 1.6}
                  fill={color}
                  opacity={isNearest ? 1 : 0.75}
                  style={{ transition: 'r 0.15s, opacity 0.15s' }}
                />
                {/* Label — always show for Core, show on hover for others */}
                {(isHovered || c.category === 'Core' || isNearest) && (
                  <text
                    x={c.x + 2.5}
                    y={c.y + 1}
                    fontSize="2.8"
                    fontFamily="DM Sans, system-ui, sans-serif"
                    fill={isNearest ? color : 'rgba(255,255,255,0.8)'}
                    fontWeight={isNearest ? '700' : '400'}
                  >
                    {c.label}
                  </text>
                )}
              </g>
            );
          })}

          {/* User dot — animated in */}
          <AnimatePresence>
            {userDot && (
              <motion.g
                key={userDot.word + userDot.x}
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0 }}
                style={{ originX: `${userDot.x}%`, originY: `${userDot.y}%` }}
              >
                {/* Outer pulse ring */}
                <motion.circle
                  cx={userDot.x}
                  cy={userDot.y}
                  r={5}
                  fill="none"
                  stroke="#fb923c"
                  strokeWidth="0.5"
                  initial={{ opacity: 0.8, r: 2 }}
                  animate={{ opacity: 0, r: 7 }}
                  transition={{ duration: 1.2, repeat: Infinity, ease: 'easeOut' }}
                />
                {/* Core dot */}
                <circle cx={userDot.x} cy={userDot.y} r={2.4} fill="#fb923c" />
                {/* Label */}
                <text
                  x={userDot.x + 3}
                  y={userDot.y + 1}
                  fontSize="3.2"
                  fontFamily="DM Sans, system-ui, sans-serif"
                  fill="#fb923c"
                  fontWeight="700"
                >
                  "{userDot.word}"
                </text>
              </motion.g>
            )}
          </AnimatePresence>
        </svg>

        {/* Axis labels */}
        <div className="absolute bottom-2 right-3 text-[10px] font-body text-white/25 select-none">
          {t('howItWorksPage.embeddings.scatter.axisLabel')}
        </div>
      </div>

      {/* Nearest concepts panel */}
      <AnimatePresence>
        {userDot && nearestConcepts.length > 0 && (
          <motion.div
            key={userDot.word}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ duration: 0.3 }}
            className="rounded-xl border border-white/10 bg-zinc-900/70 px-5 py-4"
          >
            <p className="text-xs font-body uppercase tracking-widest text-white/40 mb-3">
              {t('howItWorksPage.embeddings.scatter.nearestTo', { word: userDot.word })}
            </p>
            <div className="space-y-2">
              {nearestConcepts.map((c, i) => {
                const color = CATEGORY_COLOR[c.category];
                const score = similarityScore(i);
                return (
                  <div key={c.id} className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                    <span className="font-body text-sm text-white/80 flex-1">
                      {c.label}
                      {c.greek && (
                        <span className="ml-1.5 text-white/40 text-xs">({c.greek})</span>
                      )}
                    </span>
                    {/* Similarity bar */}
                    <div className="flex items-center gap-2 shrink-0">
                      <div className="w-20 h-1.5 rounded-full bg-white/10 overflow-hidden">
                        <motion.div
                          className="h-full rounded-full"
                          style={{ backgroundColor: color }}
                          initial={{ width: 0 }}
                          animate={{ width: `${parseFloat(score) * 100}%` }}
                          transition={{ duration: 0.6, delay: i * 0.1 }}
                        />
                      </div>
                      <span className="font-mono text-xs text-white/50 w-7 text-right">{score}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input row */}
      <div className="flex gap-2">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('howItWorksPage.embeddings.scatter.placeholder')}
          className="flex-1 bg-white/5 border border-white/15 rounded-xl px-4 py-2.5 text-sm font-body text-white placeholder-white/30
                     focus:outline-none focus:ring-1 focus:ring-orange-500/60 focus:border-orange-500/40 transition-colors"
        />
        <button
          onClick={() => embed(input)}
          disabled={!input.trim()}
          className="px-4 py-2.5 rounded-xl bg-orange-500 text-white text-sm font-body font-medium
                     hover:bg-orange-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          {t('howItWorksPage.embeddings.scatter.embed')}
        </button>
      </div>

      {/* Suggested chips */}
      <div className="flex flex-wrap gap-2">
        {CHIPS.map((chip) => (
          <button
            key={chip}
            onClick={() => embed(chip)}
            className="px-3 py-1 rounded-full border border-white/15 text-xs font-body text-white/60
                       hover:border-orange-500/50 hover:text-orange-400 hover:bg-orange-500/5 transition-all"
          >
            {chip}
          </button>
        ))}
      </div>
    </div>
  );
}
