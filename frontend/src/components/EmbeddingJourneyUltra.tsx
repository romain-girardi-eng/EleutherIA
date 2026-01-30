import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import {
  Play, Pause, RotateCcw, ChevronRight, ChevronLeft,
  Type, Scissors, Table2, Waves, Brain, Layers, Compass,
  Sparkles, Send, Loader2, Lightbulb, BookOpen, ArrowRight,
  Maximize2, Minimize2
} from 'lucide-react';

// ============================================================================
// TYPES & CONSTANTS
// ============================================================================

interface Token {
  text: string;
  id: number;
  isSubword: boolean;
}

interface DemoText {
  text: string;
  category: string;
  color: string;
}

interface LiveEmbeddedPoint {
  text: string;
  position: [number, number, number];
  color: string;
  cluster: string;
}

const DEMO_TEXTS: DemoText[] = [
  { text: "What is up to us", category: "Core", color: "#fbbf24" },
  { text: "Fate determines all", category: "Stoic", color: "#60a5fa" },
  { text: "Atoms swerve freely", category: "Epicurean", color: "#c084fc" },
  { text: "Deliberate choice", category: "Aristotelian", color: "#4ade80" },
];

// Simulated vocabulary (simplified for visualization)
// In reality: vocab.txt maps string tokens → integer IDs
const VOCAB: Record<string, number> = {
  'what': 2847, 'is': 2003, 'up': 5765, 'to': 2000, 'us': 3421,
  'fate': 8934, 'deter': 12453, '##mines': 34521, 'all': 2035,
  'atoms': 15678, 'swerve': 28934, 'free': 4532, '##ly': 9823,
  'deliber': 19234, '##ate': 5678, 'choice': 7845,
  // Core philosophical terms
  'freedom': 5123, 'will': 3456, 'virtue': 6789,
  'necessity': 9012, 'cause': 2134, 'effect': 3245,
  '[UNK]': 100, '[PAD]': 0, '[CLS]': 101, '[SEP]': 102,
};

// Stage definitions with icons and durations (PRESENTATION MODE - VERY SLOW)
const STAGES = [
  {
    id: 'input',
    name: 'Text Input',
    icon: Type,
    description: 'Raw text enters the transformer',
    duration: 10000  // 10 seconds
  },
  {
    id: 'tokenize',
    name: 'Tokenization',
    icon: Scissors,
    description: 'Split into subword tokens via vocabulary lookup',
    duration: 12000  // 12 seconds
  },
  {
    id: 'vocab',
    name: 'Vocabulary Mapping',
    icon: BookOpen,
    description: 'HOW does text become a number? The vocabulary file!',
    duration: 18000  // 18 seconds - crucial stage
  },
  {
    id: 'meaning',
    name: 'How Meaning Emerges',
    icon: Lightbulb,
    description: 'The SECRET: words in similar contexts → similar vectors',
    duration: 30000  // 30 seconds - THE CORE INSIGHT (5 phases × 6 sec each)
  },
  {
    id: 'lookup',
    name: 'Embedding Lookup',
    icon: Table2,
    description: 'Token ID retrieves its learned vector from the matrix',
    duration: 15000  // 15 seconds
  },
  {
    id: 'position',
    name: 'Positional Encoding',
    icon: Waves,
    description: 'Add position information via sine/cosine waves',
    duration: 12000  // 12 seconds
  },
  {
    id: 'attention',
    name: 'Self-Attention',
    icon: Brain,
    description: 'Tokens attend to each other via Q, K, V',
    duration: 15000  // 15 seconds
  },
  {
    id: 'pooling',
    name: 'Mean Pooling',
    icon: Layers,
    description: 'Average all token vectors into one',
    duration: 12000  // 12 seconds
  },
  {
    id: 'space',
    name: 'Semantic Space',
    icon: Compass,
    description: 'The embedding lands in meaning-space',
    duration: 20000  // 20 seconds
  },
];

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

// BPE-style tokenization (simplified)
function tokenize(text: string): Token[] {
  const words = text.toLowerCase().split(/\s+/);
  const tokens: Token[] = [];

  // Add [CLS] token
  tokens.push({ text: '[CLS]', id: 101, isSubword: false });

  words.forEach(word => {
    // Check if word is in vocab
    if (VOCAB[word]) {
      tokens.push({ text: word, id: VOCAB[word], isSubword: false });
    } else {
      // BPE-style: split into subwords
      const mid = Math.ceil(word.length * 0.6);
      const prefix = word.slice(0, mid);
      const suffix = '##' + word.slice(mid);

      tokens.push({
        text: prefix,
        id: VOCAB[prefix] || Math.floor(Math.random() * 30000) + 1000,
        isSubword: false
      });
      tokens.push({
        text: suffix,
        id: VOCAB[suffix] || Math.floor(Math.random() * 30000) + 1000,
        isSubword: true
      });
    }
  });

  // Add [SEP] token
  tokens.push({ text: '[SEP]', id: 102, isSubword: false });

  return tokens;
}

// Generate deterministic embedding row for visualization
function generateEmbeddingRow(tokenId: number, dim: number = 8): number[] {
  const row: number[] = [];
  for (let i = 0; i < dim; i++) {
    // Use sin/cos for deterministic but varied values
    row.push(Math.sin(tokenId * (i + 1) * 0.1) * Math.cos(tokenId * 0.05 + i * 0.3));
  }
  return row;
}

// Generate positional encoding values
function generatePositionalEncoding(pos: number, dim: number = 8): number[] {
  const pe: number[] = [];
  for (let i = 0; i < dim; i++) {
    const div = Math.pow(10000, (2 * Math.floor(i / 2)) / dim);
    if (i % 2 === 0) {
      pe.push(Math.sin(pos / div));
    } else {
      pe.push(Math.cos(pos / div));
    }
  }
  return pe;
}

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

// NEW: "How Meaning Emerges" explanation component
function MeaningExplainer({ phase }: { phase: number }) {
  const phases = [
    {
      title: "The Distributional Hypothesis",
      subtitle: '"You shall know a word by the company it keeps" — J.R. Firth, 1957',
      content: "The fundamental insight: words that appear in SIMILAR CONTEXTS tend to have SIMILAR MEANINGS.",
      icon: "💡",
      color: "from-yellow-500/20 to-amber-500/20",
      borderColor: "border-yellow-500/40"
    },
    {
      title: "Context Creates Meaning",
      subtitle: "Consider these sentences:",
      content: null,
      examples: [
        { text: "The ___ barked at the mailman", highlight: "dog" },
        { text: "I took my ___ for a walk", highlight: "dog" },
        { text: "The ___ wagged its tail happily", highlight: "dog" },
      ],
      explanation: "What word fits? 'Dog' appears in contexts about pets, walks, barking, tails...",
      icon: "📖",
      color: "from-cyan-500/20 to-blue-500/20",
      borderColor: "border-cyan-500/40"
    },
    {
      title: "Similar Contexts → Similar Vectors",
      subtitle: "During training, the model learns:",
      content: null,
      pairs: [
        { word1: "king", word2: "queen", shared: "royalty, throne, crown, palace" },
        { word1: "dog", word2: "cat", shared: "pet, animal, fur, paws" },
        { word1: "freedom", word2: "liberty", shared: "rights, choice, will" },
      ],
      explanation: "Words sharing contexts get PULLED CLOSER in vector space!",
      icon: "🧲",
      color: "from-purple-500/20 to-pink-500/20",
      borderColor: "border-purple-500/40"
    },
    {
      title: "The Famous Analogy",
      subtitle: "Vector arithmetic captures relationships:",
      content: null,
      analogy: {
        equation: "king − man + woman ≈ queen",
        explanation: "The 'royalty' direction + 'female' direction = queen's position"
      },
      visualization: true,
      icon: "👑",
      color: "from-amber-500/20 to-orange-500/20",
      borderColor: "border-amber-500/40"
    },
    {
      title: "Training: Billions of Contexts",
      subtitle: "The model sees MASSIVE amounts of text:",
      content: null,
      stats: [
        { label: "Training tokens", value: "~2 trillion" },
        { label: "Books, articles, web pages", value: "∞ contexts" },
        { label: "Result", value: "Meaning emerges from patterns" },
      ],
      finalInsight: "After seeing 'freedom' and 'liberty' in billions of similar contexts, their vectors become nearly identical — they MEAN nearly the same thing!",
      icon: "🚀",
      color: "from-green-500/20 to-emerald-500/20",
      borderColor: "border-green-500/40"
    }
  ];

  const currentPhase = phases[Math.min(phase, phases.length - 1)];

  return (
    <motion.div
      key={phase}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.6 }}
      className={`p-6 rounded-2xl bg-gradient-to-br ${currentPhase.color} border ${currentPhase.borderColor} max-w-2xl mx-auto`}
    >
      {/* Phase indicator */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{currentPhase.icon}</span>
          <span className="text-white/50 text-xs font-mono">Phase {phase + 1}/5</span>
        </div>
        <div className="flex gap-1">
          {phases.map((_, i) => (
            <div
              key={i}
              className={`w-2 h-2 rounded-full transition-all ${
                i <= phase ? 'bg-white/80' : 'bg-white/20'
              }`}
            />
          ))}
        </div>
      </div>

      {/* Title */}
      <h3 className="text-xl font-bold text-white mb-1">{currentPhase.title}</h3>
      <p className="text-white/60 text-sm italic mb-4">{currentPhase.subtitle}</p>

      {/* Content varies by phase */}
      {currentPhase.content && (
        <p className="text-white/80 text-base leading-relaxed">{currentPhase.content}</p>
      )}

      {/* Phase 1: Examples */}
      {currentPhase.examples && (
        <div className="space-y-3 mb-4">
          {currentPhase.examples.map((ex, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.3 }}
              className="bg-slate-900/50 rounded-lg p-3 font-mono text-sm"
            >
              <span className="text-white/70">{ex.text.split('___')[0]}</span>
              <span className="text-cyan-400 font-bold bg-cyan-500/20 px-2 py-0.5 rounded">___</span>
              <span className="text-white/70">{ex.text.split('___')[1]}</span>
            </motion.div>
          ))}
          <p className="text-white/60 text-sm mt-3">{currentPhase.explanation}</p>
        </div>
      )}

      {/* Phase 2: Word pairs */}
      {currentPhase.pairs && (
        <div className="space-y-3 mb-4">
          {currentPhase.pairs.map((pair, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.4 }}
              className="flex items-center gap-3 bg-slate-900/50 rounded-lg p-3"
            >
              <span className="text-cyan-400 font-mono font-bold">{pair.word1}</span>
              <span className="text-white/30">≈</span>
              <span className="text-purple-400 font-mono font-bold">{pair.word2}</span>
              <ArrowRight className="w-4 h-4 text-white/30" />
              <span className="text-white/50 text-xs">{pair.shared}</span>
            </motion.div>
          ))}
          <p className="text-green-400 text-sm font-medium mt-3">{currentPhase.explanation}</p>
        </div>
      )}

      {/* Phase 3: Analogy */}
      {currentPhase.analogy && (
        <div className="text-center mb-4">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3, type: 'spring' }}
            className="inline-block bg-slate-900/70 rounded-xl p-6 border border-white/10"
          >
            <div className="text-2xl font-mono text-white mb-3">
              <span className="text-amber-400">king</span>
              <span className="text-white/50"> − </span>
              <span className="text-blue-400">man</span>
              <span className="text-white/50"> + </span>
              <span className="text-pink-400">woman</span>
              <span className="text-white/50"> ≈ </span>
              <span className="text-purple-400">queen</span>
            </div>
            <p className="text-white/50 text-sm">{currentPhase.analogy.explanation}</p>
          </motion.div>

          {/* Simple vector visualization */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="mt-4 h-32 relative"
          >
            <svg className="w-full h-full" viewBox="0 0 400 120">
              {/* Axes */}
              <line x1="50" y1="100" x2="350" y2="100" stroke="rgba(255,255,255,0.2)" strokeWidth="1" />
              <line x1="50" y1="100" x2="50" y2="20" stroke="rgba(255,255,255,0.2)" strokeWidth="1" />
              <text x="360" y="105" fill="rgba(255,255,255,0.4)" fontSize="10">gender</text>
              <text x="40" y="15" fill="rgba(255,255,255,0.4)" fontSize="10">royalty</text>

              {/* Points */}
              <motion.circle
                initial={{ r: 0 }}
                animate={{ r: 8 }}
                transition={{ delay: 0.5 }}
                cx="100" cy="80" fill="#3b82f6"
              />
              <text x="90" y="95" fill="#3b82f6" fontSize="10">man</text>

              <motion.circle
                initial={{ r: 0 }}
                animate={{ r: 8 }}
                transition={{ delay: 0.7 }}
                cx="280" cy="80" fill="#ec4899"
              />
              <text x="265" y="95" fill="#ec4899" fontSize="10">woman</text>

              <motion.circle
                initial={{ r: 0 }}
                animate={{ r: 8 }}
                transition={{ delay: 0.9 }}
                cx="100" cy="35" fill="#f59e0b"
              />
              <text x="90" y="28" fill="#f59e0b" fontSize="10">king</text>

              <motion.circle
                initial={{ r: 0 }}
                animate={{ r: 8 }}
                transition={{ delay: 1.1 }}
                cx="280" cy="35" fill="#a855f7"
              />
              <text x="265" y="28" fill="#a855f7" fontSize="10">queen</text>

              {/* Arrows showing relationships */}
              <motion.path
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ delay: 1.3, duration: 0.5 }}
                d="M 108 80 L 272 80"
                stroke="rgba(255,255,255,0.3)"
                strokeWidth="1"
                strokeDasharray="4"
                fill="none"
                markerEnd="url(#arrowhead)"
              />
              <motion.path
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ delay: 1.5, duration: 0.5 }}
                d="M 108 35 L 272 35"
                stroke="rgba(255,255,255,0.3)"
                strokeWidth="1"
                strokeDasharray="4"
                fill="none"
              />
              <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                  <polygon points="0 0, 10 3.5, 0 7" fill="rgba(255,255,255,0.3)" />
                </marker>
              </defs>
            </svg>
          </motion.div>
        </div>
      )}

      {/* Phase 4: Training stats */}
      {currentPhase.stats && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            {currentPhase.stats.map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.3 }}
                className="bg-slate-900/50 rounded-lg p-3 text-center"
              >
                <div className="text-green-400 font-bold text-lg">{stat.value}</div>
                <div className="text-white/40 text-xs">{stat.label}</div>
              </motion.div>
            ))}
          </div>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2 }}
            className="p-4 bg-gradient-to-r from-green-500/10 to-emerald-500/10 rounded-xl border border-green-500/30"
          >
            <Sparkles className="w-5 h-5 text-green-400 mb-2" />
            <p className="text-white/80 text-sm leading-relaxed">{currentPhase.finalInsight}</p>
          </motion.div>
        </div>
      )}
    </motion.div>
  );
}

// NEW: Vocabulary Mapping Visualization
function VocabularyMappingViz({ tokens, currentHighlight }: { tokens: Token[]; currentHighlight: number | null }) {
  const vocabEntries = [
    { token: "[PAD]", id: 0, type: "special" },
    { token: "[UNK]", id: 100, type: "special" },
    { token: "[CLS]", id: 101, type: "special" },
    { token: "[SEP]", id: 102, type: "special" },
    { token: "...", id: null, type: "ellipsis" },
    { token: "the", id: 1996, type: "common" },
    { token: "is", id: 2003, type: "common" },
    { token: "to", id: 2000, type: "common" },
    { token: "...", id: null, type: "ellipsis" },
    { token: "what", id: 2847, type: "word" },
    { token: "us", id: 3421, type: "word" },
    { token: "free", id: 4532, type: "word" },
    { token: "up", id: 5765, type: "word" },
    { token: "...", id: null, type: "ellipsis" },
    { token: "fate", id: 8934, type: "word" },
    { token: "##ly", id: 9823, type: "subword" },
    { token: "...", id: null, type: "ellipsis" },
    { token: "atoms", id: 15678, type: "word" },
    { token: "deliber", id: 19234, type: "word" },
    { token: "swerve", id: 28934, type: "word" },
    { token: "##mines", id: 34521, type: "subword" },
  ];

  const highlightedToken = currentHighlight !== null ? tokens[currentHighlight] : null;

  return (
    <div className="bg-slate-900/80 rounded-xl p-4 border border-white/10">
      <div className="flex items-center gap-2 mb-4">
        <BookOpen className="w-5 h-5 text-cyan-400" />
        <span className="text-cyan-400 font-mono text-sm">vocab.txt</span>
        <span className="text-white/30 text-xs ml-auto">30,522 entries</span>
      </div>

      {/* The key insight */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-4 p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/30"
      >
        <div className="flex items-start gap-2">
          <Lightbulb className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-yellow-400 font-medium text-sm">The Vocabulary File!</p>
            <p className="text-white/60 text-xs mt-1">
              A simple text file where LINE NUMBER = TOKEN ID.
              Line 2847 contains "what", so "what" → ID 2847
            </p>
          </div>
        </div>
      </motion.div>

      {/* Vocab entries */}
      <div className="space-y-1 max-h-60 overflow-y-auto font-mono text-xs">
        {vocabEntries.map((entry, i) => {
          const isHighlighted = highlightedToken && entry.id === highlightedToken.id;

          if (entry.type === 'ellipsis') {
            return (
              <div key={i} className="text-white/20 text-center py-1">⋮</div>
            );
          }

          return (
            <motion.div
              key={i}
              animate={isHighlighted ? {
                backgroundColor: ['rgba(34,211,238,0.2)', 'rgba(34,211,238,0.4)', 'rgba(34,211,238,0.2)'],
              } : {}}
              transition={{ duration: 1, repeat: isHighlighted ? Infinity : 0 }}
              className={`flex items-center gap-2 px-2 py-1 rounded transition-all ${
                isHighlighted
                  ? 'bg-cyan-500/30 border border-cyan-500/50'
                  : 'hover:bg-white/5'
              }`}
            >
              <span className={`w-12 text-right ${
                isHighlighted ? 'text-cyan-300' : 'text-white/30'
              }`}>
                {entry.id}
              </span>
              <span className="text-white/20">│</span>
              <span className={`${
                entry.type === 'special' ? 'text-yellow-400' :
                entry.type === 'subword' ? 'text-purple-400' :
                entry.type === 'common' ? 'text-white/50' :
                isHighlighted ? 'text-cyan-300' : 'text-white/70'
              }`}>
                {entry.token}
              </span>
              {isHighlighted && (
                <motion.span
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="ml-auto text-cyan-400"
                >
                  ← FOUND!
                </motion.span>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Current lookup */}
      {highlightedToken && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 p-3 bg-cyan-500/10 rounded-lg border border-cyan-500/30"
        >
          <div className="flex items-center justify-center gap-3">
            <span className="text-white font-mono">"{highlightedToken.text}"</span>
            <ArrowRight className="w-4 h-4 text-cyan-400" />
            <span className="text-cyan-400 font-mono font-bold">ID: {highlightedToken.id}</span>
          </div>
        </motion.div>
      )}
    </div>
  );
}

// Embedding Matrix Visualization
function EmbeddingMatrix({
  highlightRow,
  extractedVector,
}: {
  highlightRow: number | null;
  extractedVector: number[] | null;
}) {
  const VISIBLE_ROWS = 10;
  const COLS = 8;

  // Generate matrix data (simulated 30522 x 768 → showing 10 x 8)
  const matrixData = Array.from({ length: VISIBLE_ROWS }, (_, i) => {
    const tokenId = highlightRow ? Math.max(0, highlightRow - 4) + i : i * 3000;
    return {
      tokenId,
      values: generateEmbeddingRow(tokenId, COLS),
      isHighlighted: tokenId === highlightRow
    };
  });

  return (
    <div className="relative">
      {/* Matrix Header */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-cyan-400 text-xs font-mono">Embedding Matrix (learned weights)</span>
        <span className="text-white/40 text-[10px]">30,522 × 768</span>
      </div>

      {/* Matrix Grid */}
      <div className="bg-slate-900/80 rounded-lg p-2 border border-white/10 overflow-x-auto">
        {/* Column headers */}
        <div className="flex gap-1 mb-1 pl-12">
          {Array.from({ length: COLS }, (_, i) => (
            <div key={i} className="w-10 text-center text-[9px] text-white/30 font-mono">
              d{i}
            </div>
          ))}
          <div className="w-8 text-center text-[9px] text-white/30">...</div>
        </div>

        {/* Rows */}
        {matrixData.map((row) => (
          <motion.div
            key={row.tokenId}
            className={`flex gap-1 items-center py-0.5 rounded transition-all ${
              row.isHighlighted
                ? 'bg-cyan-500/30 scale-[1.02]'
                : ''
            }`}
            animate={row.isHighlighted ? {
              boxShadow: ['0 0 0px rgba(34,211,238,0)', '0 0 20px rgba(34,211,238,0.5)', '0 0 0px rgba(34,211,238,0)']
            } : {}}
            transition={{ duration: 1.5, repeat: row.isHighlighted ? Infinity : 0 }}
          >
            {/* Row index (token ID) */}
            <div className={`w-10 text-right text-[9px] font-mono pr-1 ${
              row.isHighlighted ? 'text-cyan-300 font-bold' : 'text-white/30'
            }`}>
              {row.tokenId}
            </div>
            <div className="text-white/20 text-[9px]">→</div>

            {/* Values */}
            {row.values.map((val, colIdx) => (
              <motion.div
                key={colIdx}
                className={`w-10 h-5 flex items-center justify-center text-[8px] font-mono rounded ${
                  row.isHighlighted
                    ? val > 0
                      ? 'bg-cyan-500/50 text-cyan-100'
                      : 'bg-purple-500/50 text-purple-100'
                    : val > 0
                      ? 'bg-cyan-500/10 text-cyan-400/50'
                      : 'bg-purple-500/10 text-purple-400/50'
                }`}
                animate={row.isHighlighted && extractedVector ? {
                  scale: [1, 1.15, 1],
                  y: [0, -3, 0]
                } : {}}
                transition={{ delay: colIdx * 0.08, duration: 0.4 }}
              >
                {val.toFixed(2)}
              </motion.div>
            ))}

            <div className="w-8 text-center text-white/20 text-[9px]">...</div>
          </motion.div>
        ))}

        {/* Show there's more rows */}
        <div className="text-center text-white/20 text-[9px] mt-1">
          ⋮ (30,512 more rows)
        </div>
      </div>

      {/* Extracted vector animation */}
      <AnimatePresence>
        {extractedVector && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="mt-3 p-2 bg-cyan-500/20 rounded-lg border border-cyan-500/50"
          >
            <div className="text-cyan-300 text-xs mb-1">✓ Extracted Vector:</div>
            <div className="flex gap-1 flex-wrap">
              {extractedVector.map((val, i) => (
                <motion.span
                  key={i}
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.08 }}
                  className="text-[9px] font-mono text-white bg-cyan-500/30 px-1.5 py-0.5 rounded"
                >
                  {val.toFixed(3)}
                </motion.span>
              ))}
              <span className="text-white/40 text-[9px]">...×768</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Positional Encoding Visualization
function PositionalEncodingViz({
  positions,
  currentPos
}: {
  positions: number;
  currentPos: number | null;
}) {
  const width = 300;
  const height = 120;

  return (
    <div className="relative">
      <div className="text-cyan-400 text-xs font-mono mb-2">Positional Encoding Waves</div>

      {/* SVG Wave visualization */}
      <svg width={width} height={height} className="bg-slate-900/50 rounded-lg">
        {/* Sine waves at different frequencies */}
        {[0, 1, 2, 3].map(dim => {
          const freq = Math.pow(10000, dim / 4);
          const points = Array.from({ length: positions * 10 }, (_, i) => {
            const x = (i / (positions * 10 - 1)) * width;
            const pos = i / 10;
            const y = height / 2 + (dim % 2 === 0
              ? Math.sin(pos / freq) * (height / 4 - dim * 5)
              : Math.cos(pos / freq) * (height / 4 - dim * 5));
            return `${x},${y}`;
          }).join(' ');

          return (
            <g key={dim}>
              <polyline
                points={points}
                fill="none"
                stroke={dim % 2 === 0 ? '#22d3ee' : '#a855f7'}
                strokeWidth="1.5"
                opacity={0.6}
              />
              <text
                x={width - 25}
                y={15 + dim * 12}
                fill={dim % 2 === 0 ? '#22d3ee' : '#a855f7'}
                fontSize="8"
                opacity={0.8}
              >
                {dim % 2 === 0 ? 'sin' : 'cos'}(d{dim})
              </text>
            </g>
          );
        })}

        {/* Current position marker */}
        {currentPos !== null && (
          <motion.line
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            x1={(currentPos / positions) * width}
            y1={0}
            x2={(currentPos / positions) * width}
            y2={height}
            stroke="#fbbf24"
            strokeWidth="2"
            strokeDasharray="4,4"
          />
        )}

        {/* Position markers */}
        {Array.from({ length: positions }, (_, i) => (
          <g key={i}>
            <circle
              cx={(i / (positions - 1)) * width}
              cy={height - 10}
              r={currentPos === i ? 6 : 4}
              fill={currentPos === i ? '#fbbf24' : '#ffffff20'}
            />
            <text
              x={(i / (positions - 1)) * width}
              y={height - 20}
              fill="#ffffff60"
              fontSize="8"
              textAnchor="middle"
            >
              {i}
            </text>
          </g>
        ))}
      </svg>

      {/* Formula */}
      <div className="mt-2 text-[10px] text-white/50 font-mono text-center">
        PE(pos, 2i) = sin(pos / 10000^(2i/d)) &nbsp;|&nbsp; PE(pos, 2i+1) = cos(pos / 10000^(2i/d))
      </div>
    </div>
  );
}

// Attention Heatmap
function AttentionHeatmap({
  tokens,
  weights
}: {
  tokens: Token[];
  weights: number[][];
}) {
  const maxWeight = Math.max(...weights.flat());

  return (
    <div className="relative">
      <div className="flex items-center justify-between mb-2">
        <span className="text-cyan-400 text-xs font-mono">Attention Scores (softmax(QK^T/√d))</span>
      </div>

      <div className="bg-slate-900/80 rounded-lg p-2 border border-white/10 overflow-x-auto">
        {/* Header row (Keys) */}
        <div className="flex gap-0.5 mb-0.5 pl-16">
          {tokens.slice(0, 8).map((token, j) => (
            <div
              key={j}
              className="w-12 text-center text-[8px] text-purple-300 font-mono truncate"
              title={token.text}
            >
              K:{token.text.slice(0, 4)}
            </div>
          ))}
        </div>

        {/* Heatmap rows (Queries) */}
        {tokens.slice(0, 8).map((token, i) => (
          <div key={i} className="flex gap-0.5 items-center">
            <div className="w-14 text-right text-[8px] text-cyan-300 font-mono pr-1 truncate">
              Q:{token.text.slice(0, 5)}
            </div>
            <div className="text-white/20 text-[8px] w-2">→</div>
            {weights[i]?.slice(0, 8).map((weight, j) => {
              const intensity = weight / maxWeight;
              return (
                <motion.div
                  key={j}
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: (i * 8 + j) * 0.08 }}
                  className="w-12 h-8 flex items-center justify-center text-[9px] font-mono rounded"
                  style={{
                    backgroundColor: `rgba(34, 211, 238, ${intensity * 0.8})`,
                    color: intensity > 0.5 ? 'white' : 'rgba(255,255,255,0.6)'
                  }}
                  title={`Q[${i}] attending to K[${j}]: ${weight.toFixed(3)}`}
                >
                  {weight.toFixed(2)}
                </motion.div>
              );
            })}
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-2 flex items-center justify-center gap-4 text-[9px] text-white/50">
        <span>Q = Query (what am I looking for?)</span>
        <span>K = Key (what do I contain?)</span>
        <span>Brighter = Higher attention</span>
      </div>
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

interface Props {
  className?: string;
  autoPlay?: boolean;
}

export default function EmbeddingJourneyUltra({ className = '', autoPlay = false }: Props) {
  const [currentStage, setCurrentStage] = useState(0);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [selectedText, setSelectedText] = useState(0);
  const [tokens, setTokens] = useState<Token[]>([]);
  const [displayedText, setDisplayedText] = useState('');
  const [attentionWeights, setAttentionWeights] = useState<number[][]>([]);
  const [highlightedTokenIdx, setHighlightedTokenIdx] = useState<number | null>(null);
  const [extractedVectors, setExtractedVectors] = useState<number[][]>([]);
  const [positionHighlight, setPositionHighlight] = useState<number | null>(null);
  const [meaningPhase, setMeaningPhase] = useState(0);
  const [vocabHighlight, setVocabHighlight] = useState<number | null>(null);

  // Live demo state
  const [liveInput, setLiveInput] = useState('');
  const [isEmbedding, setIsEmbedding] = useState(false);
  const [liveEmbeddedPoints, setLiveEmbeddedPoints] = useState<LiveEmbeddedPoint[]>([]);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [embeddingStep, setEmbeddingStep] = useState<'idle' | 'vectorizing' | 'comparing' | 'placing'>('idle');
  const [currentVector, setCurrentVector] = useState<number[] | null>(null);
  const [similarities, setSimilarities] = useState<{ cluster: string; score: number; color: string }[]>([]);

  // Real KG nodes from API
  const [realKGNodes, setRealKGNodes] = useState<{
    id: number | string;
    node_id: string;
    name: string;
    school: string;
    type: string;
    position_3d: { x: number; y: number; z: number };
    color: string;
  }[]>([]);
  const [kgNodesLoaded, setKgNodesLoaded] = useState(false);
  const initializedWithRealNodesRef = useRef(false);

  // Three.js refs
  const mountRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const semanticSpaceRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const composerRef = useRef<EffectComposer | null>(null);
  const frameIdRef = useRef<number | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const livePointsGroupRef = useRef<THREE.Group | null>(null);

  const currentText = DEMO_TEXTS[selectedText].text;
  const currentCategory = DEMO_TEXTS[selectedText].category;
  const currentColor = DEMO_TEXTS[selectedText].color;

  // Initialize tokens when text changes
  useEffect(() => {
    const newTokens = tokenize(currentText);
    setTokens(newTokens);

    // Generate attention weights
    const weights: number[][] = [];
    for (let i = 0; i < newTokens.length; i++) {
      const row: number[] = [];
      for (let j = 0; j < newTokens.length; j++) {
        const distance = Math.abs(i - j);
        const base = Math.exp(-distance * 0.3);
        const special = (newTokens[i].text === '[CLS]' || newTokens[j].text === '[CLS]') ? 0.3 : 0;
        row.push(base + special + Math.random() * 0.1);
      }
      const sum = row.reduce((a, b) => a + b, 0);
      weights.push(row.map(w => w / sum));
    }
    setAttentionWeights(weights);

    // Generate extracted vectors
    setExtractedVectors(newTokens.map(t => generateEmbeddingRow(t.id, 8)));
  }, [currentText]);

  // Fetch real KG nodes from API for semantic space visualization
  useEffect(() => {
    const fetchRealKGNodes = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/api/embeddings/semantic-space`);
        if (response.ok) {
          const data = await response.json();
          setRealKGNodes(data.nodes || []);
          setKgNodesLoaded(true);
          console.log(`Loaded ${data.nodes?.length || 0} real KG nodes from API`);
        }
      } catch (error) {
        console.error('Failed to load real KG nodes:', error);
        // Keep using simulated data if API fails
      }
    };

    fetchRealKGNodes();
  }, []);

  // Typing animation for stage 0
  useEffect(() => {
    if (currentStage === 0) {
      setDisplayedText('');
      let index = 0;
      const interval = setInterval(() => {
        if (index < currentText.length) {
          setDisplayedText(currentText.slice(0, index + 1));
          index++;
        } else {
          clearInterval(interval);
        }
      }, 150); // PRESENTATION: 150ms per character (slow typing)
      return () => clearInterval(interval);
    }
  }, [currentStage, currentText]);

  // Stage 2: Vocabulary mapping animation
  useEffect(() => {
    if (currentStage === 2) {
      let idx = 0;
      const interval = setInterval(() => {
        if (idx < tokens.length) {
          setVocabHighlight(idx);
          idx++;
        } else {
          clearInterval(interval);
        }
      }, 2000); // PRESENTATION: 2 seconds per token
      return () => clearInterval(interval);
    } else {
      setVocabHighlight(null);
    }
  }, [currentStage, tokens.length]);

  // Stage 3: Meaning explanation phases
  useEffect(() => {
    if (currentStage === 3) {
      setMeaningPhase(0);
      let phase = 0;
      const interval = setInterval(() => {
        phase++;
        if (phase < 5) {
          setMeaningPhase(phase);
        } else {
          clearInterval(interval);
        }
      }, 5500); // PRESENTATION: 5.5 seconds per phase (5 phases = 27.5 seconds)
      return () => clearInterval(interval);
    }
  }, [currentStage]);

  // Stage 4: Embedding lookup animation
  useEffect(() => {
    if (currentStage === 4) {
      let idx = 0;
      const interval = setInterval(() => {
        if (idx < tokens.length) {
          setHighlightedTokenIdx(idx);
          idx++;
        } else {
          clearInterval(interval);
        }
      }, 1800); // PRESENTATION: 1.8 seconds per token
      return () => clearInterval(interval);
    } else {
      setHighlightedTokenIdx(null);
    }
  }, [currentStage, tokens.length]);

  // Stage 5: Position encoding animation
  useEffect(() => {
    if (currentStage === 5) {
      let pos = 0;
      const interval = setInterval(() => {
        if (pos < tokens.length) {
          setPositionHighlight(pos);
          pos++;
        } else {
          clearInterval(interval);
        }
      }, 1500); // PRESENTATION: 1.5 seconds per position
      return () => clearInterval(interval);
    } else {
      setPositionHighlight(null);
    }
  }, [currentStage, tokens.length]);

  // Auto-advance stages when playing (using per-stage durations)
  useEffect(() => {
    if (!isPlaying) return;

    const duration = STAGES[currentStage].duration;
    const timer = setTimeout(() => {
      if (currentStage < STAGES.length - 1) {
        setCurrentStage(prev => prev + 1);
      } else {
        setIsPlaying(false);
      }
    }, duration);

    return () => clearTimeout(timer);
  }, [isPlaying, currentStage]);

  // Initialize Three.js scene for final stage
  const initThreeScene = useCallback(() => {
    if (!mountRef.current || sceneRef.current) return;

    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050510);
    scene.fog = new THREE.FogExp2(0x050510, 0.004);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
    camera.position.set(60, 40, 90);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Post-processing
    const composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(width, height),
      1.2, 0.4, 0.85
    );
    composer.addPass(bloomPass);
    composerRef.current = composer;

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.2; // Slower rotation
    controlsRef.current = controls;

    // Group for live embedded points
    const liveGroup = new THREE.Group();
    scene.add(liveGroup);
    livePointsGroupRef.current = liveGroup;

    // Helper to create cluster label sprites
    const createClusterLabel = (text: string, color: THREE.Color): THREE.Sprite => {
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d')!;
      canvas.width = 256;
      canvas.height = 80;

      // Background with gradient
      const gradient = context.createLinearGradient(0, 0, canvas.width, 0);
      gradient.addColorStop(0, 'rgba(0, 0, 0, 0)');
      gradient.addColorStop(0.2, 'rgba(0, 0, 0, 0.6)');
      gradient.addColorStop(0.8, 'rgba(0, 0, 0, 0.6)');
      gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
      context.fillStyle = gradient;
      context.fillRect(0, 0, canvas.width, canvas.height);

      // Text with glow
      context.shadowColor = `#${color.getHexString()}`;
      context.shadowBlur = 10;
      context.fillStyle = `#${color.getHexString()}`;
      context.font = 'bold 32px sans-serif';
      context.textAlign = 'center';
      context.textBaseline = 'middle';
      context.fillText(text, canvas.width / 2, canvas.height / 2);

      const texture = new THREE.CanvasTexture(canvas);
      const material = new THREE.SpriteMaterial({
        map: texture,
        transparent: true,
        depthTest: false
      });
      const sprite = new THREE.Sprite(material);
      sprite.scale.set(30, 10, 1);
      return sprite;
    };

    // Category config for fallback AND for target position lookup
    const categoryConfigs = [
      { name: 'Core', color: 0xfbbf24, center: [0, 0, 0] },
      { name: 'Stoic', color: 0x60a5fa, center: [-35, 20, -15] },
      { name: 'Epicurean', color: 0xc084fc, center: [35, 15, 25] },
      { name: 'Aristotelian', color: 0x4ade80, center: [-25, -25, 30] },
      { name: 'Platonic', color: 0xf472b6, center: [30, -20, -30] },
    ];

    // Use REAL KG nodes if loaded, otherwise fallback to simulated
    if (realKGNodes.length > 0) {
      console.log(`Rendering ${realKGNodes.length} REAL KG nodes in semantic space`);

      // Group nodes by school and create point clouds
      const nodesBySchool: Record<string, typeof realKGNodes> = {};
      for (const node of realKGNodes) {
        if (!nodesBySchool[node.school]) nodesBySchool[node.school] = [];
        nodesBySchool[node.school].push(node);
      }

      // Render each school's nodes as a point cloud
      Object.entries(nodesBySchool).forEach(([school, nodes]) => {
        const count = nodes.length;
        const positions = new Float32Array(count * 3);
        const colors = new Float32Array(count * 3);

        // Calculate centroid for label placement
        let cx = 0, cy = 0, cz = 0;

        nodes.forEach((node, i) => {
          positions[i * 3] = node.position_3d.x;
          positions[i * 3 + 1] = node.position_3d.y;
          positions[i * 3 + 2] = node.position_3d.z;

          cx += node.position_3d.x;
          cy += node.position_3d.y;
          cz += node.position_3d.z;

          const color = new THREE.Color(node.color);
          colors[i * 3] = color.r;
          colors[i * 3 + 1] = color.g;
          colors[i * 3 + 2] = color.b;
        });

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const material = new THREE.PointsMaterial({
          size: 4,
          vertexColors: true,
          transparent: true,
          opacity: 0.9,
          sizeAttenuation: true,
        });

        const points = new THREE.Points(geometry, material);
        scene.add(points);

        // Add cluster label at centroid
        if (school !== 'Unknown') {
          const centroid = { x: cx / count, y: cy / count, z: cz / count };
          const labelColor = new THREE.Color(nodes[0].color);
          const label = createClusterLabel(school, labelColor);
          label.position.set(centroid.x, centroid.y + 15, centroid.z);
          scene.add(label);
        }
      });
    } else {
      // Fallback: simulated clusters (if API hasn't loaded yet)
      console.log('Using simulated clusters (real KG nodes not loaded)');

      categoryConfigs.forEach(config => {
        const count = 20;
        const positions = new Float32Array(count * 3);
        const colors = new Float32Array(count * 3);
        const color = new THREE.Color(config.color);

        for (let i = 0; i < count; i++) {
          positions[i * 3] = config.center[0] + (Math.random() - 0.5) * 25;
          positions[i * 3 + 1] = config.center[1] + (Math.random() - 0.5) * 25;
          positions[i * 3 + 2] = config.center[2] + (Math.random() - 0.5) * 25;
          colors[i * 3] = color.r;
          colors[i * 3 + 1] = color.g;
          colors[i * 3 + 2] = color.b;
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const material = new THREE.PointsMaterial({
          size: 5,
          vertexColors: true,
          transparent: true,
          opacity: 0.8,
          sizeAttenuation: true,
        });

        const points = new THREE.Points(geometry, material);
        scene.add(points);

        // Add cluster label
        const label = createClusterLabel(config.name, color);
        label.position.set(config.center[0], config.center[1] + 18, config.center[2]);
        scene.add(label);
      });
    }

    // Add coordinate axes
    const axisLength = 50;
    const axisColors = [0xff4444, 0x44ff44, 0x4444ff];

    axisColors.forEach((color, i) => {
      const dir = new THREE.Vector3(
        i === 0 ? 1 : 0,
        i === 1 ? 1 : 0,
        i === 2 ? 1 : 0
      );
      const origin = new THREE.Vector3(-axisLength/2, -axisLength/2, -axisLength/2);
      const arrow = new THREE.ArrowHelper(dir, origin, axisLength, color, 3, 2);
      scene.add(arrow);
    });

    // Add subtle grid
    const gridHelper = new THREE.GridHelper(100, 20, 0x1a1a3a, 0x0a0a1a);
    gridHelper.position.y = -50;
    scene.add(gridHelper);

    // Current embedding point (animated)
    const targetPos = categoryConfigs.find(c => c.name === currentCategory)?.center || [0, 0, 0];
    const sphereGeometry = new THREE.SphereGeometry(4, 32, 32);
    const sphereMaterial = new THREE.MeshBasicMaterial({
      color: new THREE.Color(currentColor),
      transparent: true,
      opacity: 1,
    });
    const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
    sphere.position.set(0, 80, 0);
    scene.add(sphere);

    // Animate landing (slower)
    let progress = 0;
    const startPos = { x: 0, y: 80, z: 0 };

    // Animation loop
    const animate = () => {
      frameIdRef.current = requestAnimationFrame(animate);
      controls.update();

      // Landing animation (slower)
      if (progress < 1) {
        progress += 0.005; // Slower landing
        const eased = 1 - Math.pow(1 - progress, 3);
        sphere.position.x = startPos.x + (targetPos[0] - startPos.x) * eased;
        sphere.position.y = startPos.y + (targetPos[1] - startPos.y) * eased;
        sphere.position.z = startPos.z + (targetPos[2] - startPos.z) * eased;
      } else {
        // Pulse effect
        const pulse = 1 + Math.sin(Date.now() * 0.002) * 0.15;
        sphere.scale.setScalar(pulse);
      }

      composer.render();
    };
    animate();
  }, [currentCategory, currentColor, realKGNodes]);

  // Clean up Three.js
  useEffect(() => {
    return () => {
      if (frameIdRef.current) cancelAnimationFrame(frameIdRef.current);
      if (rendererRef.current && mountRef.current) {
        mountRef.current.removeChild(rendererRef.current.domElement);
        rendererRef.current.dispose();
      }
      sceneRef.current = null;
      livePointsGroupRef.current = null;
    };
  }, []);

  // Initialize Three.js when reaching final stage OR when real KG nodes load
  useEffect(() => {
    if (currentStage === 8) {
      // Determine if we need to (re)initialize
      const needsInit = !sceneRef.current;
      const needsReinit = kgNodesLoaded && !initializedWithRealNodesRef.current && sceneRef.current;

      if (needsInit || needsReinit) {
        // Clean up existing scene first if reinitializing
        if (needsReinit) {
          console.log('Reinitializing scene with real KG nodes');
          if (frameIdRef.current) {
            cancelAnimationFrame(frameIdRef.current);
            frameIdRef.current = null;
          }
          if (rendererRef.current && mountRef.current) {
            try {
              mountRef.current.removeChild(rendererRef.current.domElement);
            } catch {
              // Element might already be removed
            }
            rendererRef.current.dispose();
            rendererRef.current = null;
          }
          sceneRef.current = null;
          livePointsGroupRef.current = null;
        }

        // Mark that we've initialized with real nodes (if available)
        if (kgNodesLoaded) {
          initializedWithRealNodesRef.current = true;
        }

        const timer = setTimeout(() => initThreeScene(), 100);
        return () => clearTimeout(timer);
      }
    } else {
      // Clean up when leaving stage 8
      if (frameIdRef.current) {
        cancelAnimationFrame(frameIdRef.current);
        frameIdRef.current = null;
      }
      if (rendererRef.current && mountRef.current) {
        try {
          mountRef.current.removeChild(rendererRef.current.domElement);
        } catch {
          // Element might already be removed
        }
        rendererRef.current.dispose();
        rendererRef.current = null;
      }
      sceneRef.current = null;
      livePointsGroupRef.current = null;
      // Reset flag when leaving stage so we can reinit if we return
      initializedWithRealNodesRef.current = false;
    }
  }, [currentStage, kgNodesLoaded, initThreeScene]); // Reinitialize when real nodes load

  // Semantic word categories for intelligent positioning
  const getSemanticCategory = (word: string): { center: number[], color: number, name: string } => {
    const w = word.toLowerCase().trim();

    // Philosophy/Free Will terms → Core cluster (gold)
    if (['freedom', 'free', 'liberty', 'choice', 'will', 'agency', 'autonomy', 'self', 'control', 'decision', 'voluntary', 'deliberate', 'intention'].some(t => w.includes(t))) {
      return { center: [0, 0, 0], color: 0xfbbf24, name: 'Core' };
    }
    // Stoic terms → Blue cluster
    if (['fate', 'destiny', 'necessity', 'providence', 'logos', 'nature', 'cosmos', 'stoic', 'chrysippus', 'epictetus', 'marcus', 'seneca', 'determinism'].some(t => w.includes(t))) {
      return { center: [-35, 20, -15], color: 0x60a5fa, name: 'Stoic' };
    }
    // Epicurean terms → Purple cluster
    if (['atom', 'swerve', 'clinamen', 'epicur', 'lucretius', 'pleasure', 'void', 'random', 'chance', 'indeterminate'].some(t => w.includes(t))) {
      return { center: [35, 15, 25], color: 0xc084fc, name: 'Epicurean' };
    }
    // Aristotelian terms → Green cluster
    if (['virtue', 'deliberat', 'practical', 'reason', 'aristotle', 'potentiality', 'actuality', 'teleolog', 'purpose', 'cause', 'ethics'].some(t => w.includes(t))) {
      return { center: [-25, -25, 30], color: 0x4ade80, name: 'Aristotelian' };
    }
    // Platonic terms → Pink cluster
    if (['soul', 'plato', 'form', 'idea', 'justice', 'good', 'beauty', 'truth', 'knowledge', 'dialectic', 'republic'].some(t => w.includes(t))) {
      return { center: [30, -20, -30], color: 0xf472b6, name: 'Platonic' };
    }
    // Default: position based on hash but in a neutral area
    const hash = w.split('').reduce((a, b) => a + b.charCodeAt(0), 0);
    return {
      center: [
        (Math.sin(hash * 0.1) - 0.5) * 40,
        (Math.cos(hash * 0.15) - 0.5) * 40,
        (Math.sin(hash * 0.2) - 0.5) * 40
      ],
      color: 0xffffff,
      name: 'Unknown'
    };
  };

  // Create 3D text sprite for labels
  const createTextSprite = (text: string, color: THREE.Color): THREE.Sprite => {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d')!;
    canvas.width = 256;
    canvas.height = 64;

    // Background
    context.fillStyle = 'rgba(0, 0, 0, 0.7)';
    context.roundRect(0, 0, canvas.width, canvas.height, 8);
    context.fill();

    // Border
    context.strokeStyle = `#${color.getHexString()}`;
    context.lineWidth = 3;
    context.roundRect(2, 2, canvas.width - 4, canvas.height - 4, 6);
    context.stroke();

    // Text
    context.fillStyle = '#ffffff';
    context.font = 'bold 28px monospace';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillText(text.slice(0, 16), canvas.width / 2, canvas.height / 2);

    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      depthTest: false
    });
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(20, 5, 1);

    return sprite;
  };

  // Generate a simulated embedding vector (deterministic based on input)
  const generateSimulatedVector = (text: string, dim: number = 8): number[] => {
    const hash = text.toLowerCase().split('').reduce((a, b, i) => a + b.charCodeAt(0) * (i + 1), 0);
    const vector: number[] = [];
    for (let i = 0; i < dim; i++) {
      vector.push(Math.sin(hash * (i + 1) * 0.1) * Math.cos(hash * 0.05 + i * 0.3));
    }
    // Normalize
    const magnitude = Math.sqrt(vector.reduce((sum, v) => sum + v * v, 0));
    return vector.map(v => v / magnitude);
  };

  // Cluster prototype vectors (what each school "looks like" in embedding space)
  const clusterPrototypes: Record<string, { vector: number[]; color: string; center: number[] }> = {
    'Core': {
      vector: [0.8, 0.2, 0.1, 0.3, 0.5, 0.1, 0.2, 0.4],
      color: '#fbbf24',
      center: [0, 0, 0]
    },
    'Stoic': {
      vector: [0.3, 0.7, 0.5, 0.2, 0.1, 0.6, 0.3, 0.2],
      color: '#60a5fa',
      center: [-35, 20, -15]
    },
    'Epicurean': {
      vector: [0.1, 0.3, 0.8, 0.4, 0.2, 0.1, 0.5, 0.3],
      color: '#c084fc',
      center: [35, 15, 25]
    },
    'Aristotelian': {
      vector: [0.4, 0.1, 0.2, 0.7, 0.6, 0.3, 0.1, 0.5],
      color: '#4ade80',
      center: [-25, -25, 30]
    },
    'Platonic': {
      vector: [0.2, 0.4, 0.3, 0.1, 0.8, 0.5, 0.6, 0.2],
      color: '#f472b6',
      center: [30, -20, -30]
    },
  };

  // Calculate cosine similarity between two vectors
  const cosineSimilarity = (a: number[], b: number[]): number => {
    const dotProduct = a.reduce((sum, val, i) => sum + val * b[i], 0);
    const magnitudeA = Math.sqrt(a.reduce((sum, val) => sum + val * val, 0));
    const magnitudeB = Math.sqrt(b.reduce((sum, val) => sum + val * val, 0));
    return dotProduct / (magnitudeA * magnitudeB);
  };

  // Live embedding demo handler - WITH REAL GEMINI EMBEDDINGS
  const handleLiveEmbed = async () => {
    if (!liveInput.trim() || isEmbedding) return;

    // Ensure scene is ready
    if (!sceneRef.current || !livePointsGroupRef.current) {
      initThreeScene();
      await new Promise(resolve => setTimeout(resolve, 200));
      if (!sceneRef.current || !livePointsGroupRef.current) {
        return;
      }
    }

    setIsEmbedding(true);
    const inputText = liveInput.trim();
    setLiveInput('');

    // STEP 1: Vectorize - Call REAL Gemini API
    setEmbeddingStep('vectorizing');

    let wordVector: number[] = [];
    let position3d = { x: 0, y: 0, z: 0 };
    let cluster = 'Core';
    let clusterColor = '#fbbf24';
    let similarNodes: any[] = [];

    try {
      // Call the real embedding API
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/embeddings/visualize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText }),
      });

      if (response.ok) {
        const apiResponse = await response.json();
        wordVector = apiResponse.embedding; // First 32 dims for display
        position3d = apiResponse.position_3d;
        cluster = apiResponse.cluster;
        clusterColor = apiResponse.cluster_color;
        similarNodes = apiResponse.similar_nodes || [];
      } else {
        // Fallback to simulated if API fails
        wordVector = generateSimulatedVector(inputText);
        const category = getSemanticCategory(inputText);
        position3d = { x: category.center[0], y: category.center[1], z: category.center[2] };
        cluster = category.name;
        clusterColor = `#${category.color.toString(16).padStart(6, '0')}`;
      }
    } catch (error) {
      console.error('Embedding API error, using fallback:', error);
      // Fallback to simulated
      wordVector = generateSimulatedVector(inputText);
      const category = getSemanticCategory(inputText);
      position3d = { x: category.center[0], y: category.center[1], z: category.center[2] };
      cluster = category.name;
      clusterColor = `#${category.color.toString(16).padStart(6, '0')}`;
    }

    setCurrentVector(wordVector);
    await new Promise(resolve => setTimeout(resolve, 1500)); // Let user see vector

    // STEP 2: Compare - Show similarity to real similar nodes
    setEmbeddingStep('comparing');
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Create similarities from real similar nodes or fallback to prototypes
    let sims: { cluster: string; score: number; color: string }[] = [];

    if (similarNodes.length > 0) {
      // Group by school/category and average scores
      const schoolScores: Record<string, { total: number; count: number }> = {};
      for (const node of similarNodes) {
        const school = node.school || 'Core';
        if (!schoolScores[school]) schoolScores[school] = { total: 0, count: 0 };
        schoolScores[school].total += node.score;
        schoolScores[school].count += 1;
      }

      const schoolColors: Record<string, string> = {
        'Stoic': '#60a5fa', 'Stoicism': '#60a5fa',
        'Epicurean': '#c084fc', 'Epicureanism': '#c084fc',
        'Peripatetic': '#4ade80', 'Aristotelian': '#4ade80',
        'Platonic': '#f472b6', 'Platonism': '#f472b6', 'Academic': '#f472b6',
        'Core': '#fbbf24', 'Free Will': '#fbbf24',
      };

      sims = Object.entries(schoolScores).map(([school, data]) => ({
        cluster: school,
        score: data.total / data.count,
        color: schoolColors[school] || '#ffffff',
      })).sort((a, b) => b.score - a.score);
    } else {
      // Fallback to prototype comparison
      sims = Object.entries(clusterPrototypes).map(([name, proto]) => ({
        cluster: name,
        score: cosineSimilarity(wordVector, proto.vector),
        color: proto.color
      })).sort((a, b) => b.score - a.score);
    }

    setSimilarities(sims);
    await new Promise(resolve => setTimeout(resolve, 2500)); // Let user see the scores

    // STEP 3: Place - Use REAL 3D position from API
    setEmbeddingStep('placing');

    // Add some variance to the position for visual spread
    const variance = 8;
    const newPos: [number, number, number] = [
      position3d.x + (Math.random() - 0.5) * variance,
      position3d.y + (Math.random() - 0.5) * variance,
      position3d.z + (Math.random() - 0.5) * variance,
    ];

    const threeColor = new THREE.Color(clusterColor);

    // Add to state
    const newPoint: LiveEmbeddedPoint = {
      text: inputText,
      position: newPos,
      color: clusterColor,
      cluster: cluster
    };

    // Add to Three.js scene with full visualization
    if (sceneRef.current && livePointsGroupRef.current) {
      // 1. Create the main sphere (larger, glowing)
      const sphereGeometry = new THREE.SphereGeometry(4, 32, 32);
      const sphereMaterial = new THREE.MeshBasicMaterial({
        color: threeColor,
        transparent: true,
        opacity: 1,
      });
      const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
      sphere.position.set(0, 80, 0);
      livePointsGroupRef.current.add(sphere);

      // 2. Create outer glow sphere
      const glowGeometry = new THREE.SphereGeometry(6, 32, 32);
      const glowMaterial = new THREE.MeshBasicMaterial({
        color: threeColor,
        transparent: true,
        opacity: 0.3,
      });
      const glow = new THREE.Mesh(glowGeometry, glowMaterial);
      glow.position.copy(sphere.position);
      livePointsGroupRef.current.add(glow);

      // 3. Create text label
      const label = createTextSprite(inputText, threeColor);
      label.position.set(0, 88, 0);
      livePointsGroupRef.current.add(label);

      // 4. Create connection line to cluster center (will animate)
      const lineGeometry = new THREE.BufferGeometry();
      const lineMaterial = new THREE.LineBasicMaterial({
        color: threeColor,
        transparent: true,
        opacity: 0
      });
      const line = new THREE.Line(lineGeometry, lineMaterial);
      livePointsGroupRef.current.add(line);

      // 5. Create particle trail
      const particleCount = 20;
      const particleGeometry = new THREE.BufferGeometry();
      const particlePositions = new Float32Array(particleCount * 3);
      for (let i = 0; i < particleCount; i++) {
        particlePositions[i * 3] = 0;
        particlePositions[i * 3 + 1] = 80;
        particlePositions[i * 3 + 2] = 0;
      }
      particleGeometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
      const particleMaterial = new THREE.PointsMaterial({
        color: threeColor,
        size: 2,
        transparent: true,
        opacity: 0.8,
      });
      const particles = new THREE.Points(particleGeometry, particleMaterial);
      livePointsGroupRef.current.add(particles);

      // Animation
      let animProgress = 0;
      const startY = 80;
      const trailPositions: { x: number; y: number; z: number }[] = [];

      const animatePoint = () => {
        animProgress += 0.008; // Slower animation

        if (animProgress < 1) {
          // Eased progress
          const eased = 1 - Math.pow(1 - animProgress, 3);

          // Current position
          const currentX = newPos[0] * eased;
          const currentY = startY + (newPos[1] - startY) * eased;
          const currentZ = newPos[2] * eased;

          // Update sphere position
          sphere.position.set(currentX, currentY, currentZ);
          glow.position.copy(sphere.position);
          glow.scale.setScalar(1 + Math.sin(animProgress * Math.PI * 4) * 0.2);

          // Update label position (above sphere)
          label.position.set(currentX, currentY + 8, currentZ);

          // Store trail position
          trailPositions.push({ x: currentX, y: currentY, z: currentZ });
          if (trailPositions.length > particleCount) trailPositions.shift();

          // Update particle trail
          const positions = particleGeometry.attributes.position.array as Float32Array;
          trailPositions.forEach((pos, i) => {
            positions[i * 3] = pos.x + (Math.random() - 0.5) * 2;
            positions[i * 3 + 1] = pos.y + (Math.random() - 0.5) * 2;
            positions[i * 3 + 2] = pos.z + (Math.random() - 0.5) * 2;
          });
          particleGeometry.attributes.position.needsUpdate = true;
          particleMaterial.opacity = 0.8 * (1 - animProgress * 0.5);

          requestAnimationFrame(animatePoint);
        } else {
          // Animation complete - finalize
          sphere.position.set(newPos[0], newPos[1], newPos[2]);
          glow.position.copy(sphere.position);
          label.position.set(newPos[0], newPos[1] + 8, newPos[2]);

          // Remove particles
          livePointsGroupRef.current?.remove(particles);
          particleGeometry.dispose();
          particleMaterial.dispose();

          // Show connection line to origin (semantic center)
          const linePoints = [
            new THREE.Vector3(newPos[0], newPos[1], newPos[2]),
            new THREE.Vector3(0, 0, 0) // Connect to semantic origin
          ];
          lineGeometry.setFromPoints(linePoints);
          lineMaterial.opacity = 0.3;

          // Pulse effect on landing
          let pulseProgress = 0;
          const pulseAnimation = () => {
            pulseProgress += 0.02;
            if (pulseProgress < 1) {
              const pulseScale = 1 + Math.sin(pulseProgress * Math.PI) * 0.5;
              glow.scale.setScalar(pulseScale);
              glow.material.opacity = 0.3 * (1 - pulseProgress);
              requestAnimationFrame(pulseAnimation);
            } else {
              // Keep subtle glow
              glow.scale.setScalar(1.2);
              glow.material.opacity = 0.2;
            }
          };
          pulseAnimation();

          // Fade out connection line after a moment
          setTimeout(() => {
            let fadeProgress = 0;
            const fadeAnimation = () => {
              fadeProgress += 0.02;
              if (fadeProgress < 1) {
                lineMaterial.opacity = 0.3 * (1 - fadeProgress);
                requestAnimationFrame(fadeAnimation);
              } else {
                livePointsGroupRef.current?.remove(line);
                lineGeometry.dispose();
                lineMaterial.dispose();
              }
            };
            fadeAnimation();
          }, 2000);
        }
      };
      animatePoint();
    }

    // Add to React state for UI tracking
    setLiveEmbeddedPoints(prev => [...prev, newPoint]);

    // Wait for animation to complete before resetting state
    setTimeout(() => {
      setIsEmbedding(false);
      setEmbeddingStep('idle');
      setCurrentVector(null);
      setSimilarities([]);
    }, 5000); // 5s for the placing animation to complete
  };

  const resetJourney = () => {
    setCurrentStage(0);
    setIsPlaying(false);
    setDisplayedText('');
    setHighlightedTokenIdx(null);
    setPositionHighlight(null);
    setMeaningPhase(0);
    setVocabHighlight(null);
    setLiveEmbeddedPoints([]);

    // Clean up Three.js
    if (frameIdRef.current) cancelAnimationFrame(frameIdRef.current);
    if (rendererRef.current && mountRef.current && rendererRef.current.domElement.parentNode === mountRef.current) {
      mountRef.current.removeChild(rendererRef.current.domElement);
      rendererRef.current.dispose();
    }
    sceneRef.current = null;
    livePointsGroupRef.current = null;
  };

  // Fullscreen toggle using native API
  const toggleFullscreen = async (element: HTMLElement | null) => {
    if (!element) return;

    try {
      if (!document.fullscreenElement) {
        await element.requestFullscreen();
        setIsFullscreen(true);
      } else {
        await document.exitFullscreen();
        setIsFullscreen(false);
      }
    } catch (err) {
      console.error('Fullscreen error:', err);
    }
  };

  // Listen for fullscreen changes and resize Three.js
  useEffect(() => {
    const handleFullscreenChange = () => {
      const isNowFullscreen = !!document.fullscreenElement;
      setIsFullscreen(isNowFullscreen);

      // Resize Three.js renderer after a short delay to let the DOM update
      setTimeout(() => {
        if (mountRef.current && rendererRef.current && cameraRef.current && composerRef.current) {
          const width = mountRef.current.clientWidth;
          const height = mountRef.current.clientHeight;

          cameraRef.current.aspect = width / height;
          cameraRef.current.updateProjectionMatrix();
          rendererRef.current.setSize(width, height);
          composerRef.current.setSize(width, height);
        }
      }, 100);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const nextText = () => {
    setSelectedText(prev => (prev + 1) % DEMO_TEXTS.length);
    resetJourney();
  };

  const prevStage = () => {
    if (currentStage > 0) {
      setCurrentStage(prev => prev - 1);
      setIsPlaying(false);
    }
  };

  const nextStage = () => {
    if (currentStage < STAGES.length - 1) {
      setCurrentStage(prev => prev + 1);
      setIsPlaying(false);
    }
  };

  const StageIcon = STAGES[currentStage].icon;

  return (
    <div
      ref={containerRef}
      className={`relative bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 overflow-hidden border border-white/10 transition-all duration-300 rounded-2xl ${className}`}
    >
      {/* Stage Progress */}
      <div className="absolute top-0 left-0 right-0 z-20 p-4 bg-gradient-to-b from-slate-950/95 to-transparent">
        {/* Progress dots */}
        <div className="flex items-center justify-center gap-1.5 mb-3 flex-wrap">
          {STAGES.map((stage, index) => {
            const Icon = stage.icon;
            return (
              <button
                key={stage.id}
                onClick={() => { setCurrentStage(index); setIsPlaying(false); }}
                className={`relative group transition-all duration-300 ${
                  index === currentStage
                    ? 'scale-110'
                    : 'opacity-50 hover:opacity-80'
                }`}
              >
                <div className={`w-7 h-7 rounded-full flex items-center justify-center transition-all ${
                  index < currentStage
                    ? 'bg-cyan-500/30 border border-cyan-500'
                    : index === currentStage
                      ? 'bg-gradient-to-r from-cyan-500 to-purple-500 border border-white/30'
                      : 'bg-white/10 border border-white/20'
                }`}>
                  <Icon className="w-3.5 h-3.5 text-white" />
                </div>
                {/* Connector line */}
                {index < STAGES.length - 1 && (
                  <div className={`absolute top-1/2 left-full w-1.5 h-0.5 -translate-y-1/2 ${
                    index < currentStage ? 'bg-cyan-500' : 'bg-white/20'
                  }`} />
                )}
                {/* Tooltip */}
                <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity bg-slate-800 px-2 py-1 rounded text-[9px] text-white z-30">
                  {stage.name}
                </div>
              </button>
            );
          })}
        </div>

        {/* Current stage info */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500/30 to-purple-500/30 flex items-center justify-center border border-white/10">
              <StageIcon className="w-4 h-4 text-cyan-400" />
            </div>
            <div>
              <h3 className="text-white font-medium text-sm">
                {currentStage + 1}. {STAGES[currentStage].name}
              </h3>
              <p className="text-white/50 text-xs">{STAGES[currentStage].description}</p>
            </div>
          </div>

          {/* Controls */}
          <div className="flex gap-1">
            <button
              onClick={prevStage}
              disabled={currentStage === 0}
              className="p-2 bg-white/10 rounded-lg text-white/80 hover:bg-white/20 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="p-2 bg-cyan-500/20 rounded-lg text-cyan-400 hover:bg-cyan-500/30 transition-all"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </button>
            <button
              onClick={nextStage}
              disabled={currentStage === STAGES.length - 1}
              className="p-2 bg-white/10 rounded-lg text-white/80 hover:bg-white/20 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
            <button
              onClick={resetJourney}
              className="p-2 bg-white/10 rounded-lg text-white/80 hover:bg-white/20 transition-all ml-2"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            <button
              onClick={() => toggleFullscreen(containerRef.current)}
              className="p-2 bg-purple-500/20 rounded-lg text-purple-400 hover:bg-purple-500/30 transition-all ml-1"
              title={isFullscreen ? 'Exit fullscreen (ESC)' : 'Enter fullscreen'}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Main Visualization Area */}
      <div className="h-[600px] flex items-center justify-center pt-32 pb-16 px-6">
        <AnimatePresence mode="wait">
          {/* Stage 0: Text Input */}
          {currentStage === 0 && (
            <motion.div
              key="input"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="text-center max-w-2xl"
            >
              <div className="mb-6">
                <Type className="w-10 h-10 text-cyan-400 mx-auto mb-3" />
                <span className="text-white/40 text-xs uppercase tracking-widest">Input Text</span>
              </div>

              <div className="relative mb-8">
                <div className="text-3xl md:text-4xl font-serif text-white min-h-[60px] flex items-center justify-center">
                  <span>{displayedText}</span>
                  <span className="animate-pulse text-cyan-400 ml-1">|</span>
                </div>
                <div className="absolute -inset-4 bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-cyan-500/10 rounded-2xl blur-xl -z-10" />
              </div>

              {/* Text selector */}
              <div className="flex justify-center gap-2 flex-wrap">
                {DEMO_TEXTS.map((item, i) => (
                  <button
                    key={i}
                    onClick={() => { setSelectedText(i); resetJourney(); }}
                    className={`px-4 py-2 rounded-xl text-sm transition-all border ${
                      i === selectedText
                        ? 'text-white border-cyan-500/50'
                        : 'bg-white/5 text-white/60 hover:bg-white/10 border-white/10'
                    }`}
                    style={i === selectedText ? { backgroundColor: `${item.color}30` } : {}}
                  >
                    {item.category}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {/* Stage 1: Tokenization */}
          {currentStage === 1 && (
            <motion.div
              key="tokenize"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center max-w-3xl"
            >
              <div className="mb-6">
                <Scissors className="w-8 h-8 text-cyan-400 mx-auto mb-2" />
                <p className="text-white/50 text-sm">BPE (Byte-Pair Encoding) splits text into subword tokens</p>
              </div>

              <div className="flex flex-wrap justify-center gap-3">
                {tokens.map((token, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, scale: 0, rotateY: -90 }}
                    animate={{ opacity: 1, scale: 1, rotateY: 0 }}
                    transition={{ delay: i * 0.6, type: 'spring', stiffness: 150 }}
                    className="relative group"
                  >
                    <div className={`px-4 py-3 rounded-xl border backdrop-blur-sm ${
                      token.isSubword
                        ? 'bg-purple-500/20 border-purple-500/40'
                        : token.text.startsWith('[')
                          ? 'bg-yellow-500/20 border-yellow-500/40'
                          : 'bg-cyan-500/20 border-cyan-500/40'
                    }`}>
                      <span className="text-white font-mono text-lg">{token.text}</span>
                      <div className="text-[10px] text-white/40 mt-1 font-mono">ID: {token.id}</div>
                    </div>

                    {/* Token type indicator */}
                    <div className={`absolute -top-2 -right-2 px-1.5 py-0.5 rounded text-[8px] font-bold ${
                      token.isSubword
                        ? 'bg-purple-500 text-white'
                        : token.text.startsWith('[')
                          ? 'bg-yellow-500 text-black'
                          : 'bg-cyan-500 text-white'
                    }`}>
                      {token.isSubword ? '##' : token.text.startsWith('[') ? 'SPL' : i}
                    </div>
                  </motion.div>
                ))}
              </div>

              <div className="mt-6 text-xs text-white/40">
                <span className="text-cyan-400">Full words</span> •
                <span className="text-purple-400 ml-2">##Subwords</span> •
                <span className="text-yellow-400 ml-2">[Special tokens]</span>
              </div>
            </motion.div>
          )}

          {/* Stage 2: Vocabulary Mapping - NEW! */}
          {currentStage === 2 && (
            <motion.div
              key="vocab"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="w-full max-w-4xl"
            >
              <div className="text-center mb-6">
                <BookOpen className="w-8 h-8 text-cyan-400 mx-auto mb-2" />
                <p className="text-white/50 text-sm">HOW does "what" become 2847? The vocabulary file!</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left: Current token lookup */}
                <div className="bg-slate-900/50 rounded-xl p-4 border border-white/10">
                  <h4 className="text-white font-medium mb-4">Lookup Process</h4>

                  {vocabHighlight !== null && tokens[vocabHighlight] && (
                    <motion.div
                      key={vocabHighlight}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="space-y-4"
                    >
                      <div className="p-4 bg-cyan-500/10 rounded-lg border border-cyan-500/30">
                        <div className="text-xs text-white/50 mb-2">Step 1: Take the token</div>
                        <div className="text-2xl font-mono text-white">"{tokens[vocabHighlight].text}"</div>
                      </div>

                      <div className="flex items-center justify-center">
                        <ArrowRight className="w-6 h-6 text-white/30" />
                      </div>

                      <div className="p-4 bg-purple-500/10 rounded-lg border border-purple-500/30">
                        <div className="text-xs text-white/50 mb-2">Step 2: Search vocab.txt</div>
                        <div className="text-white/60 text-sm">
                          Find which LINE contains "{tokens[vocabHighlight].text}"
                        </div>
                      </div>

                      <div className="flex items-center justify-center">
                        <ArrowRight className="w-6 h-6 text-white/30" />
                      </div>

                      <div className="p-4 bg-green-500/10 rounded-lg border border-green-500/30">
                        <div className="text-xs text-white/50 mb-2">Step 3: Line number = Token ID!</div>
                        <div className="text-3xl font-mono text-green-400 font-bold">
                          {tokens[vocabHighlight].id}
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* Progress */}
                  <div className="flex gap-1 mt-4">
                    {tokens.map((_, i) => (
                      <div
                        key={i}
                        className={`h-1.5 flex-1 rounded transition-all ${
                          i < (vocabHighlight ?? 0)
                            ? 'bg-cyan-500'
                            : i === vocabHighlight
                              ? 'bg-cyan-400 animate-pulse'
                              : 'bg-white/10'
                        }`}
                      />
                    ))}
                  </div>
                </div>

                {/* Right: Vocabulary file visualization */}
                <VocabularyMappingViz tokens={tokens} currentHighlight={vocabHighlight} />
              </div>
            </motion.div>
          )}

          {/* Stage 3: How Meaning Emerges - THE CORE INSIGHT! */}
          {currentStage === 3 && (
            <motion.div
              key="meaning"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="w-full max-w-4xl"
            >
              <div className="text-center mb-6">
                <Lightbulb className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
                <p className="text-white/50 text-sm">The secret to how vectors capture meaning</p>
              </div>

              <MeaningExplainer phase={meaningPhase} />
            </motion.div>
          )}

          {/* Stage 4: Embedding Lookup */}
          {currentStage === 4 && (
            <motion.div
              key="lookup"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="w-full max-w-4xl"
            >
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left: Token being looked up */}
                <div>
                  <div className="mb-4 text-center">
                    <Table2 className="w-8 h-8 text-cyan-400 mx-auto mb-2" />
                    <p className="text-white/50 text-sm">Token ID indexes into matrix row</p>
                  </div>

                  {/* Current token highlight */}
                  <div className="bg-slate-900/50 rounded-xl p-4 border border-white/10">
                    <div className="text-xs text-white/40 mb-2">Current Token:</div>
                    {highlightedTokenIdx !== null && tokens[highlightedTokenIdx] && (
                      <motion.div
                        key={highlightedTokenIdx}
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="flex items-center gap-4"
                      >
                        <div className="px-4 py-2 bg-cyan-500/30 rounded-lg border border-cyan-500/50">
                          <span className="text-white font-mono text-xl">{tokens[highlightedTokenIdx].text}</span>
                        </div>
                        <div className="text-2xl text-white/30">→</div>
                        <div className="text-cyan-400 font-mono text-2xl">
                          [{tokens[highlightedTokenIdx].id}]
                        </div>
                      </motion.div>
                    )}

                    {/* Progress through tokens */}
                    <div className="flex gap-1 mt-4">
                      {tokens.map((_, i) => (
                        <div
                          key={i}
                          className={`h-1.5 flex-1 rounded transition-all ${
                            i < (highlightedTokenIdx ?? 0)
                              ? 'bg-cyan-500'
                              : i === highlightedTokenIdx
                                ? 'bg-cyan-400 animate-pulse'
                                : 'bg-white/10'
                          }`}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Key insight box */}
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                    className="mt-4 p-4 bg-gradient-to-r from-cyan-500/10 to-purple-500/10 rounded-xl border border-cyan-500/20"
                  >
                    <div className="flex items-start gap-3">
                      <Sparkles className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <div className="text-yellow-400 font-medium text-sm mb-1">Key Insight!</div>
                        <p className="text-white/70 text-xs leading-relaxed">
                          Embedding is just a <strong className="text-cyan-400">table lookup</strong>!
                          Each token ID indexes into a matrix of <strong>pre-trained weights</strong>.
                          These weights were LEARNED during training to capture meaning.
                        </p>
                      </div>
                    </div>
                  </motion.div>
                </div>

                {/* Right: Embedding Matrix */}
                <div>
                  <EmbeddingMatrix
                    highlightRow={highlightedTokenIdx !== null ? tokens[highlightedTokenIdx]?.id : null}
                    extractedVector={highlightedTokenIdx !== null ? extractedVectors[highlightedTokenIdx] : null}
                  />
                </div>
              </div>
            </motion.div>
          )}

          {/* Stage 5: Positional Encoding */}
          {currentStage === 5 && (
            <motion.div
              key="position"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="w-full max-w-4xl"
            >
              <div className="text-center mb-6">
                <Waves className="w-8 h-8 text-cyan-400 mx-auto mb-2" />
                <p className="text-white/50 text-sm">Adding position information via sine/cosine functions</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Wave visualization */}
                <PositionalEncodingViz
                  positions={tokens.length}
                  currentPos={positionHighlight}
                />

                {/* Vector addition */}
                <div className="bg-slate-900/50 rounded-xl p-4 border border-white/10">
                  <div className="text-cyan-400 text-xs font-mono mb-3">Token + Position = Final Embedding</div>

                  {positionHighlight !== null && tokens[positionHighlight] && (
                    <motion.div
                      key={positionHighlight}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="space-y-3"
                    >
                      {/* Token embedding */}
                      <div>
                        <div className="text-[10px] text-white/40 mb-1">Token Embedding (from lookup):</div>
                        <div className="flex gap-1 flex-wrap">
                          {extractedVectors[positionHighlight]?.slice(0, 6).map((v, i) => (
                            <span key={i} className="text-[9px] font-mono bg-cyan-500/20 text-cyan-300 px-1.5 py-0.5 rounded">
                              {v.toFixed(2)}
                            </span>
                          ))}
                          <span className="text-white/30 text-[9px]">...</span>
                        </div>
                      </div>

                      {/* Plus sign */}
                      <div className="text-2xl text-white/30 text-center">+</div>

                      {/* Position encoding */}
                      <div>
                        <div className="text-[10px] text-white/40 mb-1">Position Encoding (pos={positionHighlight}):</div>
                        <div className="flex gap-1 flex-wrap">
                          {generatePositionalEncoding(positionHighlight, 6).map((v, i) => (
                            <span key={i} className="text-[9px] font-mono bg-purple-500/20 text-purple-300 px-1.5 py-0.5 rounded">
                              {v.toFixed(2)}
                            </span>
                          ))}
                          <span className="text-white/30 text-[9px]">...</span>
                        </div>
                      </div>

                      {/* Equals sign */}
                      <div className="text-2xl text-white/30 text-center">=</div>

                      {/* Final */}
                      <div>
                        <div className="text-[10px] text-white/40 mb-1">Position-Aware Embedding:</div>
                        <div className="flex gap-1 flex-wrap">
                          {extractedVectors[positionHighlight]?.slice(0, 6).map((v, i) => {
                            const pe = generatePositionalEncoding(positionHighlight, 6)[i];
                            return (
                              <motion.span
                                key={i}
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{ delay: i * 0.08 }}
                                className="text-[9px] font-mono bg-gradient-to-r from-cyan-500/30 to-purple-500/30 text-white px-1.5 py-0.5 rounded"
                              >
                                {(v + pe).toFixed(2)}
                              </motion.span>
                            );
                          })}
                          <span className="text-white/30 text-[9px]">...×768</span>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {/* Stage 6: Self-Attention */}
          {currentStage === 6 && (
            <motion.div
              key="attention"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="w-full max-w-4xl"
            >
              <div className="text-center mb-6">
                <Brain className="w-8 h-8 text-cyan-400 mx-auto mb-2" />
                <p className="text-white/50 text-sm">Query-Key-Value attention mechanism</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
                {/* Q, K, V explanation cards */}
                {[
                  { name: 'Query (Q)', desc: 'What am I looking for?', color: 'cyan' },
                  { name: 'Key (K)', desc: 'What information do I have?', color: 'purple' },
                  { name: 'Value (V)', desc: 'What do I return if matched?', color: 'pink' },
                ].map((item, i) => (
                  <motion.div
                    key={item.name}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.8 }}
                    className={`p-3 rounded-xl bg-${item.color}-500/10 border border-${item.color}-500/30`}
                  >
                    <div className={`text-${item.color}-400 font-mono text-sm mb-1`}>{item.name}</div>
                    <div className="text-white/60 text-xs">{item.desc}</div>
                    <div className="text-white/30 text-[10px] mt-2 font-mono">
                      {item.name[0]} = X × W{item.name[0].toLowerCase()}
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Attention heatmap */}
              <AttentionHeatmap tokens={tokens} weights={attentionWeights} />

              {/* Formula */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 4 }}
                className="mt-4 text-center"
              >
                <div className="inline-block px-4 py-2 bg-slate-900/50 rounded-lg border border-white/10">
                  <span className="text-white/60 text-sm font-mono">
                    Attention(Q, K, V) = softmax(
                    <span className="text-cyan-400">Q</span>
                    <span className="text-purple-400">K</span>
                    <sup>T</sup> / √d<sub>k</sub>)
                    <span className="text-pink-400">V</span>
                  </span>
                </div>
              </motion.div>
            </motion.div>
          )}

          {/* Stage 7: Pooling */}
          {currentStage === 7 && (
            <motion.div
              key="pooling"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="w-full max-w-2xl text-center"
            >
              <div className="mb-6">
                <Layers className="w-8 h-8 text-cyan-400 mx-auto mb-2" />
                <p className="text-white/50 text-sm">Average all token vectors into single embedding</p>
              </div>

              {/* Collapsing animation */}
              <div className="relative h-72 flex items-center justify-center">
                {/* Token vectors */}
                {tokens.map((token, i) => {
                  const angle = (i / tokens.length) * Math.PI * 2 - Math.PI / 2;
                  const radius = 100;

                  return (
                    <motion.div
                      key={i}
                      initial={{
                        x: Math.cos(angle) * radius,
                        y: Math.sin(angle) * radius,
                        opacity: 1,
                        scale: 1,
                      }}
                      animate={{
                        x: 0,
                        y: 0,
                        opacity: 0,
                        scale: 0,
                      }}
                      transition={{
                        delay: i * 0.4,
                        duration: 2.5,
                        ease: 'easeInOut',
                      }}
                      className="absolute w-14 h-14 rounded-full bg-gradient-to-br from-cyan-500/40 to-purple-500/40 flex items-center justify-center border border-white/20"
                    >
                      <span className="text-white text-[9px] font-mono truncate px-1">{token.text}</span>
                    </motion.div>
                  );
                })}

                {/* Final pooled embedding */}
                <motion.div
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: tokens.length * 0.4 + 1, type: 'spring', stiffness: 100 }}
                  className="relative"
                >
                  <div className="w-24 h-24 rounded-full bg-gradient-to-br from-cyan-400 via-purple-400 to-pink-400 flex items-center justify-center shadow-2xl shadow-purple-500/30">
                    <span className="text-white font-bold text-2xl">E</span>
                  </div>
                  <motion.div
                    initial={{ scale: 1, opacity: 0.5 }}
                    animate={{ scale: 2.5, opacity: 0 }}
                    transition={{ repeat: Infinity, duration: 2.5 }}
                    className="absolute inset-0 rounded-full bg-gradient-to-br from-cyan-400 to-purple-400"
                  />
                </motion.div>
              </div>

              {/* Formula */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: tokens.length * 0.4 + 2 }}
                className="mt-4"
              >
                <div className="inline-block px-6 py-3 bg-slate-900/50 rounded-xl border border-white/10">
                  <div className="text-white/60 text-sm font-mono mb-2">
                    E = (1/n) × Σ h<sub>i</sub>
                  </div>
                  <div className="text-white/40 text-xs">
                    Mean of {tokens.length} token vectors → Single 768-D embedding
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}

          {/* Stage 8: Semantic Space */}
          {currentStage === 8 && (
            <motion.div
              key="space"
              ref={semanticSpaceRef}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="w-full h-full relative bg-slate-950"
              style={isFullscreen ? { width: '100vw', height: '100vh' } : undefined}
            >
              <div
                ref={mountRef}
                className="w-full h-full rounded-xl overflow-hidden"
                style={isFullscreen ? { width: '100vw', height: '100vh' } : undefined}
              />

              {/* Semantic Space Fullscreen Button */}
              <button
                onClick={() => toggleFullscreen(semanticSpaceRef.current)}
                className="absolute top-4 right-4 z-30 p-3 bg-slate-900/90 hover:bg-slate-800 border border-cyan-500/50 rounded-lg text-cyan-400 transition-all shadow-lg backdrop-blur-sm group"
                title={isFullscreen ? 'Exit fullscreen (ESC)' : 'Fullscreen semantic space'}
              >
                {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
                <span className="absolute right-full mr-2 top-1/2 -translate-y-1/2 px-2 py-1 bg-slate-800 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                  {isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
                </span>
              </button>

              {/* Live embedding demo */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 2 }}
                className="absolute bottom-28 left-1/2 -translate-x-1/2 w-full max-w-lg px-4"
              >
                <div className="bg-slate-900/95 rounded-xl border border-cyan-500/30 p-4 backdrop-blur-sm">
                  <div className="flex items-center gap-2 mb-3">
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                    <span className="text-cyan-400 text-sm font-medium">Live Embedding Demo</span>
                    <span className="text-white/30 text-xs ml-auto">Type anything!</span>
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={liveInput}
                      onChange={(e) => setLiveInput(e.target.value)}
                      placeholder="Try: freedom, fate, atoms, virtue..."
                      className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-white text-sm placeholder-white/30 focus:outline-none focus:border-cyan-500/50"
                      onKeyDown={(e) => e.key === 'Enter' && handleLiveEmbed()}
                    />
                    <button
                      onClick={handleLiveEmbed}
                      disabled={isEmbedding || !liveInput.trim()}
                      className="px-5 py-2.5 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/50 rounded-lg text-cyan-400 text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {isEmbedding ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                      Embed
                    </button>
                  </div>

                  {/* Cosine Similarity Visualization - Shows the math! */}
                  <AnimatePresence>
                    {embeddingStep !== 'idle' && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-4 overflow-hidden"
                      >
                        <div className="bg-slate-800/80 rounded-lg border border-amber-500/30 p-4">
                          {/* Step indicator */}
                          <div className="flex items-center gap-3 mb-3">
                            <div className="flex gap-1">
                              {['vectorizing', 'comparing', 'placing'].map((step, i) => (
                                <div
                                  key={step}
                                  className={`w-2 h-2 rounded-full transition-all ${
                                    embeddingStep === step
                                      ? 'bg-amber-400 scale-125'
                                      : i < ['vectorizing', 'comparing', 'placing'].indexOf(embeddingStep)
                                        ? 'bg-amber-400/50'
                                        : 'bg-white/20'
                                  }`}
                                />
                              ))}
                            </div>
                            <span className="text-amber-400 text-xs font-medium">
                              {embeddingStep === 'vectorizing' && '1. Generating Vector...'}
                              {embeddingStep === 'comparing' && '2. Computing Cosine Similarities...'}
                              {embeddingStep === 'placing' && '3. Placing in Semantic Space...'}
                            </span>
                          </div>

                          {/* Vector display */}
                          {embeddingStep === 'vectorizing' && currentVector && (
                            <motion.div
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              className="space-y-2"
                            >
                              <div className="text-white/50 text-xs">Embedding vector (8-dim preview):</div>
                              <div className="font-mono text-xs flex flex-wrap gap-1">
                                {currentVector.map((v, i) => (
                                  <motion.span
                                    key={i}
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.08 }}
                                    className="px-1.5 py-0.5 bg-cyan-500/20 rounded text-cyan-400"
                                  >
                                    {v.toFixed(3)}
                                  </motion.span>
                                ))}
                              </div>
                              <div className="text-white/30 text-xs mt-2">
                                <span className="text-amber-400/70">‖v‖ = </span>
                                {Math.sqrt(currentVector.reduce((sum, v) => sum + v * v, 0)).toFixed(4)}
                                <span className="text-white/20 ml-2">(normalized)</span>
                              </div>
                            </motion.div>
                          )}

                          {/* Cosine similarity scores */}
                          {embeddingStep === 'comparing' && similarities.length > 0 && (
                            <motion.div
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              className="space-y-2"
                            >
                              <div className="text-white/50 text-xs mb-2">
                                cos(θ) = <span className="text-amber-400">(a · b)</span> / <span className="text-cyan-400">(‖a‖ × ‖b‖)</span>
                              </div>
                              <div className="space-y-1.5">
                                {similarities.map((sim, i) => (
                                  <motion.div
                                    key={sim.cluster}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: i * 0.15 }}
                                    className="flex items-center gap-2"
                                  >
                                    <div
                                      className="w-3 h-3 rounded-full"
                                      style={{ backgroundColor: sim.color }}
                                    />
                                    <span className="text-white/70 text-xs w-24">{sim.cluster}</span>
                                    <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                                      <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${sim.score * 100}%` }}
                                        transition={{ delay: i * 0.15, duration: 0.5 }}
                                        className="h-full rounded-full"
                                        style={{ backgroundColor: sim.color }}
                                      />
                                    </div>
                                    <span
                                      className={`text-xs font-mono w-14 text-right ${
                                        i === 0 ? 'text-green-400 font-bold' : 'text-white/50'
                                      }`}
                                    >
                                      {(sim.score * 100).toFixed(1)}%
                                    </span>
                                    {i === 0 && (
                                      <span className="text-green-400 text-xs">✓ Best</span>
                                    )}
                                  </motion.div>
                                ))}
                              </div>
                            </motion.div>
                          )}

                          {/* Placing animation */}
                          {embeddingStep === 'placing' && similarities.length > 0 && (
                            <motion.div
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              className="flex items-center gap-2"
                            >
                              <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
                              <span className="text-white/70 text-sm">
                                Placing in <span style={{ color: similarities[0].color }} className="font-medium">{similarities[0].cluster}</span> cluster
                              </span>
                              <span className="text-white/30 text-xs ml-auto">
                                similarity: {(similarities[0].score * 100).toFixed(1)}%
                              </span>
                            </motion.div>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Show embedded points with cluster info */}
                  {liveEmbeddedPoints.length > 0 && (
                    <div className="mt-3 space-y-2">
                      <div className="text-white/40 text-xs">Embedded words:</div>
                      <div className="flex flex-wrap gap-2">
                        {liveEmbeddedPoints.map((point, i) => (
                          <motion.div
                            key={i}
                            initial={{ opacity: 0, scale: 0 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="flex items-center gap-1.5 px-2 py-1 rounded text-xs font-mono"
                            style={{
                              backgroundColor: `${point.color}20`,
                              border: `1px solid ${point.color}50`
                            }}
                          >
                            <span style={{ color: point.color }}>{point.text}</span>
                            <span className="text-white/30">→</span>
                            <span className="text-white/50">{point.cluster}</span>
                          </motion.div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>

              {/* Current embedding info */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 2.5 }}
                className="absolute bottom-4 left-1/2 -translate-x-1/2"
              >
                <div className="px-4 py-2 bg-slate-900/80 rounded-lg border border-cyan-500/30 backdrop-blur-sm">
                  <span className="text-cyan-400 font-medium">"{currentText}"</span>
                  <span className="text-white/50 text-sm ml-2">→ {currentCategory} cluster</span>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Bottom Info */}
      <div className="absolute bottom-4 left-4 right-4 flex justify-between items-center text-xs text-white/30">
        <span>Gemini text-embedding-004 • 768 dimensions (Matryoshka)</span>
        <button
          onClick={nextText}
          className="flex items-center gap-1 text-white/50 hover:text-white/80 transition-all"
        >
          Try different text <ChevronRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}
