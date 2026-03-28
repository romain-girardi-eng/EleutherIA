import { ChevronLeft, ChevronRight, Minus, Plus, Columns2, AlignJustify } from 'lucide-react';
import type { FontSizePreset } from './types';
import { FONT_SIZE_MAP } from './types';

interface BookControlsProps {
  currentPage: number;
  totalPages: number;
  onPrevious: () => void;
  onNext: () => void;
  onGoToPage: (page: number) => void;
  fontSize: FontSizePreset;
  onFontSizeChange: (size: FontSizePreset) => void;
  isBilingual: boolean;
  hasBilingual: boolean;
  onToggleBilingual: () => void;
  isPaginated: boolean;
  onToggleMode: () => void;
}

const FONT_ORDER: FontSizePreset[] = ['small', 'normal', 'large'];

export function BookControls({
  currentPage,
  totalPages,
  onPrevious,
  onNext,
  fontSize,
  onFontSizeChange,
  isBilingual,
  hasBilingual,
  onToggleBilingual,
  onToggleMode,
}: BookControlsProps) {
  const fontIdx = FONT_ORDER.indexOf(fontSize);

  const increaseFontSize = () => {
    if (fontIdx < FONT_ORDER.length - 1) onFontSizeChange(FONT_ORDER[fontIdx + 1]);
  };

  const decreaseFontSize = () => {
    if (fontIdx > 0) onFontSizeChange(FONT_ORDER[fontIdx - 1]);
  };

  return (
    <div className="flex items-center justify-center gap-6 py-4">
      <button
        onClick={onPrevious}
        disabled={currentPage <= 1}
        className="w-9 h-9 rounded-full border border-amber-200/40 flex items-center justify-center text-stone-600 hover:border-amber-600/60 hover:text-stone-800 transition disabled:opacity-20 disabled:cursor-not-allowed"
      >
        <ChevronLeft size={16} />
      </button>

      <span className="font-garamond text-sm text-stone-500 tracking-[1px] tabular-nums">
        {currentPage}–{Math.min(currentPage + 1, totalPages)} sur {totalPages}
      </span>

      <button
        onClick={onNext}
        disabled={currentPage >= totalPages}
        className="w-9 h-9 rounded-full border border-amber-200/40 flex items-center justify-center text-stone-600 hover:border-amber-600/60 hover:text-stone-800 transition disabled:opacity-20 disabled:cursor-not-allowed"
      >
        <ChevronRight size={16} />
      </button>

      <div className="w-px h-5 bg-amber-200/40" />

      {/* Font size +/- */}
      <div className="flex items-center gap-1">
        <button
          onClick={decreaseFontSize}
          disabled={fontIdx <= 0}
          className="w-7 h-7 rounded flex items-center justify-center text-stone-500 hover:text-stone-800 hover:bg-amber-100/40 transition disabled:opacity-20 disabled:cursor-not-allowed"
          title={`Réduire (${FONT_SIZE_MAP[fontSize]}px)`}
        >
          <Minus size={13} />
        </button>
        <span className="text-[10px] text-stone-400 min-w-[28px] text-center tabular-nums">
          {FONT_SIZE_MAP[fontSize]}
        </span>
        <button
          onClick={increaseFontSize}
          disabled={fontIdx >= FONT_ORDER.length - 1}
          className="w-7 h-7 rounded flex items-center justify-center text-stone-500 hover:text-stone-800 hover:bg-amber-100/40 transition disabled:opacity-20 disabled:cursor-not-allowed"
          title={`Agrandir (${FONT_SIZE_MAP[fontSize]}px)`}
        >
          <Plus size={13} />
        </button>
      </div>

      {hasBilingual && (
        <button
          onClick={onToggleBilingual}
          className={`flex items-center gap-1.5 text-xs transition ${isBilingual ? 'text-amber-700' : 'text-stone-500 hover:text-stone-800'}`}
          title={isBilingual ? 'Mode monolingue' : 'Mode bilingue'}
        >
          <Columns2 size={14} />
        </button>
      )}

      <button
        onClick={onToggleMode}
        className="flex items-center gap-1.5 text-xs text-stone-500 hover:text-stone-800 transition"
        title="Mode scroll"
      >
        <AlignJustify size={14} />
      </button>
    </div>
  );
}
