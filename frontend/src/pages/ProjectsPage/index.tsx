import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookOpen,
  Clock,
  FileText,
  FolderOpen,
  Plus,
  X,
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { cn } from '../../utils/cn';
import {
  createProject,
  listProjects,
  type ResearchProject,
} from '../../api/projects';
import { formatRelativeTime } from './utils';

// ── Skeletons ─────────────────────────────────────────────────────────────────

function ProjectCardSkeleton() {
  return (
    <div className="rounded-2xl border border-amber-200/60 bg-white/60 p-6 animate-pulse">
      <div className="h-5 w-2/3 rounded bg-stone-200 mb-3" />
      <div className="h-3.5 w-full rounded bg-stone-100 mb-1.5" />
      <div className="h-3.5 w-3/4 rounded bg-stone-100 mb-5" />
      <div className="flex items-center justify-between">
        <div className="h-3 w-20 rounded bg-stone-100" />
        <div className="h-3 w-16 rounded bg-stone-100" />
      </div>
    </div>
  );
}

// ── Project card ──────────────────────────────────────────────────────────────

interface ProjectCardProps {
  project: ResearchProject;
}

function ProjectCard({ project }: ProjectCardProps) {
  const { t, i18n } = useTranslation();

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
    >
      <Link
        to={`/projects/${project.project_id}`}
        className="group block rounded-2xl border border-amber-200/60 bg-white/60 hover:bg-parchment-50/80 hover:border-amber-300/80 hover:shadow-[0_8px_32px_-12px_rgba(120,53,15,0.25)] transition-all duration-200 p-6 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/60"
      >
        <div className="flex items-start gap-3 mb-3">
          <span className="mt-0.5 h-9 w-9 inline-flex items-center justify-center rounded-xl bg-amber-100/80 text-amber-700 group-hover:bg-amber-200/60 transition-colors shrink-0">
            <FolderOpen className="h-4.5 w-4.5" />
          </span>
          <h2 className="font-display text-[17px] font-semibold text-stone-900 leading-snug group-hover:text-amber-900 transition-colors line-clamp-2">
            {project.name}
          </h2>
        </div>

        {project.description && (
          <p className="text-sm text-stone-600 leading-relaxed line-clamp-2 mb-4 pl-12">
            {project.description}
          </p>
        )}

        <div className="flex items-center justify-between pt-3 border-t border-stone-100 pl-12">
          <span className="inline-flex items-center gap-1.5 text-xs text-stone-500">
            <FileText className="h-3.5 w-3.5" aria-hidden="true" />
            {t('projects.card.documents', { count: project.document_count })}
          </span>
          <span className="inline-flex items-center gap-1 text-xs text-stone-400">
            <Clock className="h-3 w-3" aria-hidden="true" />
            {formatRelativeTime(project.updated_at, i18n.language)}
          </span>
        </div>
      </Link>
    </motion.div>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────

interface EmptyStateProps {
  onNew: () => void;
}

function EmptyState({ onNew }: EmptyStateProps) {
  const { t } = useTranslation();

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-20 text-center"
    >
      <span className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-100/70 text-amber-600 mb-5">
        <BookOpen className="h-8 w-8" aria-hidden="true" />
      </span>
      <h2 className="font-display text-2xl font-semibold text-stone-800 mb-2">
        {t('projects.empty.title')}
      </h2>
      <p className="text-stone-500 text-sm max-w-xs mb-6 leading-relaxed">
        {t('projects.empty.body')}
      </p>
      <Button onClick={onNew} variant="warning">
        <Plus className="h-4 w-4 mr-1.5" />
        {t('projects.newProject')}
      </Button>
    </motion.div>
  );
}

// ── New project modal ─────────────────────────────────────────────────────────

interface NewProjectModalProps {
  onClose: () => void;
  onCreated: (project: ResearchProject) => void;
}

function NewProjectModal({ onClose, onCreated }: NewProjectModalProps) {
  const { t } = useTranslation();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    nameRef.current?.focus();
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!name.trim()) return;
      setSubmitting(true);
      setError(null);
      try {
        const project = await createProject({
          name: name.trim(),
          description: description.trim() || undefined,
        });
        onCreated(project);
      } catch (err) {
        setError(err instanceof Error ? err.message : t('projects.modal.error'));
        setSubmitting(false);
      }
    },
    [name, description, onCreated, t]
  );

  return (
    <>
      {/* Backdrop */}
      <motion.div
        key="modal-backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.18 }}
        className="fixed inset-0 z-[70] bg-stone-950/30 backdrop-blur-sm"
        aria-hidden="true"
        onClick={onClose}
      />

      {/* Panel */}
      <motion.div
        key="modal-panel"
        initial={{ opacity: 0, scale: 0.96, y: -8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: -8 }}
        transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className={cn(
          'fixed top-1/2 left-4 right-4 -translate-y-1/2 z-[71]',
          'sm:left-1/2 sm:right-auto sm:-translate-x-1/2',
          'max-w-md sm:w-full rounded-2xl',
          'max-h-[85vh] overflow-y-auto',
          'bg-parchment-50/98 border border-amber-200/70',
          'shadow-[0_32px_80px_-24px_rgba(120,53,15,0.45)]',
          'p-6'
        )}
      >
        <div className="flex items-center justify-between mb-5">
          <h2
            id="modal-title"
            className="font-display text-xl font-semibold text-stone-900"
          >
            {t('projects.modal.title')}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label={t('projects.modal.close')}
            className="h-11 w-11 -mr-1.5 inline-flex items-center justify-center rounded-full text-stone-400 hover:bg-amber-100/60 hover:text-amber-900 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
          <div>
            <label
              htmlFor="project-name"
              className="block text-xs font-medium text-stone-700 mb-1.5"
            >
              {t('projects.modal.name')}
              <span className="text-amber-700 ml-0.5" aria-hidden="true">*</span>
            </label>
            <input
              ref={nameRef}
              id="project-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t('projects.modal.namePlaceholder')}
              required
              className="w-full rounded-xl border border-stone-300 bg-white/80 px-3.5 py-2.5 text-base text-stone-900 shadow-sm placeholder:text-stone-400 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
            />
          </div>

          <div>
            <label
              htmlFor="project-description"
              className="block text-xs font-medium text-stone-700 mb-1.5"
            >
              {t('projects.modal.description')}
            </label>
            <textarea
              id="project-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t('projects.modal.descriptionPlaceholder')}
              rows={3}
              className="w-full rounded-xl border border-stone-300 bg-white/80 px-3.5 py-2.5 text-sm text-stone-900 shadow-sm placeholder:text-stone-400 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 resize-none"
            />
          </div>

          {error && (
            <p role="alert" className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 pt-1">
            <Button type="button" variant="ghost" onClick={onClose} disabled={submitting} className="min-h-11">
              {t('projects.modal.cancel')}
            </Button>
            <Button
              type="submit"
              variant="warning"
              disabled={!name.trim() || submitting}
              className="min-h-11"
            >
              {submitting ? t('projects.modal.creating') : t('projects.modal.create')}
            </Button>
          </div>
        </form>
      </motion.div>
    </>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

const cardVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.05 },
  },
};

export default function ProjectsPage() {
  const { t } = useTranslation();
  const [projects, setProjects] = useState<ResearchProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    let cancelled = false;
    listProjects()
      .then((data) => {
        if (!cancelled) {
          setProjects(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleCreated = useCallback((project: ResearchProject) => {
    setProjects((prev) => [project, ...prev]);
    setShowModal(false);
  }, []);

  return (
    <div className="min-h-screen w-full pt-28 pb-20">
      <div className="academic-container relative z-10 max-w-5xl">
        {/* Page header */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-10">
          <div>
            <h1 className="font-display text-2xl sm:text-4xl font-semibold text-stone-900">
              {t('projects.title')}
            </h1>
            <p className="mt-2 text-stone-500 text-sm leading-relaxed">
              {t('projects.subtitle')}
            </p>
          </div>
          <Button
            onClick={() => setShowModal(true)}
            variant="warning"
            className="shrink-0 min-h-11"
          >
            <Plus className="h-4 w-4 mr-1.5" />
            <span className="hidden sm:inline">{t('projects.newProject')}</span>
            <span className="sm:hidden">{t('projects.new')}</span>
          </Button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <ProjectCardSkeleton key={i} />
            ))}
          </div>
        ) : projects.length === 0 ? (
          <EmptyState onNew={() => setShowModal(true)} />
        ) : (
          <motion.div
            variants={cardVariants}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            <AnimatePresence mode="popLayout">
              {projects.map((project) => (
                <ProjectCard key={project.project_id} project={project} />
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </div>

      {/* Modal */}
      <AnimatePresence>
        {showModal && (
          <NewProjectModal
            onClose={() => setShowModal(false)}
            onCreated={handleCreated}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
