import { useEffect, useRef, useState } from 'react';
import { X, Mail, KeyRound, ShieldCheck, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from 'react-i18next';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  title?: string;
  message?: string;
}

const RESEND_COOLDOWN_SECONDS = 60;

type LoginStep = 'email' | 'code';

function getErrorStatus(err: unknown): number | undefined {
  const axiosError = err as { response?: { status?: number } };
  return axiosError.response?.status;
}

export default function AuthModal({
  isOpen,
  onClose,
  onSuccess,
  title,
  message
}: AuthModalProps) {
  const { t } = useTranslation();
  const [step, setStep] = useState<LoginStep>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [info, setInfo] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  const { requestCode, verifyCode } = useAuth();
  const hasAutoSubmitted = useRef(false);

  const displayTitle = title || t('login.authRequired');
  const displayMessage = message || t('login.authRequiredMessage');

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const resetState = () => {
    setStep('email');
    setEmail('');
    setCode('');
    setInfo('');
    setError('');
    setCooldown(0);
    hasAutoSubmitted.current = false;
  };

  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await requestCode(email);
      setInfo(response.message || t('login.codeSent'));
      setStep('code');
      setCooldown(RESEND_COOLDOWN_SECONDS);
      hasAutoSubmitted.current = false;
    } catch {
      setError(t('login.genericError'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyCode = async (submittedCode: string) => {
    if (isLoading) return;
    setError('');
    setIsLoading(true);

    try {
      await verifyCode(email, submittedCode);
      onSuccess();
      handleClose();
    } catch (err: unknown) {
      const status = getErrorStatus(err);
      if (status === 401) {
        setError(t('login.invalidCode'));
      } else if (status === 429) {
        setError(t('login.tooManyAttempts'));
      } else {
        setError(t('login.genericError'));
      }
      setCode('');
      hasAutoSubmitted.current = false;
    } finally {
      setIsLoading(false);
    }
  };

  const handleCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const digits = e.target.value.replace(/\D/g, '').slice(0, 6);
    setCode(digits);
    if (digits.length === 6 && !hasAutoSubmitted.current) {
      hasAutoSubmitted.current = true;
      void handleVerifyCode(digits);
    }
  };

  const handleResend = async () => {
    if (cooldown > 0 || isLoading) return;
    setError('');
    setIsLoading(true);

    try {
      const response = await requestCode(email);
      setInfo(response.message || t('login.codeSent'));
      setCooldown(RESEND_COOLDOWN_SECONDS);
      setCode('');
      hasAutoSubmitted.current = false;
    } catch {
      setError(t('login.genericError'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleChangeEmail = () => {
    setStep('email');
    setCode('');
    setError('');
    setInfo('');
    setCooldown(0);
    hasAutoSubmitted.current = false;
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={handleClose}
        />

        {/* Modal */}
        <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="h-10 w-10 bg-primary-600 rounded-full flex items-center justify-center">
                {step === 'email' ? (
                  <Mail className="h-5 w-5 text-white" />
                ) : (
                  <ShieldCheck className="h-5 w-5 text-white" />
                )}
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{displayTitle}</h3>
                <p className="text-sm text-gray-600">{displayMessage}</p>
              </div>
            </div>
            <button
              onClick={handleClose}
              aria-label={t('login.cancel')}
              className="min-h-11 min-w-11 -m-2 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors touch-manipulation"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <div className="ml-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              </div>
            </div>
          )}

          {step === 'email' ? (
            <form onSubmit={handleRequestCode} className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                  {t('login.emailLabel')}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-4 w-4 text-gray-400" />
                  </div>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    autoFocus
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 text-base sm:text-sm"
                    placeholder={t('login.emailPlaceholder')}
                  />
                </div>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={handleClose}
                  className="flex-1 min-h-11 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 touch-manipulation"
                >
                  {t('login.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex-1 min-h-11 px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation"
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      {t('login.sendingCode')}
                    </div>
                  ) : (
                    t('login.sendCode')
                  )}
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-gray-600">{info || t('login.checkInbox')}</p>

              <div>
                <label htmlFor="code" className="block text-sm font-medium text-gray-700 mb-1">
                  {t('login.codeLabel')}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <KeyRound className="h-4 w-4 text-gray-400" />
                  </div>
                  <input
                    id="code"
                    name="code"
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    pattern="\d{6}"
                    maxLength={6}
                    required
                    autoFocus
                    value={code}
                    onChange={handleCodeChange}
                    disabled={isLoading}
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md tracking-[0.5em] text-center font-mono text-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500 text-base sm:text-sm disabled:opacity-50"
                    placeholder={t('login.codePlaceholder')}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between text-xs pt-1">
                <button
                  type="button"
                  onClick={handleChangeEmail}
                  className="inline-flex items-center min-h-11 py-2 -my-2 px-1 -mx-1 text-gray-500 hover:text-gray-700 focus:outline-none touch-manipulation"
                >
                  {t('login.changeEmail')}
                </button>
                <button
                  type="button"
                  onClick={() => void handleResend()}
                  disabled={cooldown > 0 || isLoading}
                  className="inline-flex items-center min-h-11 py-2 -my-2 px-1 -mx-1 text-primary-600 hover:text-primary-700 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation"
                >
                  {cooldown > 0 ? t('login.resendIn', { seconds: cooldown }) : t('login.resend')}
                </button>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={handleClose}
                  className="flex-1 min-h-11 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 touch-manipulation"
                >
                  {t('login.cancel')}
                </button>
                <button
                  type="button"
                  onClick={() => void handleVerifyCode(code)}
                  disabled={isLoading || code.length !== 6}
                  className="flex-1 min-h-11 px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation"
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      {t('login.verifying')}
                    </div>
                  ) : (
                    t('login.verify')
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
