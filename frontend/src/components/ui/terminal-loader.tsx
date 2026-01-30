import { useState, useEffect } from 'react';

// Ancient philosophy-themed loading messages - witty and scholarly
const LOADING_MESSAGES = [
  // Stoic philosophy
  "Consulting the Stoics on fate...",
  "Debating with Chrysippus...",
  "Checking if this is up to us...",
  "Calculating causal chains...",
  "Asking Epictetus for patience...",
  "Reviewing Stoic physics...",
  "Navigating the Lazy Argument...",
  "Assessing assent mechanisms...",
  "Mapping the hegemonikon...",
  "Wrestling with heimarmenē...",
  "Distinguishing fate from necessity...",
  "Applying the cylinder analogy...",
  "Consulting Marcus Aurelius...",
  "Aligning with cosmic reason...",

  // Aristotelian philosophy
  "Traversing Aristotle's categories...",
  "Examining voluntary actions...",
  "Weighing deliberate choice...",
  "Probing prohairesis...",
  "Analyzing the Nicomachean Ethics...",
  "Distinguishing the voluntary...",
  "Calculating the mean...",
  "Seeking the unmoved mover...",
  "Applying practical wisdom...",

  // Platonic philosophy
  "Parsing Plato's dialogues...",
  "Ascending from the cave...",
  "Contemplating the Forms...",
  "Recollecting eternal truths...",
  "Questioning with Socrates...",
  "Dividing the soul...",
  "Steering the chariot...",

  // Epicurean philosophy
  "Swerving atoms randomly...",
  "Calculating the clinamen...",
  "Seeking ataraxia...",
  "Avoiding unnecessary desires...",
  "Tending the Garden...",

  // General ancient philosophy
  "Unrolling ancient scrolls...",
  "Translating Greek diacritics...",
  "Following Zeno's paradoxes...",
  "Seeking Socratic wisdom...",
  "Measuring modal contingency...",
  "Questioning the gods' role...",
  "Analyzing Alexander's De Fato...",
  "Tracing chains of causation...",
  "Invoking Cicero's counsel...",
  "Interpreting oracular responses...",
  "Pondering providential design...",
  "Unlocking ancient minds...",
  "Decoding papyrus fragments...",
  "Cross-referencing the doxographers...",
  "Consulting the Stoicorum Veterum...",
  "Mining Diogenes Laertius...",

  // Witty/clever ones - fate & determinism
  "Determining if we chose this query...",
  "Freely willing a response...",
  "Deliberating on your behalf...",
  "Exercising rational agency...",
  "This was fated to take a moment...",
  "The gods are considering...",
  "Necessity permits no shortcuts...",
  "Your query was predetermined...",
  "Causally necessitating an answer...",
  "Compatibly processing...",
  "Soft-determining the response...",
  "Libertarianly free-loading...",
  "Hard-determinedly computing...",
  "Neither fate nor chance...",
  "Morally responsible for this delay...",
  "Blaming no one but the API...",
  "The Fates are spinning threads...",
  "Apollo is being consulted...",
  "Delphi is processing your query...",
  "The oracle speaks slowly...",
  "Even Hermes needs a moment...",
  "Zeus is reviewing the request...",
  "Athena approves of this question...",

  // More witty fate/determinism jokes
  "Could you have asked anything else?",
  "Klotho is measuring the response...",
  "Lachesis is weaving your answer...",
  "Atropos will cut when ready...",
  "The cosmic web is tangled here...",
  "Fate allows no faster results...",
  "The causal nexus is computing...",
  "Your assent made this happen...",
  "Blame Chrysippus, not the devs...",
  "Even the Stoics had to wait...",
  "Necessity is a stern teacher...",
  "Providence unfolds in due time...",
  "The eternal return includes this...",
  "Antecedent causes are cascading...",
  "The principle causes are at work...",
  "Not fate, just a slow API...",
  "The gods roll dice slowly...",
  "Tyche is feeling capricious...",
  "Fortuna's wheel is turning...",
  "Ananke demands patience...",
  "Moira is still deliberating...",
  "The Pythia is warming up...",
  "Consulting the Book of Fate...",
  "The thread of destiny is long...",
  "Zeus nodded, but slowly...",
  "The cosmic logos is processing...",
  "Your query was always going to wait...",
  "Nothing happens without a cause...",
  "The sufficient reason is loading...",
  "Leibniz would understand...",
  "The best possible answer is coming...",
  "Contingency is being evaluated...",
  "The modal status is unclear...",
  "Possible worlds are being searched...",
  "Alternative timelines considered...",
  "The multiverse is being queried...",
  "Determinism doesn't mean fast...",
  "Free will does not imply speed...",
  "Compatibilism accepts this delay...",
  "The agent intellect is pondering...",
  "Unmoved movers are never rushed...",
  "The rational soul deliberates...",
  "Akrasia is not an option here...",
];

interface TerminalLoaderProps {
  className?: string;
  /** Size variant: 'default' (288px), 'large' (480px), 'xl' (600px) */
  size?: 'default' | 'large' | 'xl';
  /** Optional title override */
  title?: string;
}

const SIZE_CLASSES = {
  default: {
    container: 'w-72 p-6 pt-4',
    header: 'h-6 px-2',
    headerTitle: 'text-sm leading-6',
    controlsGap: 'gap-2',
    controlSize: 'w-2.5 h-2.5',
    content: 'text-base mt-6 min-h-[1.5rem]',
    progress: 'mt-3 gap-2',
    dotSize: 'w-2 h-2',
    dotsGap: 'gap-1',
    progressText: 'text-xs',
  },
  large: {
    container: 'w-[480px] p-10 pt-6',
    header: 'h-10 px-4',
    headerTitle: 'text-lg leading-10 font-medium',
    controlsGap: 'gap-3',
    controlSize: 'w-4 h-4',
    content: 'text-xl mt-10 min-h-[2rem]',
    progress: 'mt-6 gap-3',
    dotSize: 'w-3 h-3',
    dotsGap: 'gap-2',
    progressText: 'text-sm',
  },
  xl: {
    container: 'w-[600px] p-12 pt-8',
    header: 'h-12 px-5',
    headerTitle: 'text-xl leading-[3rem] font-semibold',
    controlsGap: 'gap-4',
    controlSize: 'w-5 h-5',
    content: 'text-2xl mt-12 min-h-[2.5rem]',
    progress: 'mt-8 gap-4',
    dotSize: 'w-4 h-4',
    dotsGap: 'gap-2',
    progressText: 'text-base',
  },
};

export function TerminalLoader({ className = "", size = 'default', title = 'GraphRAG Engine' }: TerminalLoaderProps) {
  const [messageIndex, setMessageIndex] = useState(0);
  const s = SIZE_CLASSES[size];

  useEffect(() => {
    // Cycle through messages every 3 seconds
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 3000);

    // Randomize initial message
    setMessageIndex(Math.floor(Math.random() * LOADING_MESSAGES.length));

    return () => clearInterval(interval);
  }, []);

  return (
    <div className={`terminal-loader relative bg-gray-900 border border-gray-600 font-mono shadow-2xl rounded-xl border-opacity-80 overflow-hidden ${s.container} ${className}`}>
      {/* Terminal header */}
      <div className={`terminal-header absolute top-0 left-0 right-0 bg-gray-700 rounded-t flex items-center justify-between ${s.header}`}>
        <div className={`terminal-title text-gray-200 ${s.headerTitle}`}>
          {title}
        </div>
        <div className={`terminal-controls flex ${s.controlsGap}`}>
          <div className={`control close rounded-full bg-red-500 animate-pulse ${s.controlSize}`}></div>
          <div className={`control minimize rounded-full bg-yellow-400 ${s.controlSize}`}></div>
          <div className={`control maximize rounded-full bg-green-500 ${s.controlSize}`}></div>
        </div>
      </div>

      {/* Terminal content */}
      <div className={`text text-green-400 ${s.content}`}>
        <span className="terminal-text animate-typewriter">
          {LOADING_MESSAGES[messageIndex]}
        </span>
        <span className="cursor animate-blink">|</span>
      </div>

      {/* Progress indicator */}
      <div className={`flex items-center ${s.progress}`}>
        <div className={`flex ${s.dotsGap}`}>
          <span className={`bg-green-400 rounded-full animate-bounce ${s.dotSize}`} style={{ animationDelay: '0ms' }}></span>
          <span className={`bg-green-400 rounded-full animate-bounce ${s.dotSize}`} style={{ animationDelay: '150ms' }}></span>
          <span className={`bg-green-400 rounded-full animate-bounce ${s.dotSize}`} style={{ animationDelay: '300ms' }}></span>
        </div>
        <span className={`text-gray-500 ${s.progressText}`}>Processing query</span>
      </div>
    </div>
  );
}

export default TerminalLoader;
