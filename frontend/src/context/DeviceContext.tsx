/**
 * DeviceContext
 * Provides device type and capability information throughout the app
 * Part of EleutherIA mobile UI redesign - Week 1 Foundation
 */

import { createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { useIsMobile, useIsTablet, useIsDesktop, useIsTouchDevice, usePrefersDarkMode, usePrefersReducedMotion, useOrientation } from '../hooks/useMediaQuery';

/**
 * Device context value interface
 * Provides comprehensive device information for adaptive UI
 */
export interface DeviceContextValue {
  /** True if viewport width < 768px */
  isMobile: boolean;

  /** True if viewport width between 768px and 1024px */
  isTablet: boolean;

  /** True if viewport width >= 1024px */
  isDesktop: boolean;

  /** True if device supports touch events */
  isTouchDevice: boolean;

  /** True if user prefers dark color scheme */
  prefersDarkMode: boolean;

  /** True if user prefers reduced motion (accessibility) */
  prefersReducedMotion: boolean;

  /** Current device orientation */
  orientation: 'portrait' | 'landscape';

  /** Comprehensive device type classification */
  deviceType: 'mobile' | 'tablet' | 'desktop';

  /** Helper to check if mobile or tablet */
  isMobileOrTablet: boolean;
}

const DeviceContext = createContext<DeviceContextValue | undefined>(undefined);

/**
 * DeviceProvider
 * Wraps app to provide device information to all components
 *
 * @example
 * // In main.tsx or App.tsx:
 * <DeviceProvider>
 *   <App />
 * </DeviceProvider>
 */
export function DeviceProvider({ children }: { children: ReactNode }) {
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();
  const isDesktop = useIsDesktop();
  const isTouchDevice = useIsTouchDevice();
  const prefersDarkMode = usePrefersDarkMode();
  const prefersReducedMotion = usePrefersReducedMotion();
  const orientation = useOrientation();

  // Determine device type
  const deviceType: 'mobile' | 'tablet' | 'desktop' =
    isMobile ? 'mobile' : isTablet ? 'tablet' : 'desktop';

  const value: DeviceContextValue = {
    isMobile,
    isTablet,
    isDesktop,
    isTouchDevice,
    prefersDarkMode,
    prefersReducedMotion,
    orientation,
    deviceType,
    isMobileOrTablet: isMobile || isTablet,
  };

  return (
    <DeviceContext.Provider value={value}>
      {children}
    </DeviceContext.Provider>
  );
}

/**
 * useDevice Hook
 * Access device information in any component
 *
 * @throws Error if used outside DeviceProvider
 *
 * @example
 * function MyComponent() {
 *   const { isMobile, isTouchDevice } = useDevice();
 *
 *   return (
 *     <div>
 *       {isMobile ? <MobileView /> : <DesktopView />}
 *       {isTouchDevice && <TouchOptimizedControls />}
 *     </div>
 *   );
 * }
 */
export function useDevice(): DeviceContextValue {
  const context = useContext(DeviceContext);

  if (context === undefined) {
    throw new Error(
      'useDevice must be used within a DeviceProvider. ' +
      'Wrap your app with <DeviceProvider> in main.tsx or App.tsx'
    );
  }

  return context;
}

/**
 * withDevice HOC
 * Higher-order component to inject device props
 * Useful for class components or complex component patterns
 *
 * @example
 * const MyComponent = withDevice(({ device, ...props }) => {
 *   return device.isMobile ? <MobileView /> : <DesktopView />;
 * });
 */
export function withDevice<P extends object>(
  Component: React.ComponentType<P & { device: DeviceContextValue }>
) {
  return function WithDeviceComponent(props: P) {
    const device = useDevice();
    return <Component {...props} device={device} />;
  };
}
