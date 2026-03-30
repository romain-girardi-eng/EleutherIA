import { RefreshCw } from 'lucide-react';

export interface ResponseTab {
  id: string;
  label: string;
  model: string;
  mode: string;
}

interface ResponseTabsProps {
  tabs: ResponseTab[];
  activeTabId: string;
  onTabChange: (tabId: string) => void;
  onRetry: () => void;
}

export function ResponseTabs({
  tabs,
  activeTabId,
  onTabChange,
  onRetry,
}: ResponseTabsProps) {
  if (tabs.length <= 1) return null;

  return (
    <div className="flex items-center gap-1 border-b border-amber-200/40 px-2 bg-parchment-50/60">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`px-3 py-1.5 text-xs rounded-t transition-colors ${
            tab.id === activeTabId
              ? 'bg-white text-stone-800 border-b-2 border-amber-500 font-semibold'
              : 'text-stone-500 hover:text-stone-700'
          }`}
        >
          {tab.label}
        </button>
      ))}
      <button
        onClick={onRetry}
        className="ml-auto flex items-center gap-1 px-2 py-1 text-xs text-stone-500 hover:text-stone-700 transition-colors"
        title="Retry with a different model"
      >
        <RefreshCw className="w-3 h-3" />
        Retry with...
      </button>
    </div>
  );
}
