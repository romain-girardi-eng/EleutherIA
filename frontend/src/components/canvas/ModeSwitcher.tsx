import { useMemo } from 'react';
import { Network, Orbit, Box } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export default function ModeSwitcher() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const modes = useMemo(() => [
    {
      id: 'observatory' as const,
      path: '/visualizer',
      icon: Network,
      label: t('graphUi.modeSwitcher.observatory.label'),
      description: t('graphUi.modeSwitcher.observatory.description'),
    },
    {
      id: 'cosmos' as const,
      path: '/cosmos',
      icon: Orbit,
      label: t('graphUi.modeSwitcher.cosmos.label'),
      description: t('graphUi.modeSwitcher.cosmos.description'),
    },
    {
      id: 'semativerse' as const,
      path: '/semativerse',
      icon: Box,
      label: t('graphUi.modeSwitcher.semativerse.label'),
      description: t('graphUi.modeSwitcher.semativerse.description'),
    },
  ], [t]);

  // Determine active mode from current pathname
  const currentPath = location.pathname;
  const activeMode = currentPath.startsWith('/semativerse')
    ? 'semativerse'
    : currentPath.startsWith('/cosmos')
      ? 'cosmos'
      : 'observatory';

  return (
    <div className="flex gap-1 p-1 bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-xl" role="radiogroup" aria-label={t('graphUi.modeSwitcher.ariaLabel')}>
      {modes.map((m) => {
        const Icon = m.icon;
        const isActive = activeMode === m.id;

        return (
          <button
            key={m.id}
            onClick={() => navigate(m.path)}
            className={`relative group flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${
              isActive
                ? 'bg-violet-500/40 text-white'
                : 'text-white/50 hover:text-white hover:bg-white/10'
            }`}
            title={m.description}
            role="radio"
            aria-checked={isActive}
            aria-label={`${m.label}: ${m.description}`}
          >
            <Icon className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{m.label}</span>

            {/* Tooltip */}
            <div className="absolute right-0 top-full mt-2 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-200 z-50">
              <div className="bg-slate-900/95 backdrop-blur-xl text-white text-[10px] rounded-lg py-1.5 px-2.5 whitespace-nowrap shadow-lg border border-white/10">
                {m.description}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
