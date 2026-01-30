import * as React from "react";
import { AILoader } from "./ai-loader";

interface InlineLoaderProps {
  size?: number;
  text?: string;
  theme?: 'chat' | 'search';
  className?: string;
}

/**
 * @deprecated Use AILoaderInline from './ai-loader' instead
 * This component is kept for backward compatibility
 */
export const InlineAILoader: React.FC<InlineLoaderProps> = ({
  text = "Generating",
  className = ''
}) => {
  return (
    <div className={className}>
      <AILoader text={text} size="sm" />
    </div>
  );
};

// Export the new version as well for migration
export { AILoaderInline, AILoader, PageLoader } from "./ai-loader";
