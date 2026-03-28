import { ChevronLeft, ChevronRight, Type, Columns2, AlignJustify } from 'lucide-react';
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

const FONT_PRESETS: FontSizePreset[] = ['small', 'normal', 'large'];

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
  const nextFontSize = () => {
    const idx = FONT_PRESETS.indexOf(fontSize);
    onFontSizeChange(FONT_PRESETS[(idx + 1) % FONT_PRESETS.length]);
  };

  return (
    <div className="flex items-center justify-center gap-8 mb-12">
      <button
        onClick={onPrevious}
        disabled={currentPage <= 1}
        className="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center text-white/80 hover:border-amber-600/40 hover:text-amber-600 transition disabled:opacity-20 disabled:cursor-not-allowed"
      >
        <ChevronLeft size={18} />
      </button>

      <span className="font-garamond text-sm opacity-50 tracking-[1px] tabular-nums">
        {currentPage}–{Math.min(currentPage + 1, totalPages)} sur {totalPages}
      </span>

      <button
        onClick={onNext}
        disabled={currentPage >= totalPages}
        className="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center text-white/80 hover:border-amber-600/40 hover:text-amber-600 transition disabled:opacity-20 disabled:cursor-not-allowed"
      >
        <ChevronRight size={18} />
      </button>

      <div className="w-px h-6 bg-white/10" />

      <button
        onClick={nextFontSize}
        className="flex items-center gap-1.5 text-xs opacity-50 hover:opacity-80 transition"
        title={`Taille : ${FONT_SIZE_MAP[fontSize]}px`}
      >
        <Type size={14} />
        <span className="uppercase tracking-wider">{fontSize === 'small' ? 'P' : fontSize === 'normal' ? 'M' : 'G'}</span>
      </button>

      {hasBilingual && (
        <button
          onClick={onToggleBilingual}
          className={`flex items-center gap-1.5 text-xs transition ${isBilingual ? 'text-amber-600 opacity-80' : 'opacity-50 hover:opacity-80'}`}
          title={isBilingual ? 'Mode monolingue' : 'Mode bilingue'}
        >
          <Columns2 size={14} />
        </button>
      )}

      <button
        onClick={onToggleMode}
        className="flex items-center gap-1.5 text-xs opacity-50 hover:opacity-80 transition"
        title="Mode scroll"
      >
        <AlignJustify size={14} />
      </button>
    </div>
  );
}
