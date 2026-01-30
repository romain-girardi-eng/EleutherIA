/**
 * Focus management utilities for accessibility
 */

/**
 * Get all focusable elements within a container
 * @param container - The container element to search within
 * @returns Array of focusable elements
 */
export function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const focusableSelectors = [
    'a[href]:not([disabled])',
    'button:not([disabled])',
    'textarea:not([disabled])',
    'input:not([disabled]):not([type="hidden"])',
    'select:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]',
    'audio[controls]',
    'video[controls]',
    'iframe',
    'embed',
    'object',
    'summary',
    'details',
  ].join(', ');

  return Array.from(container.querySelectorAll(focusableSelectors)) as HTMLElement[];
}

/**
 * Get the first focusable element within a container
 * @param container - The container element to search within
 * @returns The first focusable element or null
 */
export function getFirstFocusableElement(container: HTMLElement): HTMLElement | null {
  const elements = getFocusableElements(container);
  return elements[0] || null;
}

/**
 * Get the last focusable element within a container
 * @param container - The container element to search within
 * @returns The last focusable element or null
 */
export function getLastFocusableElement(container: HTMLElement): HTMLElement | null {
  const elements = getFocusableElements(container);
  return elements[elements.length - 1] || null;
}

/**
 * Trap focus within a container (for modals/dialogs)
 * @param container - The container to trap focus within
 * @param initialFocus - Optional element to focus initially
 * @returns Cleanup function to remove the trap
 */
export function trapFocus(container: HTMLElement, initialFocus?: HTMLElement): () => void {
  const focusableElements = getFocusableElements(container);

  if (focusableElements.length === 0) {
    // If no focusable elements, make the container focusable
    container.tabIndex = -1;
    container.focus();
    return () => {
      container.tabIndex = 0;
    };
  }

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key !== 'Tab') return;

    // If Tab is pressed alone (not Shift+Tab)
    if (!e.shiftKey) {
      // If focus is on the last element, move to first
      if (document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    } else {
      // If Shift+Tab is pressed
      // If focus is on the first element, move to last
      if (document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      }
    }
  }

  // Add the event listener
  container.addEventListener('keydown', handleKeyDown);

  // Focus initial element or first element
  if (initialFocus && focusableElements.includes(initialFocus)) {
    initialFocus.focus();
  } else {
    firstElement.focus();
  }

  // Return cleanup function
  return () => {
    container.removeEventListener('keydown', handleKeyDown);
  };
}

/**
 * Restore focus to a previous element
 * @param element - The element to restore focus to
 */
export function restoreFocus(element: HTMLElement | null): void {
  if (element && typeof element.focus === 'function') {
    // Use requestAnimationFrame to ensure DOM is ready
    requestAnimationFrame(() => {
      element.focus();
    });
  }
}

/**
 * Lock body scroll (useful for modals)
 * @returns Cleanup function to restore scroll
 */
export function lockBodyScroll(): () => void {
  const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
  const originalOverflow = document.body.style.overflow;
  const originalPaddingRight = document.body.style.paddingRight;

  document.body.style.overflow = 'hidden';

  // Prevent layout shift by adding padding equal to scrollbar width
  if (scrollbarWidth > 0) {
    document.body.style.paddingRight = `${scrollbarWidth}px`;
  }

  return () => {
    document.body.style.overflow = originalOverflow;
    document.body.style.paddingRight = originalPaddingRight;
  };
}

/**
 * Announce message to screen readers using ARIA live region
 * @param message - The message to announce
 * @param priority - The priority level ('polite' or 'assertive')
 * @param timeout - How long to keep the announcement (ms)
 */
export function announce(
  message: string,
  priority: 'polite' | 'assertive' = 'polite',
  timeout: number = 1000
): void {
  // Create announcement element
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.setAttribute('role', priority === 'assertive' ? 'alert' : 'status');

  // Make it visually hidden but readable by screen readers
  announcement.style.position = 'absolute';
  announcement.style.left = '-10000px';
  announcement.style.width = '1px';
  announcement.style.height = '1px';
  announcement.style.overflow = 'hidden';

  // Add message
  announcement.textContent = message;

  // Add to body
  document.body.appendChild(announcement);

  // Remove after timeout
  setTimeout(() => {
    if (document.body.contains(announcement)) {
      document.body.removeChild(announcement);
    }
  }, timeout);
}

/**
 * Check if an element is visible in the viewport
 * @param element - The element to check
 * @param partial - Whether partial visibility counts
 * @returns Whether the element is visible
 */
export function isElementInViewport(element: HTMLElement, partial: boolean = false): boolean {
  const rect = element.getBoundingClientRect();

  if (partial) {
    // Check if any part of the element is visible
    return (
      rect.bottom > 0 &&
      rect.right > 0 &&
      rect.top < window.innerHeight &&
      rect.left < window.innerWidth
    );
  } else {
    // Check if the entire element is visible
    return (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= window.innerHeight &&
      rect.right <= window.innerWidth
    );
  }
}

/**
 * Scroll an element into view if it's not visible
 * @param element - The element to scroll into view
 * @param options - Scroll options
 */
export function ensureElementIsVisible(
  element: HTMLElement,
  options: ScrollIntoViewOptions = { behavior: 'smooth', block: 'nearest', inline: 'nearest' }
): void {
  if (!isElementInViewport(element)) {
    element.scrollIntoView(options);
  }
}

/**
 * Get the currently focused element (cross-browser)
 * @returns The currently focused element or null
 */
export function getFocusedElement(): HTMLElement | null {
  return document.activeElement as HTMLElement || null;
}

/**
 * Check if an element contains focus (including descendants)
 * @param element - The element to check
 * @returns Whether the element or its descendants have focus
 */
export function containsFocus(element: HTMLElement): boolean {
  const activeElement = document.activeElement;
  return element === activeElement || element.contains(activeElement);
}

/**
 * Move focus to the next focusable element
 * @param container - The container to search within
 * @param wrap - Whether to wrap around to the beginning
 */
export function focusNext(container: HTMLElement = document.body, wrap: boolean = true): void {
  const focusableElements = getFocusableElements(container);
  const currentIndex = focusableElements.indexOf(document.activeElement as HTMLElement);

  if (currentIndex === -1) {
    // No element is focused, focus the first one
    focusableElements[0]?.focus();
  } else if (currentIndex < focusableElements.length - 1) {
    // Focus the next element
    focusableElements[currentIndex + 1].focus();
  } else if (wrap) {
    // Wrap to the beginning
    focusableElements[0].focus();
  }
}

/**
 * Move focus to the previous focusable element
 * @param container - The container to search within
 * @param wrap - Whether to wrap around to the end
 */
export function focusPrevious(container: HTMLElement = document.body, wrap: boolean = true): void {
  const focusableElements = getFocusableElements(container);
  const currentIndex = focusableElements.indexOf(document.activeElement as HTMLElement);

  if (currentIndex === -1) {
    // No element is focused, focus the last one
    focusableElements[focusableElements.length - 1]?.focus();
  } else if (currentIndex > 0) {
    // Focus the previous element
    focusableElements[currentIndex - 1].focus();
  } else if (wrap) {
    // Wrap to the end
    focusableElements[focusableElements.length - 1].focus();
  }
}
