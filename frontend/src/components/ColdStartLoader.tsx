import { useEffect, useState } from 'react';
import { Server, Clock, Coffee } from 'lucide-react';

interface ColdStartLoaderProps {
  isLoading: boolean;
  message?: string;
  showAfterMs?: number; // Only show if loading takes longer than this
}

/**
 * Cold Start Loader Component
 *
 * Shows a friendly, informative message when the backend is waking up from sleep.
 * Designed for Render free tier which sleeps after 15 minutes of inactivity.
 *
 * Features:
 * - Only shows after 3 seconds (avoids flashing for fast requests)
 * - Progress animation to keep user informed
 * - Educational about free tier limitations
 * - Friendly, non-technical language
 */
export const ColdStartLoader = ({
  isLoading,
  message = 'Connecting to server',
  showAfterMs = 3000
}: ColdStartLoaderProps) => {
  const [showLoader, setShowLoader] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (!isLoading) {
      setShowLoader(false);
      setElapsedSeconds(0);
      return;
    }

    // Only show loader if request takes longer than threshold
    const showTimer = setTimeout(() => {
      setShowLoader(true);
    }, showAfterMs);

    // Track elapsed time for progress messages
    const secondsTimer = setInterval(() => {
      setElapsedSeconds(prev => prev + 1);
    }, 1000);

    return () => {
      clearTimeout(showTimer);
      clearInterval(secondsTimer);
    };
  }, [isLoading, showAfterMs]);

  if (!isLoading || !showLoader) {
    return null;
  }

  // Progressive messages based on elapsed time
  const getProgressMessage = () => {
    if (elapsedSeconds < 10) {
      return 'Waking up the server...';
    } else if (elapsedSeconds < 30) {
      return 'Still waking up (free tier cold start)...';
    } else if (elapsedSeconds < 60) {
      return 'Almost there! Free tier servers take 30-60 seconds to wake...';
    } else {
      return 'This is taking longer than expected. The server may be experiencing high load.';
    }
  };

  return (
    <div className="flex items-center justify-center py-12">
      <div className="max-w-md w-full bg-white border-2 border-blue-200 rounded-lg shadow-lg p-6 space-y-4">
        {/* Animated Icon */}
        <div className="flex justify-center">
          <div className="relative">
            <Server className="w-16 h-16 text-blue-600 animate-pulse" />
            <div className="absolute -top-1 -right-1">
              <Coffee className="w-6 h-6 text-amber-600 animate-bounce" />
            </div>
          </div>
        </div>

        {/* Title */}
        <h3 className="text-lg font-semibold text-center text-gray-900">
          {message}
        </h3>

        {/* Progress Message */}
        <p className="text-sm text-center text-gray-600">
          {getProgressMessage()}
        </p>

        {/* Elapsed Time */}
        <div className="flex items-center justify-center space-x-2 text-xs text-gray-500">
          <Clock className="w-4 h-4" />
          <span>{elapsedSeconds}s elapsed</span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-500 to-blue-600 h-full rounded-full transition-all duration-1000 ease-out"
            style={{
              width: `${Math.min((elapsedSeconds / 60) * 100, 95)}%`
            }}
          />
        </div>

        {/* Explanation */}
        <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
          <p className="text-xs text-gray-700 leading-relaxed">
            <strong>Why is this happening?</strong> The backend runs on Render's free tier,
            which puts inactive servers to sleep after 15 minutes. The first request wakes it up,
            taking 30-60 seconds. Subsequent requests will be fast!
          </p>
        </div>

        {/* Tips for long waits */}
        {elapsedSeconds > 45 && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
            <p className="text-xs text-amber-900 leading-relaxed">
              <strong>Still waiting?</strong> You can try:
            </p>
            <ul className="text-xs text-amber-800 mt-2 space-y-1 ml-4 list-disc">
              <li>Refreshing the page</li>
              <li>Checking your internet connection</li>
              <li>Waiting a bit longer (it usually works!)</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Minimal Cold Start Loader
 *
 * Simpler version for inline loading states
 */
export const ColdStartLoaderMinimal = ({ isLoading }: { isLoading: boolean }) => {
  const [showMessage, setShowMessage] = useState(false);

  useEffect(() => {
    if (!isLoading) {
      setShowMessage(false);
      return;
    }

    const timer = setTimeout(() => {
      setShowMessage(true);
    }, 3000);

    return () => clearTimeout(timer);
  }, [isLoading]);

  if (!isLoading) return null;

  return (
    <div className="flex flex-col items-center justify-center py-6">
      <div className="spinner w-12 h-12 mb-3"></div>
      {showMessage && (
        <div className="text-center space-y-2 max-w-md px-4">
          <p className="text-sm text-gray-700 font-medium">
            Waking up the server...
          </p>
          <p className="text-xs text-gray-500">
            Free tier cold start (30-60 seconds)
          </p>
        </div>
      )}
    </div>
  );
};
