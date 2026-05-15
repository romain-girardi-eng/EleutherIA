/**
 * ExportToolbar — multi-format download bar for the finalised research
 * answer. Each button is a direct link to
 * /api/graphrag/query/{trace_id}/export?format=<fmt>, plus a "share URL"
 * action that copies the canonical session link to the clipboard.
 */

import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, Share2 } from 'lucide-react';
import { cn } from '../../../lib/utils';
import { doctoralApi } from '../../../services/doctoralApi';
import { useToast } from '../../ui/Toast';

type ExportFormat = 'markdown' | 'latex' | 'bibtex' | 'zotero' | 'ris' | 'docx';

interface FormatItem {
  fmt: ExportFormat;
  labelKey: string;
  emoji: string;
}

const FORMATS: ReadonlyArray<FormatItem> = [
  { fmt: 'markdown', labelKey: 'research.doctoral.export.markdown', emoji: '📄' },
  { fmt: 'latex', labelKey: 'research.doctoral.export.latex', emoji: '📜' },
  { fmt: 'bibtex', labelKey: 'research.doctoral.export.bibtex', emoji: '📚' },
  { fmt: 'zotero', labelKey: 'research.doctoral.export.zotero', emoji: '🟠' },
  { fmt: 'ris', labelKey: 'research.doctoral.export.ris', emoji: '📋' },
  { fmt: 'docx', labelKey: 'research.doctoral.export.docx', emoji: '📝' },
];

interface Props {
  traceId: string;
  shareUrl?: string;
  className?: string;
}

export function ExportToolbar({ traceId, shareUrl, className }: Props) {
  const { t } = useTranslation();
  const { showToast } = useToast();
  const [copied, setCopied] = useState(false);
  const [sharing, setSharing] = useState(false);

  const onCopyShare = useCallback(async () => {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // ignore — clipboard unavailable
    }
  }, [shareUrl]);

  const onCreateShare = useCallback(async () => {
    if (sharing) return;
    setSharing(true);
    try {
      const { share_url } = await doctoralApi.createShareLink(traceId);
      await navigator.clipboard.writeText(share_url);
      showToast(t('research.doctoral.export.shareLinkCopied', 'URL copiée'), 'success');
    } catch {
      showToast(t('research.doctoral.export.shareError', 'Erreur lors du partage'), 'error');
    } finally {
      setSharing(false);
    }
  }, [traceId, sharing, showToast, t]);

  return (
    <div
      role="toolbar"
      aria-label={t('research.doctoral.export.toolbarAria')}
      className={cn(
        'flex flex-wrap items-center gap-1.5 rounded-xl border border-stone-200/70 bg-white/80 px-2.5 py-1.5 shadow-sm backdrop-blur-sm',
        className,
      )}
    >
      <span className="mr-1 hidden text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500 sm:inline">
        {t('research.doctoral.export.label')}
      </span>
      {FORMATS.map(({ fmt, labelKey, emoji }) => (
        <a
          key={fmt}
          href={doctoralApi.buildExportUrl(traceId, fmt)}
          target="_blank"
          rel="noopener noreferrer"
          download
          className="inline-flex items-center gap-1 rounded-md border border-stone-200 bg-white px-2 py-1 text-[11px] font-medium text-stone-700 transition hover:border-amber-300 hover:bg-amber-50"
          title={t(labelKey)}
        >
          <span aria-hidden="true">{emoji}</span>
          <span>{t(labelKey)}</span>
        </a>
      ))}
      {shareUrl ? (
        <button
          type="button"
          onClick={onCopyShare}
          className="inline-flex items-center gap-1 rounded-md border border-amber-300 bg-amber-50 px-2 py-1 text-[11px] font-medium text-amber-800 hover:bg-amber-100"
        >
          {copied ? (
            <>
              <Link className="h-3 w-3" aria-hidden="true" />
              {t('research.doctoral.export.shareCopied')}
            </>
          ) : (
            <>
              <Share2 className="h-3 w-3" aria-hidden="true" />
              {t('research.doctoral.export.share')}
            </>
          )}
        </button>
      ) : (
        <button
          type="button"
          onClick={onCreateShare}
          disabled={sharing}
          className="inline-flex items-center gap-1 rounded-md border border-amber-300 bg-amber-50 px-2 py-1 text-[11px] font-medium text-amber-800 hover:bg-amber-100 disabled:opacity-50"
        >
          <Share2 className="h-3 w-3" aria-hidden="true" />
          {sharing
            ? t('research.doctoral.export.shareCreating', '…')
            : t('research.doctoral.export.shareCreate', 'Partager')}
        </button>
      )}
    </div>
  );
}

export default ExportToolbar;
