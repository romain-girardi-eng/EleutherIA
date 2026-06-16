import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle,
  FileText,
  Loader2,
  Pencil,
  Trash2,
  Upload,
  X,
  XCircle,
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { cn } from '../../utils/cn';
import {
  deleteDocument,
  deleteProject,
  getDocumentFileBlob,
  getProject,
  uploadDocument,
  type ProjectDetail,
  type ProjectDocument,
} from '../../api/projects';
import { formatRelativeTime, formatFileSize } from '../ProjectsPage/utils';
import UploadZone from '../ContributePage/UploadZone';

const POLL_INTERVAL_MS = 3500;

// ── Status badge ──────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: ProjectDocument['status'] }) {
  const { t } = useTranslation();

  if (status === 'processing') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 border border-amber-300/70 px-2.5 py-1 text-xs font-medium text-amber-800">
        <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
        {t('projects.document.status.processing')}
      </span>
    );
  }
  if (status === 'ready') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 border border-emerald-300/70 px-2.5 py-1 text-xs font-medium text-emerald-800">
        <CheckCircle className="h-3 w-3" aria-hidden="true" />
        {t('projects.document.status.ready')}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-red-100 border border-red-300/70 px-2.5 py-1 text-xs font-medium text-red-800">
      <XCircle className="h-3 w-3" aria-hidden="true" />
      {t('projects.document.status.failed')}
    </span>
  );
}

// ── Document viewer slide-over ────────────────────────────────────────────────

interface DocumentViewerProps {
  doc: ProjectDocument;
  onClose: () => void;
}

function DocumentViewer({ doc, onClose }: DocumentViewerProps) {
  const { t, i18n } = useTranslation();
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const objectUrlRef = useRef<string | null>(null);

  useEffect(() => {
    if (doc.status !== 'ready') {
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    getDocumentFileBlob(doc.document_id)
      .then((blob) => {
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        objectUrlRef.current = url;
        setObjectUrl(url);
        setLoading(false);
      })
      .catch(() => {
        if (!cancelled) {
          setError(t('projects.viewer.loadError'));
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
    };
  }, [doc.document_id, doc.status, t]);

  // Close on Escape
  useEffect(() => {
    const handle = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handle);
    return () => document.removeEventListener('keydown', handle);
  }, [onClose]);

  const isPdf = doc.content_type === 'application/pdf' || doc.filename.toLowerCase().endsWith('.pdf');

  return (
    <>
      {/* Backdrop */}
      <motion.div
        key="viewer-backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        className="fixed inset-0 z-[70] bg-stone-950/30 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slide-over panel */}
      <motion.aside
        key="viewer-panel"
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', stiffness: 340, damping: 38 }}
        role="dialog"
        aria-modal="true"
        aria-label={doc.filename}
        className={cn(
          'fixed top-0 right-0 z-[71] h-[100dvh]',
          'w-full sm:w-[580px] lg:w-[700px]',
          'flex flex-col',
          'bg-parchment-50/98 border-l border-amber-200/60',
          'shadow-[-16px_0_60px_-24px_rgba(120,53,15,0.35)]',
        )}
      >
        {/* Sticky header */}
        <header className="shrink-0 flex items-start justify-between gap-3 px-5 py-4 border-b border-amber-200/40 bg-white/80 backdrop-blur-sm">
          <div className="min-w-0 flex-1">
            <h2 className="font-display text-base font-semibold text-stone-900 leading-tight truncate">
              {doc.filename}
            </h2>
            <div className="flex flex-wrap items-center gap-3 mt-1">
              <StatusBadge status={doc.status} />
              {doc.page_count !== null && (
                <span className="text-xs text-stone-500 font-mono">
                  {t('projects.viewer.pages', { count: doc.page_count })}
                </span>
              )}
              <span className="text-xs text-stone-400 font-mono">
                {formatFileSize(doc.size_bytes)}
              </span>
              <span className="text-xs text-stone-400">
                {formatRelativeTime(doc.created_at, i18n.language)}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label={t('projects.viewer.close')}
            className="shrink-0 h-9 w-9 inline-flex items-center justify-center rounded-full text-stone-400 hover:bg-amber-100/60 hover:text-amber-900 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        {/* Body */}
        <div className="flex-1 min-h-0 relative">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="h-8 w-8 animate-spin text-amber-600" />
                <p className="text-sm text-stone-500">{t('projects.viewer.loading')}</p>
              </div>
            </div>
          )}

          {!loading && error && (
            <div className="absolute inset-0 flex items-center justify-center p-6">
              <div className="text-center">
                <AlertTriangle className="h-10 w-10 text-amber-500 mx-auto mb-3" />
                <p className="text-stone-600 text-sm">{error}</p>
              </div>
            </div>
          )}

          {!loading && !error && doc.status === 'processing' && (
            <div className="absolute inset-0 flex items-center justify-center p-6">
              <div className="text-center">
                <Loader2 className="h-10 w-10 text-amber-500 animate-spin mx-auto mb-3" />
                <p className="text-stone-600 text-sm">{t('projects.viewer.stillProcessing')}</p>
              </div>
            </div>
          )}

          {!loading && !error && doc.status === 'ready' && objectUrl && (
            isPdf ? (
              <iframe
                src={objectUrl}
                title={doc.filename}
                className="w-full h-full border-0"
                aria-label={doc.filename}
              />
            ) : (
              <div className="w-full h-full overflow-auto p-6">
                <p className="text-stone-600 text-sm">{t('projects.viewer.nonPdfNote')}</p>
                <a
                  href={objectUrl}
                  download={doc.filename}
                  className="mt-3 inline-flex items-center gap-1.5 text-sm text-amber-700 underline underline-offset-2 hover:text-amber-900"
                >
                  {t('projects.viewer.download')}
                </a>
              </div>
            )
          )}
        </div>
      </motion.aside>
    </>
  );
}

// ── Document row ──────────────────────────────────────────────────────────────

interface DocumentRowProps {
  doc: ProjectDocument;
  projectId: string;
  onView: (doc: ProjectDocument) => void;
  onDeleted: (documentId: string) => void;
}

function DocumentRow({ doc, projectId, onView, onDeleted }: DocumentRowProps) {
  const { t, i18n } = useTranslation();
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleDelete = useCallback(async () => {
    setDeleting(true);
    try {
      await deleteDocument(projectId, doc.document_id);
      onDeleted(doc.document_id);
    } catch {
      setDeleting(false);
      setConfirmDelete(false);
    }
  }, [projectId, doc.document_id, onDeleted]);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 8 }}
      transition={{ duration: 0.2 }}
      className="flex items-center gap-3 px-4 py-3.5 rounded-xl border border-stone-200/80 bg-white/60 hover:bg-parchment-50/60 transition-colors group"
    >
      {/* Icon */}
      <span className="shrink-0 h-9 w-9 inline-flex items-center justify-center rounded-lg bg-amber-100/70 text-amber-700">
        <FileText className="h-4 w-4" />
      </span>

      {/* Metadata */}
      <div className="flex-1 min-w-0">
        <button
          type="button"
          onClick={() => onView(doc)}
          disabled={doc.status === 'failed'}
          className="text-left text-sm font-medium text-stone-800 hover:text-amber-900 transition-colors truncate block w-full disabled:cursor-default disabled:text-stone-500"
        >
          {doc.filename}
        </button>
        <div className="flex flex-wrap items-center gap-2 mt-0.5">
          <StatusBadge status={doc.status} />
          {doc.page_count !== null && (
            <span className="text-xs text-stone-400 font-mono">
              {t('projects.viewer.pages', { count: doc.page_count })}
            </span>
          )}
          <span className="text-xs text-stone-400 font-mono">{formatFileSize(doc.size_bytes)}</span>
          <span className="text-xs text-stone-400">
            {formatRelativeTime(doc.created_at, i18n.language)}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="shrink-0 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {doc.status === 'ready' && (
          <button
            type="button"
            onClick={() => onView(doc)}
            aria-label={t('projects.document.view', { name: doc.filename })}
            className="h-8 w-8 inline-flex items-center justify-center rounded-lg text-stone-400 hover:bg-amber-100/60 hover:text-amber-800 transition-colors"
          >
            <FileText className="h-4 w-4" />
          </button>
        )}
        {confirmDelete ? (
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => void handleDelete()}
              disabled={deleting}
              aria-label={t('projects.document.confirmDelete')}
              className="h-8 px-2 rounded-lg text-xs font-medium text-red-700 bg-red-50 hover:bg-red-100 border border-red-200 transition-colors"
            >
              {deleting ? <Loader2 className="h-3 w-3 animate-spin" /> : t('projects.document.yes')}
            </button>
            <button
              type="button"
              onClick={() => setConfirmDelete(false)}
              aria-label={t('projects.document.cancelDelete')}
              className="h-8 w-8 inline-flex items-center justify-center rounded-lg text-stone-400 hover:bg-stone-100 transition-colors"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setConfirmDelete(true)}
            aria-label={t('projects.document.delete', { name: doc.filename })}
            className="h-8 w-8 inline-flex items-center justify-center rounded-lg text-stone-400 hover:bg-red-50 hover:text-red-600 transition-colors"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        )}
      </div>
    </motion.div>
  );
}

// ── Upload zone adapter ───────────────────────────────────────────────────────

interface UploadSectionProps {
  projectId: string;
  onUploaded: (doc: ProjectDocument) => void;
}

function UploadSection({ projectId, onUploaded }: UploadSectionProps) {
  const { t } = useTranslation();
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const handleFilePicked = useCallback(
    async (file: File) => {
      setUploading(true);
      setProgress(0);
      setError(null);
      try {
        const doc = await uploadDocument(projectId, file, (ratio) => {
          setProgress(ratio);
        });
        onUploaded(doc);
        setUploading(false);
        setProgress(0);
      } catch (err) {
        setError(err instanceof Error ? err.message : t('projects.upload.error'));
        setUploading(false);
      }
    },
    [projectId, onUploaded, t]
  );

  return (
    <div className="space-y-3">
      {uploading ? (
        <div className="rounded-2xl border border-amber-300 bg-amber-50/40 px-6 py-8 flex flex-col items-center gap-3">
          <Loader2 className="h-7 w-7 animate-spin text-amber-600" />
          <p className="text-sm font-medium text-stone-700">
            {t('projects.upload.uploading')}
          </p>
          <div className="w-full max-w-xs bg-amber-100 rounded-full h-1.5 overflow-hidden">
            <motion.div
              className="h-full bg-amber-500 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${Math.round(progress * 100)}%` }}
              transition={{ ease: 'linear' }}
            />
          </div>
          <span className="text-xs text-stone-400 font-mono">
            {Math.round(progress * 100)}%
          </span>
        </div>
      ) : (
        <UploadZone onFilePicked={(file) => void handleFilePicked(file)} />
      )}

      {error && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

// ── Delete project confirmation ───────────────────────────────────────────────

interface DeleteProjectDialogProps {
  projectName: string;
  onConfirm: () => void;
  onCancel: () => void;
  deleting: boolean;
}

function DeleteProjectDialog({ projectName, onConfirm, onCancel, deleting }: DeleteProjectDialogProps) {
  const { t } = useTranslation();

  return (
    <>
      <motion.div
        key="delete-backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[70] bg-stone-950/30 backdrop-blur-sm"
        onClick={onCancel}
        aria-hidden="true"
      />
      <motion.div
        key="delete-dialog"
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.96 }}
        transition={{ duration: 0.18 }}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="delete-dialog-title"
        className={cn(
          'fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[71]',
          'w-full max-w-sm rounded-2xl',
          'bg-parchment-50/98 border border-amber-200/70',
          'shadow-[0_24px_60px_-20px_rgba(120,53,15,0.4)]',
          'p-6'
        )}
      >
        <div className="flex items-center gap-3 mb-4">
          <span className="h-10 w-10 inline-flex items-center justify-center rounded-full bg-red-100 text-red-600 shrink-0">
            <AlertTriangle className="h-5 w-5" />
          </span>
          <h3 id="delete-dialog-title" className="font-display text-lg font-semibold text-stone-900">
            {t('projects.deleteProject.title')}
          </h3>
        </div>
        <p className="text-sm text-stone-600 mb-5">
          {t('projects.deleteProject.body', { name: projectName })}
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onCancel} disabled={deleting}>
            {t('projects.deleteProject.cancel')}
          </Button>
          <Button
            variant="destructive"
            onClick={onConfirm}
            disabled={deleting}
          >
            {deleting ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : null}
            {t('projects.deleteProject.confirm')}
          </Button>
        </div>
      </motion.div>
    </>
  );
}

// ── Editable project header ───────────────────────────────────────────────────

interface ProjectHeaderProps {
  project: ProjectDetail;
  onUpdated: (updated: Partial<ProjectDetail>) => void;
  onDeleteRequest: () => void;
}

function ProjectHeader({ project, onUpdated, onDeleteRequest }: ProjectHeaderProps) {
  const { t } = useTranslation();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description ?? '');
  const [saving, setSaving] = useState(false);
  const nameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) nameRef.current?.focus();
  }, [editing]);

  const handleSave = useCallback(async () => {
    if (!name.trim()) return;
    setSaving(true);
    try {
      const { updateProject } = await import('../../api/projects');
      const updated = await updateProject(project.project_id, {
        name: name.trim(),
        description: description.trim() || undefined,
      });
      onUpdated({ name: updated.name, description: updated.description });
      setEditing(false);
    } catch {
      // keep editing open on error
    } finally {
      setSaving(false);
    }
  }, [project.project_id, name, description, onUpdated]);

  const handleCancel = useCallback(() => {
    setName(project.name);
    setDescription(project.description ?? '');
    setEditing(false);
  }, [project.name, project.description]);

  if (editing) {
    return (
      <div className="space-y-3 mb-8">
        <input
          ref={nameRef}
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full rounded-xl border border-amber-300 bg-white/80 px-3.5 py-2.5 font-display text-2xl font-semibold text-stone-900 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 sm:text-3xl"
        />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder={t('projects.modal.descriptionPlaceholder')}
          rows={2}
          className="w-full rounded-xl border border-stone-300 bg-white/80 px-3.5 py-2.5 text-sm text-stone-700 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 resize-none"
        />
        <div className="flex items-center gap-2">
          <Button
            onClick={() => void handleSave()}
            variant="warning"
            disabled={!name.trim() || saving}
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : null}
            {t('projects.header.save')}
          </Button>
          <Button variant="ghost" onClick={handleCancel} disabled={saving}>
            {t('projects.header.cancelEdit')}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start justify-between gap-4 mb-8">
      <div className="min-w-0 flex-1">
        <h1 className="font-display text-3xl sm:text-4xl font-semibold text-stone-900 leading-tight">
          {project.name}
        </h1>
        {project.description && (
          <p className="mt-2 text-stone-600 text-sm leading-relaxed max-w-2xl">
            {project.description}
          </p>
        )}
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <button
          type="button"
          onClick={() => setEditing(true)}
          aria-label={t('projects.header.edit')}
          className="h-9 w-9 inline-flex items-center justify-center rounded-full text-stone-400 hover:bg-amber-100/70 hover:text-amber-800 transition-colors"
        >
          <Pencil className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={onDeleteRequest}
          aria-label={t('projects.header.delete')}
          className="h-9 w-9 inline-flex items-center justify-center rounded-full text-stone-400 hover:bg-red-50 hover:text-red-600 transition-colors"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ProjectDetailPage() {
  const { t } = useTranslation();
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewingDoc, setViewingDoc] = useState<ProjectDocument | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deletingProject, setDeletingProject] = useState(false);
  const [showUpload, setShowUpload] = useState(false);

  const pollTimerRef = useRef<number | null>(null);
  const isMountedRef = useRef(true);

  // Load project
  useEffect(() => {
    if (!projectId) return;
    isMountedRef.current = true;

    const load = async () => {
      try {
        const data = await getProject(projectId);
        if (isMountedRef.current) {
          setProject(data);
          setLoading(false);
        }
      } catch {
        if (isMountedRef.current) {
          setError(t('projects.detail.loadError'));
          setLoading(false);
        }
      }
    };
    void load();

    return () => {
      isMountedRef.current = false;
    };
  }, [projectId, t]);

  // Poll when any document is processing
  useEffect(() => {
    if (!project || !projectId) return;

    const hasProcessing = project.documents.some((d) => d.status === 'processing');
    if (!hasProcessing) {
      if (pollTimerRef.current !== null) {
        window.clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
      return;
    }

    if (pollTimerRef.current !== null) return;

    pollTimerRef.current = window.setInterval(async () => {
      if (!isMountedRef.current) return;
      try {
        const updated = await getProject(projectId);
        if (isMountedRef.current) {
          setProject(updated);
          const stillProcessing = updated.documents.some((d) => d.status === 'processing');
          if (!stillProcessing && pollTimerRef.current !== null) {
            window.clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
          }
        }
      } catch {
        // ignore poll errors
      }
    }, POLL_INTERVAL_MS);

    return () => {
      if (pollTimerRef.current !== null) {
        window.clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, [project, projectId]);

  const handleDocUploaded = useCallback((doc: ProjectDocument) => {
    setProject((prev) =>
      prev
        ? {
            ...prev,
            documents: [doc, ...prev.documents],
            document_count: prev.document_count + 1,
          }
        : prev
    );
    setShowUpload(false);
  }, []);

  const handleDocDeleted = useCallback((documentId: string) => {
    setProject((prev) =>
      prev
        ? {
            ...prev,
            documents: prev.documents.filter((d) => d.document_id !== documentId),
            document_count: Math.max(0, prev.document_count - 1),
          }
        : prev
    );
    if (viewingDoc?.document_id === documentId) setViewingDoc(null);
  }, [viewingDoc]);

  const handleProjectUpdated = useCallback((updated: Partial<ProjectDetail>) => {
    setProject((prev) => (prev ? { ...prev, ...updated } : prev));
  }, []);

  const handleDeleteProject = useCallback(async () => {
    if (!projectId) return;
    setDeletingProject(true);
    try {
      await deleteProject(projectId);
      navigate('/projects');
    } catch {
      setDeletingProject(false);
      setShowDeleteDialog(false);
    }
  }, [projectId, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen w-full pt-28 pb-20">
        <div className="academic-container max-w-4xl">
          <div className="h-10 w-64 rounded bg-stone-200 animate-pulse mb-6" />
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-16 rounded-xl bg-stone-100 animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen w-full pt-28 pb-20">
        <div className="academic-container max-w-4xl text-center">
          <AlertTriangle className="h-12 w-12 text-amber-500 mx-auto mb-4" />
          <p className="text-stone-600">{error ?? t('projects.detail.notFound')}</p>
          <Link to="/projects" className="mt-4 inline-flex items-center gap-1.5 text-sm text-amber-700 hover:text-amber-900 transition-colors">
            <ArrowLeft className="h-4 w-4" />
            {t('projects.backToProjects')}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="min-h-screen w-full pt-28 pb-20">
        <div className="academic-container max-w-4xl relative z-10">
          {/* Breadcrumb */}
          <nav aria-label="Breadcrumb" className="mb-6">
            <Link
              to="/projects"
              className="inline-flex items-center gap-1.5 text-sm text-stone-500 hover:text-amber-800 transition-colors"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              {t('projects.backToProjects')}
            </Link>
          </nav>

          {/* Header (editable) */}
          <ProjectHeader
            project={project}
            onUpdated={handleProjectUpdated}
            onDeleteRequest={() => setShowDeleteDialog(true)}
          />

          {/* Documents section */}
          <section aria-labelledby="documents-heading">
            <div className="flex items-center justify-between mb-4">
              <h2 id="documents-heading" className="font-display text-xl font-semibold text-stone-800">
                {t('projects.documents.title')}
                {project.document_count > 0 && (
                  <span className="ml-2 text-base font-normal text-stone-400 font-mono">
                    ({project.document_count})
                  </span>
                )}
              </h2>
              <Button
                onClick={() => setShowUpload((v) => !v)}
                variant="warning"
                size="sm"
              >
                <Upload className="h-3.5 w-3.5 mr-1.5" />
                {showUpload ? t('projects.upload.hide') : t('projects.upload.add')}
              </Button>
            </div>

            {/* Upload zone (collapsible) */}
            <AnimatePresence>
              {showUpload && (
                <motion.div
                  key="upload-zone"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.22 }}
                  className="overflow-hidden mb-5"
                >
                  <div className="pt-1 pb-2">
                    <UploadSection
                      projectId={project.project_id}
                      onUploaded={handleDocUploaded}
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Document list */}
            {project.documents.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-14 rounded-2xl border border-dashed border-amber-200/70 bg-amber-50/20 text-center">
                <FileText className="h-10 w-10 text-amber-400 mb-3" />
                <p className="text-stone-500 text-sm">{t('projects.documents.empty')}</p>
                <button
                  type="button"
                  onClick={() => setShowUpload(true)}
                  className="mt-3 text-sm text-amber-700 hover:text-amber-900 underline underline-offset-2 transition-colors"
                >
                  {t('projects.documents.addFirst')}
                </button>
              </div>
            ) : (
              <motion.div
                className="space-y-2"
                initial="hidden"
                animate="visible"
                variants={{
                  hidden: {},
                  visible: { transition: { staggerChildren: 0.04 } },
                }}
              >
                <AnimatePresence mode="popLayout">
                  {project.documents.map((doc) => (
                    <DocumentRow
                      key={doc.document_id}
                      doc={doc}
                      projectId={project.project_id}
                      onView={(d) => setViewingDoc(d)}
                      onDeleted={handleDocDeleted}
                    />
                  ))}
                </AnimatePresence>
              </motion.div>
            )}
          </section>
        </div>
      </div>

      {/* Document viewer slide-over */}
      <AnimatePresence>
        {viewingDoc && (
          <DocumentViewer
            key={viewingDoc.document_id}
            doc={viewingDoc}
            onClose={() => setViewingDoc(null)}
          />
        )}
      </AnimatePresence>

      {/* Delete project confirmation */}
      <AnimatePresence>
        {showDeleteDialog && (
          <DeleteProjectDialog
            projectName={project.name}
            deleting={deletingProject}
            onConfirm={() => void handleDeleteProject()}
            onCancel={() => setShowDeleteDialog(false)}
          />
        )}
      </AnimatePresence>
    </>
  );
}
