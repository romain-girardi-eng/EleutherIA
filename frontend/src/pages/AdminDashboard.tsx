import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity,
  BadgeDollarSign,
  BookOpenCheck,
  Check,
  ChevronDown,
  CircleUserRound,
  Gauge,
  KeyRound,
  RefreshCw,
  Save,
  ShieldAlert,
  UsersRound,
} from 'lucide-react';

import apiClient from '../api/client';
import { Button } from '../components/ui/button';
import { useAuth } from '../context/AuthContext';

type Role = 'admin' | 'researcher' | 'viewer';

interface AccountRequest {
  request_id: string;
  full_name: string;
  email: string;
  affiliation?: string | null;
  requested_role: string;
  research_focus: string;
  intended_use: string[];
  locale: string;
  privacy_notice_version: string;
  status: 'pending' | 'approved' | 'rejected' | 'withdrawn';
  reviewer_notification_status?: string;
  approval_email_status?: string;
  created_at: string;
}

interface AdminUser {
  user_id: string;
  username: string;
  email: string;
  role: Role;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
  last_login_at?: string | null;
  failed_login_attempts: number;
  locked_until?: string | null;
  monthly_token_limit?: number | null;
  monthly_cost_limit_usd?: number | null;
  monthly_query_limit?: number | null;
  allow_deep_mode: boolean;
  notes?: string | null;
  lifetime_queries: number;
  lifetime_tokens: number;
  lifetime_cost_usd: number;
  month_queries: number;
  month_tokens: number;
  month_cost_usd: number;
  last_query_at?: string | null;
  latest_request?: AccountRequest | null;
}

interface AdminSummary {
  users: number;
  active_users: number;
  active_admins: number;
  lifetime_queries: number;
  lifetime_tokens: number;
  lifetime_cost_usd: number;
  month_queries: number;
  month_tokens: number;
  month_cost_usd: number;
  unassigned_queries: number;
  unassigned_cost_usd: number;
}

interface UsersPayload {
  users: AdminUser[];
  summary: AdminSummary;
}

const number = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 });
const usd = new Intl.NumberFormat('fr-FR', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 4,
});

function when(value?: string | null) {
  if (!value) return 'Jamais';
  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

function usageRatio(used: number, limit?: number | null) {
  if (limit == null || limit <= 0) return 0;
  return Math.min(100, (used / limit) * 100);
}

function UsageLine({ label, used, limit, format = number.format }: {
  label: string;
  used: number;
  limit?: number | null;
  format?: (value: number) => string;
}) {
  const ratio = usageRatio(used, limit);
  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between gap-3 text-xs">
        <span className="font-semibold uppercase tracking-[0.12em] text-stone-500">{label}</span>
        <span className="font-medium tabular-nums text-stone-800">
          {format(used)} <span className="font-normal text-stone-400">/ {limit == null ? 'illimité' : format(limit)}</span>
        </span>
      </div>
      <div className="h-1.5 overflow-hidden bg-stone-200" aria-hidden>
        <div
          className={ratio >= 90 ? 'h-full bg-red-700' : ratio >= 70 ? 'h-full bg-amber-700' : 'h-full bg-teal-800'}
          style={{ width: `${ratio}%` }}
        />
      </div>
    </div>
  );
}

function LimitInput({ label, value, onChange, step = 1 }: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  step?: number;
}) {
  return (
    <label className="grid gap-1.5 text-xs font-semibold uppercase tracking-[0.1em] text-stone-500">
      {label}
      <input
        type="number"
        min="0"
        step={step}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Illimité"
        className="min-h-11 border border-stone-300 bg-[#fffdf9] px-3 text-sm font-normal normal-case tracking-normal text-stone-900 outline-none transition focus:border-orange-800 focus:ring-2 focus:ring-orange-800/15"
      />
    </label>
  );
}

function UserLedgerRow({ user, onSaved }: { user: AdminUser; onSaved: () => Promise<void> }) {
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState({
    role: user.role,
    is_active: user.is_active,
    monthly_token_limit: user.monthly_token_limit?.toString() ?? '',
    monthly_cost_limit_usd: user.monthly_cost_limit_usd?.toString() ?? '',
    monthly_query_limit: user.monthly_query_limit?.toString() ?? '',
    allow_deep_mode: user.allow_deep_mode,
    notes: user.notes ?? '',
  });

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await apiClient.patch(`/api/admin/users/${user.user_id}`, {
        role: draft.role,
        is_active: draft.is_active,
        monthly_token_limit: draft.monthly_token_limit === '' ? null : Number(draft.monthly_token_limit),
        monthly_cost_limit_usd: draft.monthly_cost_limit_usd === '' ? null : Number(draft.monthly_cost_limit_usd),
        monthly_query_limit: draft.monthly_query_limit === '' ? null : Number(draft.monthly_query_limit),
        allow_deep_mode: draft.allow_deep_mode,
        notes: draft.notes || null,
      });
      await onSaved();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Modification refusée');
    } finally {
      setSaving(false);
    }
  };

  return (
    <article className="border-t border-stone-300 first:border-t-0">
      <div className="grid gap-4 px-4 py-5 lg:grid-cols-[minmax(240px,1.35fr)_minmax(260px,1fr)_190px_44px] lg:items-center lg:px-6">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="truncate font-display text-xl text-stone-900">{user.latest_request?.full_name || user.username}</h3>
            <span className={user.is_active ? 'bg-teal-900 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[#fffaf1]' : 'bg-stone-300 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-stone-700'}>
              {user.is_active ? 'Actif' : 'Suspendu'}
            </span>
            <span className="border border-stone-300 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-stone-600">{user.role}</span>
          </div>
          <p className="mt-1 truncate text-sm text-stone-600">{user.email}</p>
          <p className="mt-2 text-xs text-stone-400">{user.latest_request?.affiliation || 'Affiliation non renseignée'} · dernière connexion {when(user.last_login_at)}</p>
        </div>
        <div className="grid gap-3">
          <UsageLine label="Tokens · mois" used={user.month_tokens} limit={user.monthly_token_limit} />
          <UsageLine label="Coût · mois" used={user.month_cost_usd} limit={user.monthly_cost_limit_usd} format={usd.format} />
        </div>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm lg:block lg:space-y-1.5">
          <div className="flex justify-between gap-3"><dt className="text-stone-500">Requêtes</dt><dd className="font-semibold tabular-nums">{number.format(user.month_queries)}</dd></div>
          <div className="flex justify-between gap-3"><dt className="text-stone-500">Coût cumulé</dt><dd className="font-semibold tabular-nums">{usd.format(user.lifetime_cost_usd)}</dd></div>
          <div className="flex justify-between gap-3"><dt className="text-stone-500">Dernière activité</dt><dd className="text-right text-xs">{when(user.last_query_at)}</dd></div>
        </dl>
        <button
          type="button"
          aria-expanded={open}
          aria-label={`Configurer ${user.email}`}
          onClick={() => setOpen((value) => !value)}
          className="flex size-11 items-center justify-center border border-stone-300 text-stone-700 transition hover:border-orange-800 hover:text-orange-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-800"
        >
          <ChevronDown className={`size-4 transition-transform ${open ? 'rotate-180' : ''}`} />
        </button>
      </div>
      <div className={`grid transition-[grid-template-rows] duration-300 ease-out ${open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}`}>
        <div className="overflow-hidden">
          <div className="border-t border-stone-200 bg-[#f6efe4] px-4 py-6 lg:px-6">
            <div className="grid gap-8 xl:grid-cols-[1.1fr_0.9fr]">
              <section>
                <p className="mb-4 text-xs font-bold uppercase tracking-[0.16em] text-orange-900">Droits et budgets</p>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <label className="grid gap-1.5 text-xs font-semibold uppercase tracking-[0.1em] text-stone-500">
                    Rôle
                    <select value={draft.role} onChange={(event) => setDraft({ ...draft, role: event.target.value as Role })} className="min-h-11 border border-stone-300 bg-[#fffdf9] px-3 text-sm font-normal normal-case tracking-normal text-stone-900">
                      <option value="viewer">Viewer</option><option value="researcher">Researcher</option><option value="admin">Admin</option>
                    </select>
                  </label>
                  <LimitInput label="Tokens / mois" value={draft.monthly_token_limit} onChange={(value) => setDraft({ ...draft, monthly_token_limit: value })} />
                  <LimitInput label="USD / mois" value={draft.monthly_cost_limit_usd} step={0.01} onChange={(value) => setDraft({ ...draft, monthly_cost_limit_usd: value })} />
                  <LimitInput label="Requêtes / mois" value={draft.monthly_query_limit} onChange={(value) => setDraft({ ...draft, monthly_query_limit: value })} />
                  <label className="flex min-h-11 items-center gap-3 border border-stone-300 bg-[#fffdf9] px-3 text-sm text-stone-800"><input type="checkbox" checked={draft.allow_deep_mode} onChange={(event) => setDraft({ ...draft, allow_deep_mode: event.target.checked })} />Mode Deep autorisé</label>
                  <label className="flex min-h-11 items-center gap-3 border border-stone-300 bg-[#fffdf9] px-3 text-sm text-stone-800"><input type="checkbox" checked={draft.is_active} onChange={(event) => setDraft({ ...draft, is_active: event.target.checked })} />Compte actif</label>
                </div>
                <label className="mt-4 grid gap-1.5 text-xs font-semibold uppercase tracking-[0.1em] text-stone-500">Notes internes<textarea value={draft.notes} onChange={(event) => setDraft({ ...draft, notes: event.target.value })} rows={3} className="border border-stone-300 bg-[#fffdf9] p-3 text-sm font-normal normal-case leading-6 tracking-normal text-stone-900" /></label>
                <div className="mt-4 flex items-center gap-3">
                  <Button onClick={() => void save()} disabled={saving} className="min-h-11 gap-2 bg-stone-900 text-[#fffaf1] hover:bg-orange-900">{saving ? <RefreshCw className="size-4 animate-spin" /> : <Save className="size-4" />}Enregistrer</Button>
                  {error && <p role="alert" className="text-sm text-red-800">{error}</p>}
                </div>
              </section>
              <section>
                <p className="mb-4 text-xs font-bold uppercase tracking-[0.16em] text-orange-900">Dossier et historique</p>
                {user.latest_request ? (
                  <div className="space-y-4 text-sm leading-6 text-stone-700">
                    <p className="font-display text-lg text-stone-900">{user.latest_request.research_focus}</p>
                    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 border-t border-stone-300 pt-3 text-xs">
                      <dt className="text-stone-500">Demande</dt><dd>{user.latest_request.request_id}</dd><dt className="text-stone-500">Situation</dt><dd>{user.latest_request.requested_role || 'non renseignée'}</dd><dt className="text-stone-500">Usages</dt><dd>{(user.latest_request.intended_use ?? []).join(', ') || 'non renseignés'}</dd><dt className="text-stone-500">Consentement</dt><dd>{user.latest_request.privacy_notice_version || 'historique'}</dd>
                    </dl>
                  </div>
                ) : <p className="text-sm text-stone-500">Compte historique sans dossier de demande associé.</p>}
              </section>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}

export default function AdminDashboard() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [tab, setTab] = useState<'users' | 'requests'>('users');
  const [payload, setPayload] = useState<UsersPayload | null>(null);
  const [requests, setRequests] = useState<AccountRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [approving, setApproving] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [usersResponse, requestsResponse] = await Promise.all([
        apiClient.get<UsersPayload>('/api/admin/users'),
        apiClient.get<{ requests: AccountRequest[] }>('/api/admin/account-requests'),
      ]);
      setPayload(usersResponse.data);
      setRequests(requestsResponse.data.requests);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Impossible de charger le registre');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    if (isAuthenticated && user?.role === 'admin') void load();
    else if (!authLoading) setLoading(false);
  }, [authLoading, isAuthenticated, load, user?.role]);

  const pending = useMemo(() => requests.filter((request) => request.status === 'pending'), [requests]);

  const approve = async (requestId: string) => {
    setApproving(requestId); setError(null);
    try { await apiClient.post(`/api/admin/account-requests/${requestId}/approve`, { role: 'researcher' }); await load(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Approbation impossible'); }
    finally { setApproving(null); }
  };

  if (!authLoading && (!isAuthenticated || user?.role !== 'admin')) {
    return <main className="min-h-screen bg-[#f7f2e9] px-6 pt-36"><div className="mx-auto max-w-xl border-t-4 border-red-900 py-10"><ShieldAlert className="size-8 text-red-900" /><h1 className="mt-5 font-display text-3xl text-stone-900">Accès administrateur requis</h1><p className="mt-3 text-stone-600">Ce registre contient des données personnelles et financières protégées.</p></div></main>;
  }

  return (
    <main className="min-h-screen bg-[#f7f2e9] pb-20 pt-28 text-stone-900">
      <div className="mx-auto max-w-[1480px] px-4 sm:px-7 lg:px-10">
        <header className="grid gap-7 border-b border-stone-300 pb-8 lg:grid-cols-[1fr_auto] lg:items-end"><div><p className="text-xs font-bold uppercase tracking-[0.2em] text-orange-900">Bureau des accès · registre vivant</p><h1 className="mt-3 font-display text-[clamp(2.3rem,5vw,4.8rem)] leading-[0.95] tracking-tight">Utilisateurs<br /><span className="italic text-stone-500">& coût de recherche</span></h1></div><Button variant="outline" onClick={() => void load()} disabled={loading} className="min-h-11 gap-2 border-stone-400 bg-transparent"><RefreshCw className={`size-4 ${loading ? 'animate-spin' : ''}`} />Actualiser</Button></header>
        {payload && <section className="grid border-b border-stone-300 md:grid-cols-2 xl:grid-cols-4" aria-label="Synthèse">{[
          [UsersRound, 'Comptes actifs', number.format(payload.summary.active_users), `${payload.summary.users} au total`],
          [Gauge, 'Tokens ce mois', number.format(payload.summary.month_tokens), `${number.format(payload.summary.month_queries)} requêtes`],
          [BadgeDollarSign, 'Coût ce mois', usd.format(payload.summary.month_cost_usd), `${usd.format(payload.summary.lifetime_cost_usd)} cumulé`],
          [Activity, 'Coût non attribué', usd.format(payload.summary.unassigned_cost_usd), `${number.format(payload.summary.unassigned_queries)} requêtes historiques`],
        ].map(([Icon, label, value, detail]) => { const MetricIcon = Icon as typeof UsersRound; return <div key={String(label)} className="border-stone-300 px-1 py-6 md:[&:nth-child(even)]:border-l xl:border-l xl:first:border-l-0 xl:px-6"><MetricIcon className="size-5 text-orange-900" /><p className="mt-5 text-xs font-bold uppercase tracking-[0.13em] text-stone-500">{String(label)}</p><p className="mt-1 font-display text-3xl tabular-nums">{String(value)}</p><p className="mt-1 text-xs text-stone-400">{String(detail)}</p></div>; })}</section>}
        <nav className="flex gap-7 border-b border-stone-300" aria-label="Sections admin"><button onClick={() => setTab('users')} className={`min-h-14 border-b-2 text-sm font-semibold ${tab === 'users' ? 'border-orange-900 text-orange-900' : 'border-transparent text-stone-500'}`}>Utilisateurs {payload ? `(${payload.users.length})` : ''}</button><button onClick={() => setTab('requests')} className={`min-h-14 border-b-2 text-sm font-semibold ${tab === 'requests' ? 'border-orange-900 text-orange-900' : 'border-transparent text-stone-500'}`}>Demandes {pending.length ? `(${pending.length})` : ''}</button></nav>
        {error && <p role="alert" className="my-5 border-l-4 border-red-900 bg-red-50 px-4 py-3 text-sm text-red-900">{error}</p>}
        {loading && !payload ? <div className="flex min-h-[40vh] items-center justify-center"><RefreshCw className="size-7 animate-spin text-orange-900" /></div> : tab === 'users' ? <section className="bg-[#fffdf9]" aria-label="Registre des utilisateurs">{payload?.users.map((entry) => <UserLedgerRow key={entry.user_id} user={entry} onSaved={load} />)}</section> : <section className="divide-y divide-stone-300 bg-[#fffdf9]" aria-label="Demandes d’accès">{requests.map((request) => <article key={request.request_id} className="grid gap-5 px-5 py-7 lg:grid-cols-[220px_1fr_auto] lg:px-7"><div><p className="font-display text-xl">{request.full_name}</p><p className="mt-1 text-sm text-stone-600">{request.email}</p><p className="mt-2 text-xs text-stone-400">{request.affiliation || 'Sans affiliation'} · {when(request.created_at)}</p></div><div><p className="font-display text-lg leading-7 text-stone-800">{request.research_focus}</p><p className="mt-2 text-xs uppercase tracking-[0.1em] text-stone-500">{request.requested_role} · {(request.intended_use ?? []).join(', ') || 'usage non renseigné'} · consentement {request.privacy_notice_version}</p></div><div className="flex items-start gap-3"><span className="border border-stone-300 px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-stone-600">{request.status}</span>{request.status === 'pending' && <Button onClick={() => void approve(request.request_id)} disabled={approving === request.request_id} className="min-h-11 gap-2 bg-teal-900 text-[#fffaf1] hover:bg-teal-800">{approving === request.request_id ? <RefreshCw className="size-4 animate-spin" /> : <Check className="size-4" />}Approuver</Button>}</div></article>)}{requests.length === 0 && <div className="px-6 py-16 text-center"><BookOpenCheck className="mx-auto size-7 text-teal-800" /><p className="mt-4 font-display text-2xl">Aucune demande conservée pour l’instant.</p></div>}</section>}
        <footer className="mt-8 flex flex-wrap items-center gap-5 border-t border-stone-300 pt-5 text-xs text-stone-500"><span className="flex items-center gap-2"><KeyRound className="size-3.5" />Actions protégées par JWT admin</span><span className="flex items-center gap-2"><CircleUserRound className="size-3.5" />Chaque modification est auditée</span></footer>
      </div>
    </main>
  );
}
