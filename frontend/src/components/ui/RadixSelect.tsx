import * as Select from '@radix-ui/react-select';
import { ChevronDown, Check } from 'lucide-react';
import { cn } from '../../utils/cn';

interface RadixSelectProps {
  value: string;
  onValueChange: (value: string) => void;
  options: { value: string; label: string }[];
  label?: string;
  placeholder?: string;
  className?: string;
}

export function RadixSelect({ value, onValueChange, options, label, placeholder, className }: RadixSelectProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      {label && <span className="text-xs font-medium text-stone-500">{label}</span>}
      <Select.Root value={value} onValueChange={onValueChange}>
        <Select.Trigger
          className={cn(
            'inline-flex items-center justify-between gap-1.5 rounded-lg border border-stone-200 bg-white/80 px-3 py-1.5 text-xs text-stone-700',
            'hover:border-stone-300 focus:outline-none focus:ring-2 focus:ring-stone-400 focus:ring-offset-1',
            'transition-colors min-w-[60px]',
          )}
        >
          <Select.Value placeholder={placeholder} />
          <Select.Icon>
            <ChevronDown className="h-3 w-3 text-stone-400" />
          </Select.Icon>
        </Select.Trigger>

        <Select.Portal>
          <Select.Content
            className="z-50 overflow-hidden rounded-lg border border-stone-200 bg-white shadow-lg animate-in fade-in-0 zoom-in-95"
            position="popper"
            sideOffset={4}
          >
            <Select.Viewport className="p-1">
              {options.map((opt) => (
                <Select.Item
                  key={opt.value}
                  value={opt.value}
                  className={cn(
                    'relative flex items-center rounded-md px-3 py-1.5 text-xs text-stone-700 outline-none cursor-pointer',
                    'hover:bg-stone-100 hover:text-stone-800 focus:bg-stone-100 focus:text-stone-800',
                    'data-[state=checked]:font-medium',
                  )}
                >
                  <Select.ItemText>{opt.label}</Select.ItemText>
                  <Select.ItemIndicator className="ml-auto">
                    <Check className="h-3 w-3" />
                  </Select.ItemIndicator>
                </Select.Item>
              ))}
            </Select.Viewport>
          </Select.Content>
        </Select.Portal>
      </Select.Root>
    </div>
  );
}
