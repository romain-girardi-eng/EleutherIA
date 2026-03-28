import { ChevronLeft, ChevronRight, Minus, Plus, Columns2, AlignJustify } from 'lucide-react';
import { FONT_SIZE_MIN, FONT_SIZE_MAX, FONT_SIZE_STEP } from './types';

interface BookControlsProps {
  currentPage: number;
  totalPages: number;
  onPrevious: () => void;
  onNext: () => void;
  onGoToPage: (page: number) => void;
  fontSize: number;
  onFontSizeChange: (size: number) => void;
  isBilingual: boolean;
  hasBilingual: boolean;
  onToggleBilingual: () => void;
  onToggleMode: () => void;
}

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

      {/* Font size — continuous +/- */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => onFontSizeChange(Math.max(FONT_SIZE_MIN, fontSize - FONT_SIZE_STEP))}
          disabled={fontSize <= FONT_SIZE_MIN}
          className="w-7 h-7 rounded flex items-center justify-center text-stone-500 hover:text-stone-800 hover:bg-amber-100/40 transition disabled:opacity-20 disabled:cursor-not-allowed"
          title="Réduire la police"
        >
          <Minus size={13} />
        </button>
        <span className="text-[10px] text-stone-400 min-w-[28px] text-center tabular-nums">
          {fontSize}
        </span>
        <button
          onClick={() => onFontSizeChange(Math.min(FONT_SIZE_MAX, fontSize + FONT_SIZE_STEP))}
          disabled={fontSize >= FONT_SIZE_MAX}
          className="w-7 h-7 rounded flex items-center justify-center text-stone-500 hover:text-stone-800 hover:bg-amber-100/40 transition disabled:opacity-20 disabled:cursor-not-allowed"
          title="Agrandir la police"
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
