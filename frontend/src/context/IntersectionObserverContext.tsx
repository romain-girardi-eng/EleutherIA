import React, { createContext, useContext, useEffect, useRef, useCallback } from 'react';

type ObserverCallback = (entry: IntersectionObserverEntry) => void;

interface ObserverContextValue {
  observe: (
    element: Element,
    callback: ObserverCallback,
    options?: IntersectionObserverInit
  ) => void;
  unobserve: (element: Element) => void;
}

const IntersectionObserverContext = createContext<ObserverContextValue | null>(null);

export function IntersectionObserverProvider({
  children
}: {
  children: React.ReactNode
}) {
  const observers = useRef<Map<string, IntersectionObserver>>(new Map());
  const callbacks = useRef<Map<Element, ObserverCallback>>(new Map());

  const getObserver = useCallback((options?: IntersectionObserverInit) => {
    const key = JSON.stringify(options || {});

    if (!observers.current.has(key)) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          const callback = callbacks.current.get(entry.target);
          if (callback) {
            callback(entry);
          }
        });
      }, options);

      observers.current.set(key, observer);
    }

    return observers.current.get(key)!;
  }, []);

  const observe = useCallback((
    element: Element,
    callback: ObserverCallback,
    options?: IntersectionObserverInit
  ) => {
    const observer = getObserver(options);
    callbacks.current.set(element, callback);
    observer.observe(element);
  }, [getObserver]);

  const unobserve = useCallback((element: Element) => {
    callbacks.current.delete(element);

    observers.current.forEach((observer) => {
      observer.unobserve(element);
    });
  }, []);

  useEffect(() => {
    return () => {
      observers.current.forEach((observer) => observer.disconnect());
    };
  }, []);

  return (
    <IntersectionObserverContext.Provider value={{ observe, unobserve }}>
      {children}
    </IntersectionObserverContext.Provider>
  );
}

export function useIntersectionObserver() {
  const context = useContext(IntersectionObserverContext);

  if (!context) {
    throw new Error(
      'useIntersectionObserver must be used within IntersectionObserverProvider'
    );
  }

  return context;
}
