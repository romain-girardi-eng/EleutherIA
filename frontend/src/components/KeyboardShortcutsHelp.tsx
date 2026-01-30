import { motion, AnimatePresence } from 'framer-motion';
import { X, Keyboard } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';

interface KeyboardShortcutsHelpProps {
  isOpen: boolean;
  onClose: () => void;
}

interface Shortcut {
  keys: string[];
  description: string;
  category: string;
}

const shortcuts: Shortcut[] = [
  { keys: ['Ctrl', 'K'], description: 'Open Search', category: 'Navigation' },
  { keys: ['Ctrl', 'H'], description: 'Go to Home', category: 'Navigation' },
  { keys: ['Shift', '?'], description: 'Show/Hide this help', category: 'General' },
  { keys: ['Esc'], description: 'Close modals/menus', category: 'General' },
  { keys: ['Tab'], description: 'Navigate forward', category: 'General' },
  { keys: ['Shift', 'Tab'], description: 'Navigate backward', category: 'General' },
];

export function KeyboardShortcutsHelp({ isOpen, onClose }: KeyboardShortcutsHelpProps) {
  const categories = Array.from(new Set(shortcuts.map(s => s.category)));

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-[100]"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[101] w-full max-w-2xl mx-4"
          >
            <Card variant="elevated" padding="lg">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Keyboard className="w-6 h-6 text-primary-600" />
                    <CardTitle>Keyboard Shortcuts</CardTitle>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onClose}
                    aria-label="Close keyboard shortcuts help"
                  >
                    <X className="w-5 h-5" />
                  </Button>
                </div>
              </CardHeader>

              <CardContent>
                <div className="space-y-6">
                  {categories.map((category) => (
                    <div key={category}>
                      <h3 className="text-sm font-semibold text-academic-muted uppercase tracking-wider mb-3">
                        {category}
                      </h3>
                      <div className="space-y-2">
                        {shortcuts
                          .filter((s) => s.category === category)
                          .map((shortcut, index) => (
                            <div
                              key={index}
                              className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50 transition-colors"
                            >
                              <span className="text-sm text-academic-text">
                                {shortcut.description}
                              </span>
                              <div className="flex items-center gap-1">
                                {shortcut.keys.map((key, keyIndex) => (
                                  <span key={keyIndex} className="flex items-center gap-1">
                                    <kbd className="px-2 py-1 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-300 rounded shadow-sm">
                                      {key}
                                    </kbd>
                                    {keyIndex < shortcut.keys.length - 1 && (
                                      <span className="text-xs text-gray-400">+</span>
                                    )}
                                  </span>
                                ))}
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-6 pt-4 border-t border-gray-200">
                  <p className="text-xs text-academic-muted text-center">
                    Press <kbd className="px-1.5 py-0.5 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-300 rounded">Shift</kbd> + <kbd className="px-1.5 py-0.5 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-300 rounded">?</kbd> to toggle this help
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
