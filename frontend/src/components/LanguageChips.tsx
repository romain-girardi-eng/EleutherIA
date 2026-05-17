/**
 * LanguageChips — compact row of flag chips for switching the UI locale.
 *
 * Replaces the older Globe-dropdown for in-navbar use. Always-visible
 * buttons make the affordance obvious and shave a tap off the
 * "set my language" interaction. Two sizes:
 *   - `compact` (navbar): flag + 2-letter code, tight padding
 *   - `large`   (mobile menu): flag + native name, comfortable touch
 */

import { useTranslation } from 'react-i18next';
import { Check } from 'lucide-react';
import { languages } from '../i18n/config';
import { cn } from '../lib/utils';

interface LanguageChipsProps {
  size?: 'compact' | 'large';
  /** Render label as dark on light surface; default chooses by size. */
  inverted?: boolean;
  className?: string;
}

const SIZE_CLASSES = {
  compact:
    'h-9 min-w-9 px-2 text-[12px] font-medium gap-1 rounded-full',
  large:
    'h-12 min-w-12 px-3 text-sm font-medium gap-2 rounded-xl flex-1',
} as const;

export function LanguageChips({
  size = 'compact',
  inverted = false,
  className = '',
}: LanguageChipsProps) {
  const { i18n, t } = useTranslation();

  const changeLanguage = (langCode: string) => {
    if (langCode === i18n.language) return;
    void i18n.changeLanguage(langCode);
    const lang = languages.find((l) => l.code === langCode);
    const region = document.getElementById('aria-live-announcer');
    if (lang && region) {
      region.textContent = t('common.languageChangedTo', { language: lang.name });
    }
  };

  return (
    <div
      role="radiogroup"
      aria-label={t('common.selectLanguage')}
      className={cn(
        'flex items-center gap-1',
        size === 'large' && 'gap-2 w-full',
        className,
      )}
    >
      {languages.map((lang) => {
        const active = i18n.language === lang.code;
        return (
          <button
            key={lang.code}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={t('common.switchToLanguage', { language: lang.name })}
            onClick={() => changeLanguage(lang.code)}
            className={cn(
              'inline-flex items-center justify-center select-none transition-all active:scale-95',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/60',
              SIZE_CLASSES[size],
              active
                ? cn(
                    'bg-amber-50 text-amber-900 ring-1 ring-amber-400/80 shadow-sm',
                    inverted && 'bg-amber-200/20 text-amber-100 ring-amber-200/70',
                  )
                : cn(
                    'bg-white/60 text-stone-600 ring-1 ring-stone-200/70 hover:bg-amber-50/60 hover:text-amber-800',
                    inverted &&
                      'bg-white/10 text-white/80 ring-white/20 hover:bg-white/15 hover:text-white',
                  ),
            )}
          >
            <span className="text-base leading-none" aria-hidden="true">
              {lang.flag}
            </span>
            <span className="uppercase tracking-wide leading-none">
              {size === 'compact' ? lang.code : lang.nativeName}
            </span>
            {active && size === 'large' && (
              <Check className="ml-auto h-4 w-4 text-amber-700" aria-hidden="true" />
            )}
          </button>
        );
      })}
    </div>
  );
}

export default LanguageChips;
