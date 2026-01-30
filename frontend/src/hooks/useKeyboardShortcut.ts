import { useEffect, useRef } from 'react';

type KeyboardHandler = (event: KeyboardEvent) => void;

interface ShortcutConfig {
  key: string;
  ctrl?: boolean;
  alt?: boolean;
  shift?: boolean;
  meta?: boolean; // Command key on Mac
  description?: string;
}

/**
 * Hook for registering keyboard shortcuts
 *
 * @param shortcut - Shortcut configuration
 * @param callback - Function to call when shortcut is triggered
 * @param enabled - Whether the shortcut is active (default: true)
 *
 * @example
 * useKeyboardShortcut({ key: '/', ctrl: true }, () => focusSearchInput())
 * useKeyboardShortcut({ key: 'k', meta: true }, () => openCommandPalette())
 */
export function useKeyboardShortcut(
  shortcut: ShortcutConfig,
  callback: () => void,
  enabled: boolean = true
) {
  const callbackRef = useRef(callback);

  // Update callback ref when it changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!enabled) return;

    const handler: KeyboardHandler = (event) => {
      const { key, ctrl, alt, shift, meta } = shortcut;

      // Check if all modifiers match
      const ctrlMatch = ctrl === undefined || event.ctrlKey === ctrl;
      const altMatch = alt === undefined || event.altKey === alt;
      const shiftMatch = shift === undefined || event.shiftKey === shift;
      const metaMatch = meta === undefined || event.metaKey === meta;
      const keyMatch = event.key.toLowerCase() === key.toLowerCase();

      if (ctrlMatch && altMatch && shiftMatch && metaMatch && keyMatch) {
        event.preventDefault();
        callbackRef.current();
      }
    };

    window.addEventListener('keydown', handler);

    return () => {
      window.removeEventListener('keydown', handler);
    };
  }, [shortcut, enabled]);
}

/**
 * Hook for registering multiple keyboard shortcuts
 *
 * @param shortcuts - Array of [shortcut, callback] pairs
 * @param enabled - Whether shortcuts are active (default: true)
 */
export function useKeyboardShortcuts(
  shortcuts: Array<[ShortcutConfig, () => void]>,
  enabled: boolean = true
) {
  shortcuts.forEach(([shortcut, callback]) => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    useKeyboardShortcut(shortcut, callback, enabled);
  });
}

/**
 * Format shortcut for display
 * @example formatShortcut({ key: '/', ctrl: true }) => "Ctrl + /"
 */
export function formatShortcut(shortcut: ShortcutConfig): string {
  const parts: string[] = [];

  if (shortcut.meta) parts.push('⌘'); // Mac Command
  if (shortcut.ctrl) parts.push('Ctrl');
  if (shortcut.alt) parts.push('Alt');
  if (shortcut.shift) parts.push('Shift');

  parts.push(shortcut.key.toUpperCase());

  return parts.join(' + ');
}
