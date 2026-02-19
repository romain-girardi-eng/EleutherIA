import { cn } from '../../utils/cn';

interface BackgroundMeshProps {
  variant?: 'dots' | 'grid' | 'crosses';
  color?: string;
  className?: string;
  opacity?: number;
}

export function BackgroundMesh({
  variant = 'dots',
  color = 'currentColor',
  className,
  opacity = 0.06,
}: BackgroundMeshProps) {
  const patterns = {
    dots: `radial-gradient(circle, ${color} 1px, transparent 1px)`,
    grid: `linear-gradient(to right, ${color} 1px, transparent 1px), linear-gradient(to bottom, ${color} 1px, transparent 1px)`,
    crosses: `
      linear-gradient(to right, ${color} 1px, transparent 1px),
      linear-gradient(to bottom, ${color} 1px, transparent 1px)
    `,
  };

  const sizes = {
    dots: '24px 24px',
    grid: '40px 40px',
    crosses: '40px 40px',
  };

  return (
    <div
      aria-hidden="true"
      className={cn('absolute inset-0 pointer-events-none', className)}
      style={{
        backgroundImage: patterns[variant],
        backgroundSize: sizes[variant],
        opacity,
      }}
    />
  );
}
