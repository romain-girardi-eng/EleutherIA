import { useEffect, useState } from 'react';
import { Check, MessageSquareMore, Send, X } from 'lucide-react';
import { useLocation } from 'react-router-dom';

import {
  submitGeneralFeedback,
  type AnswerReportType,
  type FeedbackScope,
  type FeedbackSeverity,
} from '../api/feedback';
import { useAuth } from '../context/AuthContext';

const APP_COMMIT = [import.meta.env.VITE_APP_COMMIT, import.meta.env.VITE_GIT_SHA]
  .find((value): value is string => typeof value === 'string' && value.length > 0);

const categories: Array<{ value: AnswerReportType; label: string }> = [
  { value: 'factual_error', label: 'Erreur factuelle' },
  { value: 'wrong_citation', label: 'Citation incorrecte' },
  { value: 'missing_source', label: 'Source manquante' },
  { value: 'ui_issue', label: 'Problème d’interface' },
  { value: 'accessibility', label: 'Accessibilité' },
  { value: 'performance', label: 'Performance' },
  { value: 'account_access', label: 'Compte ou accès' },
  { value: 'feature_request', label: 'Idée de fonctionnalité' },
  { value: 'improvement', label: 'Amélioration générale' },
  { value: 'other', label: 'Autre' },
];

function inferScope(pathname: string): FeedbackScope {
  if (/graph|visualizer/.test(pathname)) return 'node';
  if (/texts|passage|bibliography/.test(pathname)) return 'source';
  if (/graphrag|research/.test(pathname)) return 'answer';
  if (/login|request-account|profile/.test(pathname)) return 'account';
  return 'page';
}

export default function FeedbackLauncher() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<AnswerReportType>('improvement');
  const [severity, setSeverity] = useState<FeedbackSeverity>('normal');
  const [message, setMessage] = useState('');
  const [contactAllowed, setContactAllowed] = useState(false);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setOpen(false);
    setSent(false);
    setError('');
  }, [location.pathname]);

  if (!isAuthenticated) return null;

  const send = async (event: React.FormEvent) => {
    event.preventDefault();
    if (message.trim().length < 3 || sending) return;
    setSending(true);
    setError('');
    try {
      const path = `${location.pathname}${location.search}`;
      const entityId = new URLSearchParams(location.search).get('node')
        ?? location.pathname.split('/').filter(Boolean).at(-1);
      await submitGeneralFeedback({
        scope: inferScope(location.pathname),
        report_type: category,
        message: message.trim(),
        severity,
        page_url: path,
        ...(entityId ? { entity_id: entityId } : {}),
        contact_allowed: contactAllowed,
        ...(APP_COMMIT ? { app_commit: APP_COMMIT } : {}),
      });
      setMessage('');
      setSent(true);
    } catch {
      setError('Le feedback n’a pas pu être envoyé. Réessayez.');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed bottom-[max(1rem,env(safe-area-inset-bottom))] left-4 z-[70] sm:left-6">
      {open && (
        <section className="mb-3 w-[min(390px,calc(100vw-2rem))] border border-stone-300 bg-[#fffdf9] shadow-[0_24px_70px_rgba(72,52,36,0.2)]" aria-label="Envoyer un feedback">
          <header className="flex items-start justify-between gap-4 border-b border-stone-200 px-5 py-4">
            <div><p className="text-[10px] font-bold uppercase tracking-[0.17em] text-orange-900">Retour utilisateur</p><h2 className="mt-1 font-display text-2xl text-stone-900">Aidez-nous à affiner EleutherIA.</h2></div>
            <button type="button" onClick={() => setOpen(false)} aria-label="Fermer" className="flex size-10 items-center justify-center text-stone-500 hover:bg-stone-100"><X className="size-4" /></button>
          </header>
          {sent ? (
            <div className="px-5 py-8 text-center"><Check className="mx-auto size-7 text-teal-800" /><p className="mt-3 font-display text-xl">Merci — votre retour est dans le registre admin.</p><button type="button" onClick={() => { setSent(false); setOpen(false); }} className="mt-5 text-sm font-semibold text-orange-900 underline">Fermer</button></div>
          ) : (
            <form onSubmit={send} className="space-y-4 px-5 py-5">
              <label className="grid gap-1.5 text-xs font-semibold uppercase tracking-[0.1em] text-stone-500">Type<select value={category} onChange={(event) => setCategory(event.target.value as AnswerReportType)} className="min-h-11 border border-stone-300 bg-white px-3 text-sm font-normal normal-case tracking-normal text-stone-900">{categories.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
              <label className="grid gap-1.5 text-xs font-semibold uppercase tracking-[0.1em] text-stone-500">Priorité<select value={severity} onChange={(event) => setSeverity(event.target.value as FeedbackSeverity)} className="min-h-11 border border-stone-300 bg-white px-3 text-sm font-normal normal-case tracking-normal text-stone-900"><option value="low">Mineure</option><option value="normal">Normale</option><option value="high">Importante</option><option value="critical">Bloquante</option></select></label>
              <label className="grid gap-1.5 text-xs font-semibold uppercase tracking-[0.1em] text-stone-500">Votre retour<textarea value={message} onChange={(event) => setMessage(event.target.value)} maxLength={8000} rows={5} className="resize-y border border-stone-300 bg-white p-3 text-sm font-normal normal-case leading-6 tracking-normal text-stone-900" placeholder="Décrivez précisément ce que vous avez vu, attendu ou souhaité…" /></label>
              <label className="flex items-start gap-3 text-sm leading-5 text-stone-600"><input type="checkbox" checked={contactAllowed} onChange={(event) => setContactAllowed(event.target.checked)} className="mt-1" />Vous pouvez me recontacter à l’adresse de mon compte.</label>
              {error && <p role="alert" className="text-sm text-red-800">{error}</p>}
              <button type="submit" disabled={message.trim().length < 3 || sending} className="flex min-h-11 w-full items-center justify-center gap-2 bg-stone-900 px-4 text-sm font-semibold text-[#fffaf1] hover:bg-orange-900 disabled:opacity-50"><Send className="size-4" />{sending ? 'Envoi…' : 'Envoyer au registre'}</button>
            </form>
          )}
        </section>
      )}
      <button type="button" onClick={() => setOpen((value) => !value)} aria-expanded={open} className="flex min-h-11 items-center gap-2 border border-stone-300 bg-[#fffdf9] px-4 text-sm font-semibold text-stone-800 shadow-[0_12px_35px_rgba(72,52,36,0.14)] hover:border-orange-800 hover:text-orange-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-800"><MessageSquareMore className="size-4" />Feedback</button>
    </div>
  );
}
