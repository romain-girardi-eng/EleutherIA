import { cn } from '../../utils/cn';

interface AuroraStripProps {
  className?: string;
  /** 'top' | 'bottom' — which edge to attach to */
  position?: 'top' | 'bottom';
  /** Colour palette: warm (orange/amber) | cool (blue/violet) */
  palette?: 'warm' | 'cool';
  height?: string;
}

export function AuroraStrip({
  className,
  position = 'bottom',
  palette = 'warm',
  height = '200px',
}: AuroraStripProps) {
  const gradients = {
    warm: 'from-orange-500/0 via-amber-400/20 via-orange-600/30 to-parchment-100/0',
    cool: 'from-blue-500/0 via-indigo-400/20 via-violet-600/30 to-blue-100/0',
  };

  return (
    <div
      aria-hidden="true"
      className={cn(
        'absolute left-0 right-0 pointer-events-none overflow-hidden',
        position === 'bottom' ? 'bottom-0' : 'top-0',
        className,
      )}
      style={{ height }}
    >
      {/* Blurred aurora blobs */}
      <div
        className={cn(
          'absolute inset-0 bg-gradient-to-r',
          gradients[palette],
          'blur-3xl opacity-60',
        )}
      />
      {/* Hard fade to transparent */}
      <div
        className={cn(
          'absolute inset-0 bg-gradient-to-t',
          position === 'bottom'
            ? 'from-transparent to-transparent'
            : 'from-transparent to-transparent',
        )}
      />
    </div>
  );
}
