import * as Tooltip from '@radix-ui/react-tooltip';
import { cn } from '../../utils/cn';

interface RadixTooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  side?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
  delayDuration?: number;
}

export function RadixTooltip({ content, children, side = 'top', className, delayDuration = 300 }: RadixTooltipProps) {
  return (
    <Tooltip.Provider delayDuration={delayDuration}>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>{children}</Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            side={side}
            sideOffset={6}
            className={cn(
              'z-50 rounded-lg bg-gray-900 px-3 py-2 text-xs text-white shadow-xl',
              'animate-in fade-in-0 zoom-in-95',
              'max-w-xs leading-relaxed',
              className,
            )}
          >
            {content}
            <Tooltip.Arrow className="fill-gray-900" width={10} height={5} />
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}
