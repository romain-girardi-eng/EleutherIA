import { useEffect, useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Mail, KeyRound, ShieldCheck, AlertCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';

const RESEND_COOLDOWN_SECONDS = 60;

type LoginStep = 'email' | 'code';

function getErrorStatus(err: unknown): number | undefined {
  const axiosError = err as { response?: { status?: number } };
  return axiosError.response?.status;
}

export default function LoginPage() {
  const { t } = useTranslation();
  const [step, setStep] = useState<LoginStep>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [info, setInfo] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  const { requestCode, verifyCode } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const hasAutoSubmitted = useRef(false);

  const from = location.state?.from?.pathname || '/';

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

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
      navigate(from, { replace: true });
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

  return (
    <div className="min-h-screen w-full pt-28 pb-12 bg-transparent">
      <div className="relative min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="max-w-md w-full space-y-8 relative z-10">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-primary-600 rounded-full flex items-center justify-center shadow-lg shadow-primary-600/50">
            {step === 'email' ? (
              <Mail className="h-6 w-6 text-white" />
            ) : (
              <ShieldCheck className="h-6 w-6 text-white" />
            )}
          </div>
          <h2 className="mt-6 text-3xl font-display font-bold text-stone-800">
            {t('login.title')}
          </h2>
          <p className="mt-2 text-sm text-stone-600">
            {t('login.subtitle')}
          </p>
        </div>

        <div className="bg-parchment-100/70 backdrop-blur-sm py-8 px-6 shadow-2xl rounded-lg border border-amber-200/60">
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <div className="ml-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              </div>
            </div>
          )}

          {step === 'email' ? (
            <form className="space-y-6" onSubmit={handleRequestCode}>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-stone-600">
                  {t('login.emailLabel')}
                </label>
                <div className="mt-1 relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-stone-400" />
                  </div>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    autoFocus
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="appearance-none block w-full min-h-11 pl-10 pr-3 py-2 border border-amber-200/60 rounded-md placeholder-stone-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 text-base"
                    placeholder={t('login.emailPlaceholder')}
                  />
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="group relative w-full flex justify-center items-center min-h-11 py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <div className="flex items-center">
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
            <div className="space-y-6">
              <p className="text-sm text-stone-600">{info || t('login.checkInbox')}</p>

              <div>
                <label htmlFor="code" className="block text-sm font-medium text-stone-600">
                  {t('login.codeLabel')}
                </label>
                <div className="mt-1 relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <KeyRound className="h-5 w-5 text-stone-400" />
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
                    className="appearance-none block w-full min-h-11 pl-10 pr-3 py-3 border border-amber-200/60 rounded-md placeholder-stone-400 tracking-[0.5em] text-center font-mono text-xl focus:outline-none focus:ring-primary-500 focus:border-primary-500 disabled:opacity-50"
                    placeholder={t('login.codePlaceholder')}
                  />
                </div>
              </div>

              <div>
                <button
                  type="button"
                  onClick={() => void handleVerifyCode(code)}
                  disabled={isLoading || code.length !== 6}
                  className="group relative w-full flex justify-center items-center min-h-11 py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      {t('login.verifying')}
                    </div>
                  ) : (
                    t('login.verify')
                  )}
                </button>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
                <button
                  type="button"
                  onClick={handleChangeEmail}
                  className="min-h-11 px-2 -mx-2 text-stone-500 hover:text-stone-700 focus:outline-none"
                >
                  {t('login.changeEmail')}
                </button>
                <button
                  type="button"
                  onClick={() => void handleResend()}
                  disabled={cooldown > 0 || isLoading}
                  className="min-h-11 px-2 -mx-2 text-primary-600 hover:text-primary-700 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {cooldown > 0 ? t('login.resendIn', { seconds: cooldown }) : t('login.resend')}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="text-center">
          <p className="text-xs text-stone-400">
            {t('login.footerText')}
          </p>
        </div>
        </div>
      </div>
    </div>
  );
}
