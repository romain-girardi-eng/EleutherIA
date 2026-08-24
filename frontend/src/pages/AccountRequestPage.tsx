import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AnimatePresence, motion } from 'framer-motion';
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronDown,
  CircleUserRound,
  FileCheck2,
  Landmark,
  Loader2,
  LockKeyhole,
  Send,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { apiClient } from '../api/client';
import type {
  AccountRequestPayload,
  AccountRequestRole,
  AccountRequestUse,
} from '../api/client';
import { cn } from '../lib/utils';

const PRIVACY_NOTICE_VERSION = '2026-08-24' as const;

type WizardStep = 1 | 2 | 3;

interface AccountRequestForm {
  fullName: string;
  email: string;
  affiliation: string;
  role: AccountRequestRole | '';
  researchFocus: string;
  intendedUse: AccountRequestUse[];
  privacyAcknowledged: boolean;
  website: string;
}

type FieldErrors = Partial<Record<keyof AccountRequestForm, string>>;

const initialForm: AccountRequestForm = {
  fullName: '',
  email: '',
  affiliation: '',
  role: '',
  researchFocus: '',
  intendedUse: [],
  privacyAcknowledged: false,
  website: '',
};

const roleValues: AccountRequestRole[] = [
  'doctoral_researcher',
  'researcher',
  'student',
  'teacher',
  'independent_scholar',
  'other',
];

const useValues: AccountRequestUse[] = [
  'research',
  'teaching',
  'writing',
  'data_exploration',
  'other',
];

function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

export default function AccountRequestPage() {
  const { t, i18n } = useTranslation();
  const [step, setStep] = useState<WizardStep>(1);
  const [form, setForm] = useState<AccountRequestForm>(initialForm);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitError, setSubmitError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [requestId, setRequestId] = useState('');
  const stepHeadingRef = useRef<HTMLHeadingElement>(null);

  const steps = useMemo(
    () => [
      { number: 1 as const, label: t('accountRequest.steps.identity'), Icon: CircleUserRound },
      { number: 2 as const, label: t('accountRequest.steps.research'), Icon: BookOpen },
      { number: 3 as const, label: t('accountRequest.steps.review'), Icon: FileCheck2 },
    ],
    [t],
  );

  useEffect(() => {
    stepHeadingRef.current?.focus();
  }, [step]);

  const updateField = <K extends keyof AccountRequestForm>(
    field: K,
    value: AccountRequestForm[K],
  ) => {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
    setSubmitError('');
  };

  const validateStep = (targetStep: WizardStep): boolean => {
    const nextErrors: FieldErrors = {};

    if (targetStep === 1) {
      if (form.fullName.trim().length < 2) {
        nextErrors.fullName = t('accountRequest.errors.fullName');
      }
      if (!isValidEmail(form.email)) {
        nextErrors.email = t('accountRequest.errors.email');
      }
      if (!form.role) {
        nextErrors.role = t('accountRequest.errors.role');
      }
    }

    if (targetStep === 2) {
      if (form.researchFocus.trim().length < 20) {
        nextErrors.researchFocus = t('accountRequest.errors.researchFocus');
      }
      if (form.intendedUse.length === 0) {
        nextErrors.intendedUse = t('accountRequest.errors.intendedUse');
      }
    }

    if (targetStep === 3 && !form.privacyAcknowledged) {
      nextErrors.privacyAcknowledged = t('accountRequest.errors.privacy');
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const nextStep = () => {
    if (!validateStep(step) || step === 3) return;
    setStep((current) => Math.min(3, current + 1) as WizardStep);
  };

  const previousStep = () => {
    setErrors({});
    setSubmitError('');
    setStep((current) => Math.max(1, current - 1) as WizardStep);
  };

  const toggleUse = (value: AccountRequestUse) => {
    const selected = form.intendedUse.includes(value);
    updateField(
      'intendedUse',
      selected
        ? form.intendedUse.filter((item) => item !== value)
        : [...form.intendedUse, value],
    );
  };

  const submitRequest = async (event: React.FormEvent) => {
    event.preventDefault();
    if (step < 3) {
      nextStep();
      return;
    }
    if (!validateStep(3) || !form.role) return;

    setIsSubmitting(true);
    setSubmitError('');
    const payload: AccountRequestPayload = {
      full_name: form.fullName.trim(),
      email: form.email.trim().toLowerCase(),
      affiliation: form.affiliation.trim() || undefined,
      role: form.role,
      research_focus: form.researchFocus.trim(),
      intended_use: form.intendedUse,
      privacy_acknowledged: true,
      privacy_notice_version: PRIVACY_NOTICE_VERSION,
      locale: i18n.language,
      website: form.website,
    };

    try {
      const response = await apiClient.requestAccount(payload);
      setRequestId(response.request_id);
    } catch (error: unknown) {
      const status = (error as { response?: { status?: number } }).response?.status;
      setSubmitError(
        status === 429
          ? t('accountRequest.errors.rateLimit')
          : t('accountRequest.errors.submit'),
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (requestId) {
    return (
      <div className="relative min-h-[calc(100vh-3rem)] overflow-hidden px-4 pb-20 pt-32 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-3xl flex-col items-start border-y border-amber-200/70 bg-parchment-50/80 px-6 py-14 shadow-[0_30px_90px_-55px_rgba(120,53,15,0.55)] backdrop-blur-sm sm:px-12 sm:py-16">
          <div className="mb-7 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-800 ring-8 ring-emerald-50">
            <CheckCircle2 className="h-7 w-7" aria-hidden="true" />
          </div>
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-amber-800">
            {t('accountRequest.success.eyebrow')}
          </p>
          <h1 className="max-w-2xl font-display text-4xl leading-tight text-stone-900 sm:text-5xl">
            {t('accountRequest.success.title')}
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-stone-600">
            {t('accountRequest.success.body', { email: form.email })}
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3 text-sm text-stone-600">
            <span className="rounded-full border border-amber-200 bg-white/70 px-4 py-2 font-medium text-stone-800">
              {t('accountRequest.success.reference', { id: requestId })}
            </span>
            <span>{t('accountRequest.success.timing')}</span>
          </div>
          <Link
            to="/login"
            className="mt-10 inline-flex min-h-11 items-center gap-2 rounded-full bg-stone-900 px-5 py-2.5 text-sm font-semibold text-parchment-50 transition-colors hover:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-amber-600 focus:ring-offset-2"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            {t('accountRequest.success.backToLogin')}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-[calc(100vh-3rem)] overflow-hidden px-4 pb-20 pt-28 sm:px-6 lg:px-8 lg:pt-32">
      <div
        className="pointer-events-none absolute left-[6%] top-48 hidden h-px w-[26%] bg-gradient-to-r from-transparent via-amber-500/40 to-amber-700/10 lg:block"
        aria-hidden="true"
      />
      <div className="relative mx-auto grid max-w-6xl gap-7 lg:grid-cols-[0.82fr_1.18fr] lg:gap-16">
        <aside className="lg:sticky lg:top-32 lg:self-start">
          <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-amber-800">
            <Landmark className="h-4 w-4" aria-hidden="true" />
            {t('accountRequest.eyebrow')}
          </p>
          <h1 className="mt-5 max-w-xl font-display text-[clamp(2.6rem,6vw,5.2rem)] leading-[0.95] tracking-[-0.03em] text-stone-900">
            {t('accountRequest.title')}
          </h1>
          <p className="mt-6 max-w-lg text-base leading-7 text-stone-600 sm:text-lg">
            {t('accountRequest.intro')}
          </p>

          <ol
            className="relative mt-7 grid grid-cols-3 gap-1 before:absolute before:left-5 before:right-5 before:top-[27px] before:h-px before:bg-amber-200 before:content-[''] lg:mt-10 lg:block lg:space-y-1 lg:before:bottom-6 lg:before:left-[19px] lg:before:right-auto lg:before:top-6 lg:before:h-auto lg:before:w-px"
            aria-label={t('accountRequest.progressLabel')}
          >
            {steps.map(({ number, label, Icon }) => {
              const active = step === number;
              const complete = step > number;
              return (
                <li
                  key={number}
                  aria-current={active ? 'step' : undefined}
                  className={cn(
                    'relative flex flex-col items-center gap-2 py-2 text-center text-xs transition-colors lg:flex-row lg:gap-4 lg:py-3 lg:text-left lg:text-sm',
                    active ? 'text-stone-900' : 'text-stone-500',
                  )}
                >
                  <span
                    className={cn(
                      'relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border bg-parchment-50 transition-all',
                      active && 'border-amber-700 text-amber-800 shadow-[0_0_0_5px_rgba(217,119,6,0.09)]',
                      complete && 'border-emerald-700 bg-emerald-700 text-white',
                      !active && !complete && 'border-amber-200 text-stone-400',
                    )}
                  >
                    {complete ? <Check className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
                  </span>
                  <span className={cn('font-medium', active && 'font-semibold')}>{label}</span>
                </li>
              );
            })}
          </ol>

          <div className="mt-6 flex max-w-md gap-3 border-t border-amber-200/70 pt-5 text-sm leading-6 text-stone-600 lg:mt-8 lg:pt-6">
            <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-emerald-800" aria-hidden="true" />
            <p>{t('accountRequest.minimalDataPromise')}</p>
          </div>
        </aside>

        <section className="relative border-y border-amber-200/80 bg-parchment-50/85 px-5 py-8 shadow-[0_30px_90px_-55px_rgba(120,53,15,0.55)] backdrop-blur-sm sm:px-9 sm:py-10">
          <div className="mb-8 flex items-center justify-between gap-4 border-b border-amber-200/60 pb-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-800">
                {t('accountRequest.stepCounter', { current: step, total: 3 })}
              </p>
              <h2
                ref={stepHeadingRef}
                tabIndex={-1}
                className="mt-1 font-display text-3xl text-stone-900 outline-none"
              >
                {t(`accountRequest.stepTitles.${step}`)}
              </h2>
            </div>
            <span className="font-display text-5xl text-amber-900/10" aria-hidden="true">
              0{step}
            </span>
          </div>

          <form onSubmit={submitRequest} noValidate>
            <AnimatePresence mode="wait" initial={false}>
              <motion.div
                key={step}
                initial={{ opacity: 0, x: 18 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -12 }}
                transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
              >
                {step === 1 && (
                  <div className="space-y-6">
                    <p className="max-w-xl text-sm leading-6 text-stone-600">
                      {t('accountRequest.identityIntro')}
                    </p>
                    <div className="grid gap-5 sm:grid-cols-2">
                      <Field
                        id="full-name"
                        label={t('accountRequest.fields.fullName')}
                        error={errors.fullName}
                        className="sm:col-span-2"
                      >
                        <input
                          id="full-name"
                          name="full-name"
                          autoComplete="name"
                          required
                          value={form.fullName}
                          onChange={(event) => updateField('fullName', event.target.value)}
                          className={inputClass(errors.fullName)}
                          aria-invalid={Boolean(errors.fullName)}
                          aria-describedby={errors.fullName ? 'full-name-error' : undefined}
                        />
                      </Field>

                      <Field
                        id="request-email"
                        label={t('accountRequest.fields.email')}
                        hint={t('accountRequest.fields.emailHint')}
                        error={errors.email}
                      >
                        <input
                          id="request-email"
                          name="request-email"
                          type="email"
                          autoComplete="email"
                          required
                          value={form.email}
                          onChange={(event) => updateField('email', event.target.value)}
                          className={inputClass(errors.email)}
                          aria-invalid={Boolean(errors.email)}
                          aria-describedby={errors.email ? 'request-email-error' : 'request-email-hint'}
                        />
                      </Field>

                      <Field
                        id="affiliation"
                        label={t('accountRequest.fields.affiliation')}
                        optional={t('accountRequest.optional')}
                        hint={t('accountRequest.fields.affiliationHint')}
                      >
                        <input
                          id="affiliation"
                          name="affiliation"
                          autoComplete="organization"
                          value={form.affiliation}
                          onChange={(event) => updateField('affiliation', event.target.value)}
                          className={inputClass()}
                          aria-describedby="affiliation-hint"
                        />
                      </Field>
                    </div>

                    <Field id="role" label={t('accountRequest.fields.role')} error={errors.role}>
                      <div className="relative">
                        <select
                          id="role"
                          required
                          value={form.role}
                          onChange={(event) => updateField('role', event.target.value as AccountRequestRole)}
                          className={cn(inputClass(errors.role), 'appearance-none pr-10')}
                          aria-invalid={Boolean(errors.role)}
                          aria-describedby={errors.role ? 'role-error' : undefined}
                        >
                          <option value="">{t('accountRequest.fields.rolePlaceholder')}</option>
                          {roleValues.map((value) => (
                            <option key={value} value={value}>
                              {t(`accountRequest.roles.${value}`)}
                            </option>
                          ))}
                        </select>
                        <ChevronDown className="pointer-events-none absolute right-3 top-3.5 h-4 w-4 text-stone-400" />
                      </div>
                    </Field>

                    <div className="absolute left-[-10000px] top-auto h-px w-px overflow-hidden" aria-hidden="true">
                      <label htmlFor="website">Website</label>
                      <input
                        id="website"
                        name="website"
                        tabIndex={-1}
                        autoComplete="off"
                        value={form.website}
                        onChange={(event) => updateField('website', event.target.value)}
                      />
                    </div>
                  </div>
                )}

                {step === 2 && (
                  <div className="space-y-7">
                    <p className="max-w-xl text-sm leading-6 text-stone-600">
                      {t('accountRequest.researchIntro')}
                    </p>
                    <Field
                      id="research-focus"
                      label={t('accountRequest.fields.researchFocus')}
                      hint={t('accountRequest.fields.researchFocusHint')}
                      error={errors.researchFocus}
                    >
                      <textarea
                        id="research-focus"
                        name="research-focus"
                        rows={6}
                        maxLength={800}
                        required
                        value={form.researchFocus}
                        onChange={(event) => updateField('researchFocus', event.target.value)}
                        className={cn(inputClass(errors.researchFocus), 'resize-y leading-6')}
                        aria-invalid={Boolean(errors.researchFocus)}
                        aria-describedby={errors.researchFocus ? 'research-focus-error' : 'research-focus-hint'}
                      />
                      <div className="mt-2 text-right text-xs text-stone-400">
                        {form.researchFocus.length}/800
                      </div>
                    </Field>

                    <fieldset>
                      <legend className="text-sm font-semibold text-stone-800">
                        {t('accountRequest.fields.intendedUse')}{' '}
                        <span className="text-amber-800" aria-hidden="true">*</span>
                      </legend>
                      <p className="mt-1 text-xs leading-5 text-stone-500">
                        {t('accountRequest.fields.intendedUseHint')}
                      </p>
                      <div className="mt-4 grid gap-3 sm:grid-cols-2">
                        {useValues.map((value) => {
                          const selected = form.intendedUse.includes(value);
                          return (
                            <label
                              key={value}
                              className={cn(
                                'flex min-h-12 cursor-pointer items-center gap-3 border px-4 py-3 text-sm transition-colors',
                                selected
                                  ? 'border-amber-700 bg-amber-50 text-stone-900'
                                  : 'border-amber-200/80 bg-white/55 text-stone-600 hover:bg-amber-50/60',
                              )}
                            >
                              <input
                                type="checkbox"
                                checked={selected}
                                onChange={() => toggleUse(value)}
                                className="h-4 w-4 rounded border-amber-300 text-amber-800 focus:ring-amber-700"
                              />
                              {t(`accountRequest.uses.${value}`)}
                            </label>
                          );
                        })}
                      </div>
                      {errors.intendedUse && (
                        <p id="intended-use-error" className="mt-2 text-sm text-red-700" role="alert">
                          {errors.intendedUse}
                        </p>
                      )}
                    </fieldset>
                  </div>
                )}

                {step === 3 && (
                  <div className="space-y-7">
                    <p className="max-w-xl text-sm leading-6 text-stone-600">
                      {t('accountRequest.reviewIntro')}
                    </p>

                    <dl className="divide-y divide-amber-100 border-y border-amber-200/70">
                      <ReviewRow label={t('accountRequest.fields.fullName')} value={form.fullName} />
                      <ReviewRow label={t('accountRequest.fields.email')} value={form.email} />
                      <ReviewRow
                        label={t('accountRequest.fields.affiliation')}
                        value={form.affiliation || t('accountRequest.notProvided')}
                      />
                      <ReviewRow
                        label={t('accountRequest.fields.role')}
                        value={t(`accountRequest.roles.${form.role}`)}
                      />
                      <ReviewRow
                        label={t('accountRequest.fields.intendedUse')}
                        value={form.intendedUse.map((value) => t(`accountRequest.uses.${value}`)).join(', ')}
                      />
                      <ReviewRow
                        label={t('accountRequest.fields.researchFocus')}
                        value={form.researchFocus}
                      />
                    </dl>

                    <div className="bg-emerald-50/70 px-5 py-5 text-sm text-emerald-950 ring-1 ring-inset ring-emerald-200/80">
                      <div className="flex gap-3">
                        <LockKeyhole className="mt-0.5 h-5 w-5 shrink-0 text-emerald-800" aria-hidden="true" />
                        <div>
                          <h3 className="font-semibold">{t('accountRequest.privacy.summaryTitle')}</h3>
                          <p className="mt-1 leading-6 text-emerald-900/80">
                            {t('accountRequest.privacy.summaryBody')}
                          </p>
                        </div>
                      </div>
                    </div>

                    <details className="group border-y border-amber-200/70 py-1">
                      <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-3 py-2 text-sm font-semibold text-stone-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-700">
                        {t('accountRequest.privacy.detailsTitle')}
                        <ChevronDown className="h-4 w-4 transition-transform group-open:rotate-180" />
                      </summary>
                      <div className="space-y-4 pb-5 pt-3 text-sm leading-6 text-stone-600">
                        <PrivacyLine title={t('accountRequest.privacy.controllerTitle')}>
                          {t('accountRequest.privacy.controllerBody')}{' '}
                          <a className="font-medium text-amber-800 underline underline-offset-2" href="mailto:romain.girardi@univ-cotedazur.fr">
                            romain.girardi@univ-cotedazur.fr
                          </a>
                        </PrivacyLine>
                        <PrivacyLine title={t('accountRequest.privacy.purposeTitle')}>
                          {t('accountRequest.privacy.purposeBody')}
                        </PrivacyLine>
                        <PrivacyLine title={t('accountRequest.privacy.legalTitle')}>
                          {t('accountRequest.privacy.legalBody')}
                        </PrivacyLine>
                        <PrivacyLine title={t('accountRequest.privacy.recipientsTitle')}>
                          {t('accountRequest.privacy.recipientsBody')}
                        </PrivacyLine>
                        <PrivacyLine title={t('accountRequest.privacy.retentionTitle')}>
                          {t('accountRequest.privacy.retentionBody')}
                        </PrivacyLine>
                        <PrivacyLine title={t('accountRequest.privacy.rightsTitle')}>
                          {t('accountRequest.privacy.rightsBody')}{' '}
                          <a
                            className="font-medium text-amber-800 underline underline-offset-2"
                            href="https://www.cnil.fr/fr/comprendre-vos-droits"
                            target="_blank"
                            rel="noreferrer"
                          >
                            CNIL
                          </a>
                        </PrivacyLine>
                        <PrivacyLine title={t('accountRequest.privacy.requiredTitle')}>
                          {t('accountRequest.privacy.requiredBody')}
                        </PrivacyLine>
                      </div>
                    </details>

                    <label
                      className={cn(
                        'flex cursor-pointer items-start gap-3 border px-4 py-4 text-sm leading-6 transition-colors',
                        errors.privacyAcknowledged
                          ? 'border-red-300 bg-red-50/60 text-red-900'
                          : 'border-amber-200/80 bg-white/55 text-stone-700 hover:bg-amber-50/60',
                      )}
                    >
                      <input
                        type="checkbox"
                        required
                        checked={form.privacyAcknowledged}
                        onChange={(event) => updateField('privacyAcknowledged', event.target.checked)}
                        className="mt-1 h-4 w-4 rounded border-amber-300 text-amber-800 focus:ring-amber-700"
                        aria-invalid={Boolean(errors.privacyAcknowledged)}
                        aria-describedby={errors.privacyAcknowledged ? 'privacy-error' : undefined}
                      />
                      <span>{t('accountRequest.privacy.acknowledgement')}</span>
                    </label>
                    {errors.privacyAcknowledged && (
                      <p id="privacy-error" className="text-sm text-red-700" role="alert">
                        {errors.privacyAcknowledged}
                      </p>
                    )}
                  </div>
                )}
              </motion.div>
            </AnimatePresence>

            {submitError && (
              <div className="mt-6 border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
                {submitError}
              </div>
            )}

            <div className="mt-9 flex flex-wrap items-center justify-between gap-3 border-t border-amber-200/60 pt-6">
              {step === 1 ? (
                <Link
                  to="/login"
                  className="inline-flex min-h-11 items-center gap-2 px-2 text-sm font-medium text-stone-500 transition-colors hover:text-stone-900 focus:outline-none focus:ring-2 focus:ring-amber-700"
                >
                  <ArrowLeft className="h-4 w-4" aria-hidden="true" />
                  {t('accountRequest.actions.backToLogin')}
                </Link>
              ) : (
                <button
                  type="button"
                  onClick={previousStep}
                  className="inline-flex min-h-11 items-center gap-2 px-2 text-sm font-medium text-stone-500 transition-colors hover:text-stone-900 focus:outline-none focus:ring-2 focus:ring-amber-700"
                >
                  <ArrowLeft className="h-4 w-4" aria-hidden="true" />
                  {t('accountRequest.actions.back')}
                </button>
              )}

              {step < 3 ? (
                <button
                  type="submit"
                  className="inline-flex min-h-11 items-center gap-2 rounded-full bg-stone-900 px-6 py-2.5 text-sm font-semibold text-parchment-50 transition-colors hover:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-amber-600 focus:ring-offset-2"
                >
                  {t('accountRequest.actions.continue')}
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex min-h-11 items-center gap-2 rounded-full bg-amber-800 px-6 py-2.5 text-sm font-semibold text-parchment-50 transition-colors hover:bg-amber-900 focus:outline-none focus:ring-2 focus:ring-amber-600 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? (
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  ) : (
                    <Send className="h-4 w-4" aria-hidden="true" />
                  )}
                  {isSubmitting ? t('accountRequest.actions.sending') : t('accountRequest.actions.submit')}
                </button>
              )}
            </div>
          </form>

          <div className="mt-8 flex items-center gap-2 text-xs text-stone-400">
            <Sparkles className="h-3.5 w-3.5 text-amber-700" aria-hidden="true" />
            {t('accountRequest.reviewPromise')}
          </div>
        </section>
      </div>
    </div>
  );
}

function Field({
  id,
  label,
  hint,
  optional,
  error,
  className,
  children,
}: {
  id: string;
  label: string;
  hint?: string;
  optional?: string;
  error?: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={className}>
      <label htmlFor={id} className="text-sm font-semibold text-stone-800">
        {label}{' '}
        {optional ? (
          <span className="font-normal text-stone-400">— {optional}</span>
        ) : (
          <span className="text-amber-800" aria-hidden="true">*</span>
        )}
      </label>
      {hint && <p id={`${id}-hint`} className="mt-1 text-xs leading-5 text-stone-500">{hint}</p>}
      <div className="mt-2">{children}</div>
      {error && (
        <p id={`${id}-error`} className="mt-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

function inputClass(error?: string): string {
  return cn(
    'block min-h-12 w-full border bg-white/75 px-3.5 py-2.5 text-base text-stone-900 outline-none transition-colors placeholder:text-stone-400',
    'focus:border-amber-700 focus:ring-2 focus:ring-amber-700/15',
    error ? 'border-red-400' : 'border-amber-200/90 hover:border-amber-300',
  );
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid gap-1 py-3 text-sm sm:grid-cols-[9rem_1fr] sm:gap-5">
      <dt className="text-stone-500">{label}</dt>
      <dd className="font-medium text-stone-800">{value}</dd>
    </div>
  );
}

function PrivacyLine({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <p>
      <strong className="font-semibold text-stone-800">{title}:</strong> {children}
    </p>
  );
}
