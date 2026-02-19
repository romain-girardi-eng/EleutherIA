import { cn } from '../../utils/cn';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  /** 'dark' = white-on-dark glass, 'light' = black-on-light glass, 'parchment' = warm cream glass */
  variant?: 'dark' | 'light' | 'parchment';
  padding?: 'sm' | 'md' | 'lg' | 'xl';
  hover?: boolean;
}

const variantStyles = {
  dark: 'bg-white/8 border-white/15 text-white backdrop-blur-md',
  light: 'bg-black/4 border-stone-200/80 text-stone-800 backdrop-blur-sm',
  parchment: 'bg-parchment-100/70 border-parchment-300/60 text-stone-800 backdrop-blur-sm',
};

const paddingStyles = {
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
  xl: 'p-10',
};

export function GlassCard({
  children,
  className,
  variant = 'dark',
  padding = 'lg',
  hover = false,
}: GlassCardProps) {
  return (
    <div
      className={cn(
        'rounded-2xl border',
        variantStyles[variant],
        paddingStyles[padding],
        hover && 'transition-all duration-300 hover:scale-[1.02] hover:shadow-xl cursor-pointer',
        className,
      )}
    >
      {children}
    </div>
  );
}
