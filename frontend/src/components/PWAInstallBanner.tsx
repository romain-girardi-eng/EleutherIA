import React from 'react';
import { Download, X, Wifi, WifiOff } from 'lucide-react';
import { usePWAInstall } from '@/hooks/usePWAInstall';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';

interface PWAInstallBannerProps {
  className?: string;
}

export const PWAInstallBanner: React.FC<PWAInstallBannerProps> = ({ className = '' }) => {
  const { t } = useTranslation();
  const { isInstallable, isInstalled, promptInstall } = usePWAInstall();
  const [dismissed, setDismissed] = React.useState(false);

  // Don't show if already installed, not installable, or dismissed
  if (isInstalled || !isInstallable || dismissed) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className={`fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg ${className}`}
        role="banner"
        aria-label={t('pwa.installBanner.install')}
      >
        <div className="max-w-7xl mx-auto px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between flex-wrap">
            <div className="flex-1 flex items-center">
              <span className="flex p-2 rounded-lg bg-blue-800">
                <Download className="h-5 w-5" aria-hidden="true" />
              </span>
              <p className="ml-3 font-medium text-sm sm:text-base">
                <span className="md:hidden">{t('pwa.installBanner.shortMessage')}</span>
                <span className="hidden md:inline">
                  {t('pwa.installBanner.fullMessage')}
                </span>
              </p>
            </div>
            <div className="flex items-center gap-2 mt-2 sm:mt-0 w-full sm:w-auto justify-end">
              <button
                onClick={promptInstall}
                className="flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-blue-600 bg-white hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-blue-600 focus:ring-white transition-colors"
                aria-label={t('pwa.installBanner.install')}
              >
                {t('pwa.installBanner.installButton')}
              </button>
              <button
                onClick={() => setDismissed(true)}
                className="flex-shrink-0 p-1 rounded-md hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-white transition-colors"
                aria-label={t('pwa.installBanner.dismiss')}
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export const OfflineIndicator: React.FC = () => {
  const { t } = useTranslation();
  const { isOnline } = usePWAInstall();

  return (
    <AnimatePresence>
      {!isOnline && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          className="fixed bottom-4 right-4 z-50 bg-yellow-500 text-yellow-900 px-4 py-2 rounded-lg shadow-lg flex items-center gap-2"
          role="status"
          aria-live="polite"
        >
          <WifiOff className="h-5 w-5" aria-hidden="true" />
          <span className="font-medium text-sm">{t('pwa.offlineIndicator.offline')}</span>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export const OnlineStatusIndicator: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { t } = useTranslation();
  const { isOnline } = usePWAInstall();

  return (
    <div
      className={`flex items-center gap-1 text-xs ${className}`}
      role="status"
      aria-label={t('pwa.offlineIndicator.status')}
    >
      {isOnline ? (
        <>
          <Wifi className="h-3 w-3 text-green-500" aria-hidden="true" />
          <span className="text-green-500">{t('pwa.offlineIndicator.online')}</span>
        </>
      ) : (
        <>
          <WifiOff className="h-3 w-3 text-yellow-500" aria-hidden="true" />
          <span className="text-yellow-500">{t('pwa.offlineIndicator.offline')}</span>
        </>
      )}
    </div>
  );
};
