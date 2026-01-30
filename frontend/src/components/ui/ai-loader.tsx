import { cn } from "@/lib/utils";

interface AILoaderProps {
  /** Text to display (each letter will be animated) */
  text?: string;
  /** Size variant */
  size?: "sm" | "md" | "lg";
  /** Whether to show as fullscreen overlay */
  fullscreen?: boolean;
  /** Additional CSS classes for wrapper */
  className?: string;
}

/**
 * AI Loader Component - Ultrathink Edition
 *
 * Modern AI-themed loader with animated letters and gradient spinning circle
 *
 * @example
 * <AILoader text="Generating" />
 * <AILoader text="Thinking" fullscreen />
 * <AILoader text="Searching" size="lg" />
 */
export function AILoader({
  text = "Generating",
  size = "md",
  fullscreen = false,
  className
}: AILoaderProps) {
  const letters = text.split("");

  // Size configurations
  const sizeClasses = {
    sm: {
      text: "text-sm",
      loader: "w-12 h-12",
      spacing: "gap-0.5"
    },
    md: {
      text: "text-base",
      loader: "w-20 h-20",
      spacing: "gap-1"
    },
    lg: {
      text: "text-lg",
      loader: "w-28 h-28",
      spacing: "gap-1.5"
    }
  };

  const currentSize = sizeClasses[size];

  const loaderContent = (
    <div className={cn(
      "loader-wrapper relative inline-block",
      currentSize.loader,
      className
    )}>
      {/* Absolutely centered text */}
      <div className="absolute inset-0 flex items-center justify-center z-10">
        <div className={cn(
          "flex items-center",
          currentSize.spacing
        )}>
          {letters.map((letter, index) => (
            <span
              key={index}
              className={cn(
                "loader-letter inline-block font-medium text-white",
                currentSize.text
              )}
              style={{
                animationDelay: `${index * 0.1}s`
              }}
            >
              {letter}
            </span>
          ))}
        </div>
      </div>

      {/* Rotating circle */}
      <div className={cn(
        "loader w-full h-full rounded-full",
        currentSize.loader
      )}></div>
    </div>
  );

  if (fullscreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-b from-slate-900 via-slate-800 to-black">
        {loaderContent}
      </div>
    );
  }

  return loaderContent;
}

/**
 * AI Loader Inline - For inline loading states
 */
export function AILoaderInline({
  text = "Loading",
  className
}: {
  text?: string;
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center justify-center", className)}>
      <AILoader text={text} size="sm" />
    </span>
  );
}

/**
 * Page Loader - For full page loading states
 */
export function PageLoader({
  text = "Loading",
  message
}: {
  text?: string;
  message?: string;
}) {
  return (
    <div className="min-h-[400px] flex flex-col items-center justify-center gap-4">
      <AILoader text={text} size="lg" />
      {message && (
        <p className="text-sm text-gray-600 animate-pulse">{message}</p>
      )}
    </div>
  );
}

// Export as Component for compatibility
export const Component = AILoader;
