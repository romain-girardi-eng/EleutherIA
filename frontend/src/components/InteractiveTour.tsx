import { useEffect, useState } from 'react';
import { TourGuideClient } from '@sjmc11/tourguidejs';

interface TourStep {
  title: string;
  content: string;
  target: string;
}

interface InteractiveTourProps {
  autoStart?: boolean;
  onComplete?: () => void;
  tourSteps?: TourStep[];
}

export default function InteractiveTour({ autoStart = false, onComplete, tourSteps }: InteractiveTourProps) {
  // Default tour steps if none provided
  const defaultTourSteps: TourStep[] = [
    {
      title: 'Welcome to EleutherIA',
      content: 'A comprehensive knowledge graph documenting ancient debates on free will from Aristotle to Boethius. Let us guide you through the key features.',
      target: 'body'
    }
  ];

  const steps = tourSteps || defaultTourSteps;
  const [tourInstance, setTourInstance] = useState<TourGuideClient | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Initialize tour with elegant, sober styling
    const tg = new TourGuideClient({
      exitOnClickOutside: false,
      showStepDots: true,
      showStepProgress: true,
      dialogAnimate: true,
      dialogZ: 9999,
      dialogWidth: 380,
      dialogClass: 'eleutheriate-tour-dialog',
      backdropColor: 'rgba(28, 25, 23, 0.6)',
      steps: steps.map((step, index) => ({
        title: step.title,
        content: step.content,
        target: step.target,
        order: index + 1
      }))
    });

    // Wait for elements to be available
    setTimeout(() => {
      setTourInstance(tg);
      setIsReady(true);
    }, 500);

    return () => {
      if (tg) {
        tg.finishTour();
      }
    };
  }, [steps]);

  useEffect(() => {
    if (isReady && tourInstance && autoStart) {
      // Always start the tour when requested (user clicked the button)
      tourInstance.start();

      // Check for tour completion
      const checkCompletion = setInterval(() => {
        const dialog = document.querySelector('.eleutheriate-tour-dialog');
        if (!dialog) {
          localStorage.setItem('eleutheriate_tour_completed', 'true');
          onComplete?.();
          clearInterval(checkCompletion);
        }
      }, 500);

      // Cleanup interval on unmount
      return () => clearInterval(checkCompletion);
    }
  }, [isReady, tourInstance, autoStart, onComplete]);

  const startTour = () => {
    if (tourInstance) {
      tourInstance.start();
    }
  };

  const exitTour = () => {
    if (tourInstance) {
      tourInstance.finishTour();
      onComplete?.();
    }
  };

  // Add keyboard shortcut to exit tour (ESC key)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && tourInstance) {
        tourInstance.finishTour();
        onComplete?.();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [tourInstance, onComplete]);

  return (
    <>
      {/* Exit Tour Button - Always visible during tour */}
      <button
        onClick={exitTour}
        className="fixed top-20 right-6 z-[10000] bg-white hover:bg-gray-100 text-gray-700 rounded-full p-2 shadow-lg transition-all hover:scale-110 active:scale-95 border border-gray-200"
        title="Exit Tour (ESC)"
        aria-label="Exit Tour"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      {/* Elegant CSS styles for the tour */}
      <style>{`
        /* Main tour dialog styling */
        .eleutheriate-tour-dialog {
          font-family: 'Crimson Text', Georgia, serif;
          background: linear-gradient(to bottom right, #fdfcfb, #f8f7f6);
          border: 1px solid #d6d3d0;
          border-radius: 12px;
          box-shadow:
            0 10px 25px rgba(28, 25, 23, 0.15),
            0 4px 10px rgba(28, 25, 23, 0.1);
          animation: tourDialogFadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
          max-width: calc(100vw - 2rem);
        }

        @keyframes tourDialogFadeIn {
          from {
            opacity: 0;
            transform: translateY(-8px) scale(0.98);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        /* Tour title styling */
        .tg-dialog-title {
          font-size: 1.375rem;
          font-weight: 700;
          color: #769687;
          margin-bottom: 0.75rem;
          letter-spacing: -0.02em;
          line-height: 1.3;
        }

        /* Tour content styling */
        .tg-dialog-body {
          font-size: 0.9375rem;
          color: #44403c;
          line-height: 1.7;
          margin-bottom: 1.5rem;
        }

        /* Button container */
        .tg-dialog-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 0.75rem;
          padding-top: 1rem;
          border-top: 1px solid #e7e5e3;
        }

        /* Step progress styling */
        .tg-step-progress {
          font-size: 0.75rem;
          color: #78716c;
          font-weight: 500;
          letter-spacing: 0.02em;
        }

        /* Step dots */
        .tg-step-dots {
          display: flex;
          gap: 0.375rem;
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid #e7e5e3;
        }

        .tg-step-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #d6d3d0;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .tg-step-dot.active {
          width: 20px;
          border-radius: 3px;
          background: #769687;
        }

        /* Button styling */
        .tg-dialog-btn {
          padding: 0.5rem 1.25rem;
          font-size: 0.875rem;
          font-weight: 500;
          border-radius: 6px;
          border: none;
          cursor: pointer;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
          font-family: system-ui, -apple-system, sans-serif;
          letter-spacing: 0.01em;
        }

        .tg-dialog-btn-primary {
          background: linear-gradient(135deg, #769687 0%, #648577 100%);
          color: white;
          box-shadow: 0 2px 4px rgba(118, 150, 135, 0.2);
        }

        .tg-dialog-btn-primary:hover {
          background: linear-gradient(135deg, #648577 0%, #536e5f 100%);
          box-shadow: 0 4px 8px rgba(118, 150, 135, 0.3);
          transform: translateY(-1px);
        }

        .tg-dialog-btn-primary:active {
          transform: translateY(0);
          box-shadow: 0 1px 2px rgba(118, 150, 135, 0.2);
        }

        .tg-dialog-btn-secondary {
          background: transparent;
          color: #57534e;
          border: 1px solid #d6d3d0;
        }

        .tg-dialog-btn-secondary:hover {
          background: #f5f5f4;
          border-color: #a8a29e;
        }

        .tg-dialog-btn-close {
          background: transparent;
          color: #78716c;
          border: none;
          padding: 0.375rem;
        }

        .tg-dialog-btn-close:hover {
          color: #44403c;
          background: #f5f5f4;
        }

        /* Backdrop animation */
        .tg-backdrop {
          animation: backdropFadeIn 0.3s ease-out;
        }

        @keyframes backdropFadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        /* Target highlight pulse */
        .tg-target-highlight {
          animation: targetPulse 2s ease-in-out infinite;
          border-radius: 8px;
        }

        @keyframes targetPulse {
          0%, 100% {
            box-shadow: 0 0 0 0 rgba(118, 150, 135, 0.4);
          }
          50% {
            box-shadow: 0 0 0 8px rgba(118, 150, 135, 0);
          }
        }

        /* Responsive adjustments */
        @media (max-width: 640px) {
          .eleutheriate-tour-dialog {
            border-radius: 10px;
          }

          .tg-dialog-title {
            font-size: 1.125rem;
          }

          .tg-dialog-body {
            font-size: 0.875rem;
          }

          .tg-dialog-btn {
            padding: 0.45rem 1rem;
            font-size: 0.8125rem;
          }
        }

        /* Dark mode support (optional) */
        @media (prefers-color-scheme: dark) {
          .eleutheriate-tour-dialog {
            background: linear-gradient(to bottom right, #2c2925, #231f1c);
            border-color: #44403c;
          }

          .tg-dialog-title {
            color: #9cb3a8;
          }

          .tg-dialog-body {
            color: #d6d3d0;
          }

          .tg-step-progress {
            color: #a8a29e;
          }

          .tg-step-dot {
            background: #57534e;
          }

          .tg-step-dot.active {
            background: #9cb3a8;
          }

          .tg-dialog-btn-secondary {
            border-color: #57534e;
            color: #d6d3d0;
          }

          .tg-dialog-btn-secondary:hover {
            background: #44403c;
            border-color: #78716c;
          }

          .tg-dialog-footer {
            border-top-color: #44403c;
          }

          .tg-step-dots {
            border-top-color: #44403c;
          }
        }
      `}</style>

      {/* Hidden tour trigger button - can be activated from parent */}
      <button
        onClick={startTour}
        className="hidden"
        data-tour-trigger="true"
        aria-label="Start interactive tour"
      />
    </>
  );
}

// Export a hook to start the tour from anywhere
export function useTour() {
  const startTour = () => {
    const trigger = document.querySelector('[data-tour-trigger="true"]') as HTMLButtonElement;
    if (trigger) {
      trigger.click();
    }
  };

  return { startTour };
}
