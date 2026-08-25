import { useTranslation } from 'react-i18next';
import * as Select from '@radix-ui/react-select';
import { Bot, Check, ChevronDown, Square } from 'lucide-react';
import { ShineBorder } from '../../components/ui/shine-border';
import { ScholarlyWaitExpectation } from './WaitingExperience';

export interface GraphRagModelOption {
  key: string;
  label: string;
  provider: string;
  available?: boolean;
}

interface ModelSelectorProps {
  selectedModel: string;
  modelOptions: GraphRagModelOption[];
  onModelChange: (model: string) => void;
  className?: string;
}

export function ModelSelector({
  selectedModel,
  modelOptions = [],
  onModelChange,
  className = '',
}: ModelSelectorProps) {
  const { t } = useTranslation();

  return (
    <div className={`flex items-center justify-between gap-3 px-1 ${className}`}>
      <Select.Root value={selectedModel} onValueChange={onModelChange}>
        <Select.Trigger
          aria-label={t('graphRagUi.modelSelector.ariaLabel')}
          className="group inline-flex min-h-8 items-center gap-1.5 rounded-full border border-amber-200/80 bg-white/70 px-2.5 py-1 text-[11px] font-medium text-stone-600 shadow-[0_1px_0_rgba(120,53,15,0.04)] transition-colors hover:border-amber-300 hover:bg-amber-50/70 focus:outline-none focus:ring-2 focus:ring-amber-300/60"
        >
          <Bot className="h-3.5 w-3.5 text-amber-700" aria-hidden="true" />
          <span className="text-stone-400">
            {t('graphRagUi.modelSelector.label')}:
          </span>
          <Select.Value />
          <Select.Icon>
            <ChevronDown
              className="h-3 w-3 text-stone-400 transition-transform group-data-[state=open]:rotate-180"
              aria-hidden="true"
            />
          </Select.Icon>
        </Select.Trigger>

        <Select.Portal>
          <Select.Content
            position="popper"
            side="top"
            align="start"
            sideOffset={8}
            className="z-[80] min-w-[17rem] overflow-hidden rounded-xl border border-amber-200/80 bg-[#fdfaf3] p-1.5 shadow-[0_18px_50px_rgba(68,45,22,0.18)]"
          >
            <Select.Viewport>
              <Select.Item
                value="auto"
                className="relative flex cursor-default select-none items-start gap-2 rounded-lg py-2 pl-8 pr-3 text-stone-700 outline-none data-[highlighted]:bg-amber-100/70"
              >
                <Select.ItemIndicator className="absolute left-2.5 top-2.5 text-amber-700">
                  <Check className="h-3.5 w-3.5" aria-hidden="true" />
                </Select.ItemIndicator>
                <div>
                  <Select.ItemText>
                    {t('graphRagUi.modelSelector.auto')}
                  </Select.ItemText>
                  <p className="mt-0.5 text-[10px] font-normal text-stone-400">
                    {t('graphRagUi.modelSelector.autoDescription')}
                  </p>
                </div>
              </Select.Item>

              <Select.Separator className="my-1 h-px bg-amber-200/60" />

              {modelOptions
                .filter((option) => option.available !== false)
                .map((option) => (
                  <Select.Item
                    key={option.key}
                    value={option.key}
                    className="relative flex cursor-default select-none items-start gap-2 rounded-lg py-2 pl-8 pr-3 text-stone-700 outline-none data-[highlighted]:bg-amber-100/70"
                  >
                    <Select.ItemIndicator className="absolute left-2.5 top-2.5 text-amber-700">
                      <Check className="h-3.5 w-3.5" aria-hidden="true" />
                    </Select.ItemIndicator>
                    <div className="min-w-0">
                      <Select.ItemText>{option.label}</Select.ItemText>
                      <p className="mt-0.5 text-[10px] font-normal capitalize text-stone-400">
                        {option.provider} · {t('graphRagUi.modelSelector.exclusive')}
                      </p>
                    </div>
                  </Select.Item>
                ))}
            </Select.Viewport>
          </Select.Content>
        </Select.Portal>
      </Select.Root>

      <p className="hidden text-[10px] text-stone-400 sm:block">
        {t('graphRagUi.modelSelector.nextRequest')}
      </p>
    </div>
  );
}

interface ChatInputProps {
  query: string;
  setQuery: (q: string) => void;
  /** True while the ACTIVE run streams — Stop only ever stops that one. */
  streaming: boolean;
  /** False once the concurrent-run cap is reached. */
  canSubmit: boolean;
  maxConcurrentRuns: number;
  inputRef: React.RefObject<HTMLInputElement | null>;
  onSubmit: (e: React.FormEvent) => void;
  onStop: () => void;
  selectedModel?: string;
  modelOptions?: GraphRagModelOption[];
  onModelChange?: (model: string) => void;
}

export default function ChatInput({
  query,
  setQuery,
  streaming,
  canSubmit,
  maxConcurrentRuns,
  inputRef,
  onSubmit,
  onStop,
  selectedModel = 'auto',
  modelOptions = [],
  onModelChange = () => undefined,
}: ChatInputProps) {
  const { t } = useTranslation();

  return (
    <div className="shrink-0 px-4 xl:px-10 2xl:px-16 py-3 xl:py-4 border-t border-amber-200/40 bg-parchment-50/80 backdrop-blur-sm">
      <ShineBorder
        className="!p-0 bg-white/95 backdrop-blur-sm shadow-sm"
        borderRadius={9999}
        color={['#fdba74', '#f97316', '#fbbf24']}
      >
        <form onSubmit={onSubmit} className="p-2">
          <div className="flex gap-2">
            {/* The ask box stays live during a stream: a new question opens a
                new run instead of waiting for the current one. */}
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t('graphrag.placeholder')}
              className="flex-1 min-w-0 px-4 sm:px-6 py-3 xl:py-4 text-base xl:text-base 2xl:text-lg bg-transparent focus:outline-none focus:ring-0 border-0"
            />
            {streaming && (
              <button
                type="button"
                onClick={onStop}
                aria-label={t('graphRagUi.runs.stopAria')}
                className="flex items-center gap-1.5 px-4 sm:px-5 py-3 xl:py-4 min-h-[44px] bg-red-600 text-white rounded-full hover:bg-red-700 font-medium transition-all text-sm xl:text-base"
              >
                <Square className="w-3 h-3 xl:w-4 xl:h-4 fill-current" />
                {t('graphRagUi.runs.stop')}
              </button>
            )}
            <button
              type="submit"
              disabled={!canSubmit || !query.trim()}
              aria-label={t('graphrag.ask')}
              className="px-4 sm:px-6 py-3 xl:py-4 min-h-[44px] bg-gradient-to-br from-orange-600 to-orange-500 text-white rounded-full hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium text-sm xl:text-base"
            >
              {t('graphrag.ask')}
            </button>
          </div>
        </form>
      </ShineBorder>
      <ModelSelector
        className="mt-2"
        selectedModel={selectedModel}
        modelOptions={modelOptions}
        onModelChange={onModelChange}
      />
      <ScholarlyWaitExpectation className="mt-2" />
      {!canSubmit && (
        <p className="mt-2 px-2 text-xs text-amber-800" data-testid="run-cap-hint">
          {t('graphRagUi.runs.capReached', { max: maxConcurrentRuns })}
        </p>
      )}
    </div>
  );
}
