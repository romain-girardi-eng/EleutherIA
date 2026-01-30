import { AILoader, AILoaderInline, PageLoader } from "./ai-loader";

/**
 * AI Loader Demo - Ultrathink Edition
 *
 * Showcase different variations of the AI Loader component
 */
export default function AILoaderDemo() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-black p-8">
      <div className="max-w-6xl mx-auto space-y-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">
            AI Loader - Ultrathink Edition
          </h1>
          <p className="text-gray-400 text-lg">
            Modern AI-themed loader with animated letters and gradient effects
          </p>
        </div>

        {/* Size Variants */}
        <section className="bg-slate-800/50 rounded-lg p-8 backdrop-blur-sm">
          <h2 className="text-2xl font-semibold text-white mb-6">Size Variants</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="flex flex-col items-center gap-4">
              <h3 className="text-gray-300 text-sm font-medium">Small</h3>
              <div className="bg-slate-900/50 p-8 rounded-lg">
                <AILoader text="Thinking" size="sm" />
              </div>
            </div>
            <div className="flex flex-col items-center gap-4">
              <h3 className="text-gray-300 text-sm font-medium">Medium (Default)</h3>
              <div className="bg-slate-900/50 p-8 rounded-lg">
                <AILoader text="Generating" size="md" />
              </div>
            </div>
            <div className="flex flex-col items-center gap-4">
              <h3 className="text-gray-300 text-sm font-medium">Large</h3>
              <div className="bg-slate-900/50 p-8 rounded-lg">
                <AILoader text="Processing" size="lg" />
              </div>
            </div>
          </div>
        </section>

        {/* Text Variants */}
        <section className="bg-slate-800/50 rounded-lg p-8 backdrop-blur-sm">
          <h2 className="text-2xl font-semibold text-white mb-6">Text Variants</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="flex flex-col items-center gap-4">
              <div className="bg-slate-900/50 p-8 rounded-lg">
                <AILoader text="Searching" />
              </div>
            </div>
            <div className="flex flex-col items-center gap-4">
              <div className="bg-slate-900/50 p-8 rounded-lg">
                <AILoader text="Analyzing" />
              </div>
            </div>
            <div className="flex flex-col items-center gap-4">
              <div className="bg-slate-900/50 p-8 rounded-lg">
                <AILoader text="Ultrathink" />
              </div>
            </div>
          </div>
        </section>

        {/* Inline Variant */}
        <section className="bg-slate-800/50 rounded-lg p-8 backdrop-blur-sm">
          <h2 className="text-2xl font-semibold text-white mb-6">Inline Usage</h2>
          <div className="bg-slate-900/50 p-8 rounded-lg">
            <p className="text-gray-300 flex items-center gap-3">
              Please wait while we process your request
              <AILoaderInline text="Loading" />
            </p>
          </div>
        </section>

        {/* Page Loader */}
        <section className="bg-slate-800/50 rounded-lg p-8 backdrop-blur-sm">
          <h2 className="text-2xl font-semibold text-white mb-6">Page Loader</h2>
          <div className="bg-slate-900/50 rounded-lg">
            <PageLoader text="Loading" message="Fetching your data..." />
          </div>
        </section>

        {/* Code Examples */}
        <section className="bg-slate-800/50 rounded-lg p-8 backdrop-blur-sm">
          <h2 className="text-2xl font-semibold text-white mb-6">Usage Examples</h2>
          <div className="space-y-4">
            <div className="bg-slate-900 p-4 rounded-lg">
              <pre className="text-green-400 text-sm overflow-x-auto">
                <code>{`// Basic usage
<AILoader text="Generating" />

// With size
<AILoader text="Processing" size="lg" />

// Fullscreen overlay
<AILoader text="Loading" fullscreen />

// Inline
<AILoaderInline text="Loading" />

// Page loader with message
<PageLoader text="Loading" message="Please wait..." />`}</code>
              </pre>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="bg-slate-800/50 rounded-lg p-8 backdrop-blur-sm">
          <h2 className="text-2xl font-semibold text-white mb-6">Features</h2>
          <ul className="space-y-3 text-gray-300">
            <li className="flex items-start gap-3">
              <span className="text-green-400 mt-1">✓</span>
              <span>Animated letters with staggered delays</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-400 mt-1">✓</span>
              <span>Rotating gradient circle with dynamic box-shadows</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-400 mt-1">✓</span>
              <span>Three size variants (sm, md, lg)</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-400 mt-1">✓</span>
              <span>Customizable text content</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-400 mt-1">✓</span>
              <span>Fullscreen overlay option</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-400 mt-1">✓</span>
              <span>TypeScript support with full type safety</span>
            </li>
          </ul>
        </section>
      </div>
    </div>
  );
}

export { AILoaderDemo };
