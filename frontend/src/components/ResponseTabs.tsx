export interface ResponseTab {
  id: string;
  label: string;
  threadId: string;
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
    <div className="flex items-center gap-1 border-b border-zinc-800 px-2">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`px-3 py-1.5 text-xs rounded-t transition-colors ${
            tab.id === activeTabId
              ? 'bg-zinc-800 text-zinc-100 border-b-2 border-blue-500'
              : 'text-zinc-500 hover:text-zinc-300'
          }`}
        >
          {tab.label}
        </button>
      ))}
      <button
        onClick={onRetry}
        className="ml-auto px-2 py-1 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
        title="Retry with a different model"
      >
        + Retry with...
      </button>
    </div>
  );
}
