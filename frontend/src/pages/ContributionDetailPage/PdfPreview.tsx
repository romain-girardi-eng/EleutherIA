import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Download, ExternalLink, FileText, FileWarning } from 'lucide-react';
import { cn } from '../../lib/utils';

interface PdfPreviewProps {
  title: string | null;
  authors: string[];
  publicationYear: number | null;
  doi: string | null;
  pdfSignedUrl: string | null;
  focusedPage: number | null;
}

export default function PdfPreview({
  title,
  authors,
  publicationYear,
  doi,
  pdfSignedUrl,
  focusedPage,
}: PdfPreviewProps) {
  const { t } = useTranslation();

  const embedSrc = useMemo(() => {
    if (!pdfSignedUrl) return null;
    // Most browser PDF viewers accept `#page=N` to jump to a specific page.
    if (typeof focusedPage === 'number' && focusedPage > 0) {
      const separator = pdfSignedUrl.includes('#') ? '&' : '#';
      return `${pdfSignedUrl}${separator}page=${focusedPage}`;
    }
    return pdfSignedUrl;
  }, [pdfSignedUrl, focusedPage]);

  const authorLine = authors.slice(0, 5).join(', ');

  return (
    <aside
      className={cn(
        'flex flex-col rounded-2xl border border-stone-200/60 bg-white/65 backdrop-blur-sm overflow-hidden',
        'lg:sticky lg:top-24 lg:max-h-[calc(100vh-7rem)]'
      )}
      aria-label={t('contributions.detail.pdfPreview.aria')}
    >
      <div className="border-b border-stone-100 p-4">
        <h2 className="text-sm font-display font-semibold text-stone-800 leading-snug line-clamp-3">
          {title ?? t('contributions.detail.pdfPreview.untitled')}
        </h2>
        {authorLine && (
          <p className="mt-1 text-xs text-stone-500">
            {authorLine}
            {publicationYear ? ` · ${publicationYear}` : ''}
          </p>
        )}
        {doi && (
          <a
            href={`https://doi.org/${doi}`}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 inline-flex items-center gap-1 text-[11px] font-medium text-amber-700 hover:text-amber-900 hover:underline"
          >
            <span>DOI: {doi}</span>
            <ExternalLink className="h-3 w-3" aria-hidden="true" />
          </a>
        )}
        {typeof focusedPage === 'number' && focusedPage > 0 && (
          <div className="mt-2 inline-flex items-center gap-1 rounded-full border border-amber-200/70 bg-amber-50/70 px-2 py-0.5 text-[10px] font-semibold text-amber-800">
            {t('contributions.detail.pdfPreview.jumpedTo', {
              page: focusedPage,
            })}
          </div>
        )}
      </div>

      {/* Mobile: card-style download link (iframes render poorly on phones). */}
      <div className="md:hidden p-4">
        {embedSrc ? (
          <a
            href={embedSrc}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 rounded-xl border border-amber-200/70 bg-amber-50/40 p-4 transition-colors hover:border-amber-300/80 hover:bg-amber-50/70 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400"
          >
            <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
              <FileText className="h-5 w-5" aria-hidden="true" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-stone-800">
                {t('contributions.detail.pdfPreview.openPdf', 'Ouvrir le PDF')}
              </p>
              <p className="mt-0.5 text-xs text-stone-500">
                {t('contributions.detail.pdfPreview.openPdfHint', 'Lecture optimisée pour ordinateur')}
              </p>
            </div>
            <Download className="h-4 w-4 flex-shrink-0 text-amber-700" aria-hidden="true" />
          </a>
        ) : (
          <div className="flex items-center gap-3 rounded-xl border border-stone-200 bg-stone-50/60 p-4">
            <FileWarning className="h-5 w-5 flex-shrink-0 text-stone-400" aria-hidden="true" />
            <p className="text-xs text-stone-500">
              {t('contributions.detail.pdfPreview.unavailable')}
            </p>
          </div>
        )}
      </div>

      {/* Desktop: embedded iframe preview. */}
      <div className="relative hidden md:block flex-1 min-h-[420px] bg-stone-50">
        {embedSrc ? (
          <iframe
            key={embedSrc}
            src={embedSrc}
            title={t('contributions.detail.pdfPreview.iframeTitle')}
            className="absolute inset-0 h-full w-full border-0"
          />
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-2 p-6 text-center">
            <FileWarning
              className="h-8 w-8 text-stone-300"
              aria-hidden="true"
            />
            <p className="text-xs text-stone-500">
              {t('contributions.detail.pdfPreview.unavailable')}
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}
