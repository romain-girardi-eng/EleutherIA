/**
 * BottomTabNav Component
 * Mobile-only bottom navigation for mode switching
 * Part of EleutherIA mobile UI redesign - Week 1 Foundation
 */

import { Network, Sparkles } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export default function BottomTabNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();

  // Determine active mode from current pathname
  const currentPath = location.pathname;
  const isObservatory = currentPath.startsWith('/visualizer');
  const isSemativerse = currentPath.startsWith('/semativerse');

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 md:hidden z-50 pb-safe"
      role="navigation"
      aria-label={t('bottomNav.ariaLabel')}
    >
      <div className="flex items-center justify-around h-16 max-w-screen-xl mx-auto px-safe">
        <TabButton
          active={isObservatory}
          onClick={() => navigate('/visualizer')}
          icon={<Network className="w-6 h-6" aria-hidden="true" />}
          label={t('bottomNav.observatory')}
          ariaLabel={t('bottomNav.observatoryAria')}
        />
        <TabButton
          active={isSemativerse}
          onClick={() => navigate('/semativerse')}
          icon={<Sparkles className="w-6 h-6" aria-hidden="true" />}
          label={t('bottomNav.semativerse')}
          ariaLabel={t('bottomNav.semativerseAria')}
        />
      </div>
    </nav>
  );
}

interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  ariaLabel: string;
}

function TabButton({ active, onClick, icon, label, ariaLabel }: TabButtonProps) {
  const activeClasses = active ? 'text-primary-600 font-semibold' : 'text-gray-400 hover:text-gray-600';

  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center justify-center min-w-[80px] h-full px-2 transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 active:scale-95 ${activeClasses}`}
      aria-label={ariaLabel}
      aria-current={active ? 'page' : undefined}
      type="button"
    >
      <div className="mb-1">
        {icon}
      </div>
      <span className="text-xs font-medium leading-tight">
        {label}
      </span>
    </button>
  );
}
