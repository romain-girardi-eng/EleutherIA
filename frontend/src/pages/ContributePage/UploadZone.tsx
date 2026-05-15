import { useCallback, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Upload, FileText, AlertTriangle } from 'lucide-react';
import { cn } from '../../utils/cn';

const MAX_SIZE_BYTES = 25 * 1024 * 1024;
const ACCEPTED_MIME = 'application/pdf';

interface UploadZoneProps {
  onFilePicked: (file: File) => void;
}

export default function UploadZone({ onFilePicked }: UploadZoneProps) {
  const { t } = useTranslation();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validate = useCallback(
    (file: File): string | null => {
      if (file.type !== ACCEPTED_MIME && !file.name.toLowerCase().endsWith('.pdf')) {
        return t('contribute.upload.errors.notPdf');
      }
      if (file.size > MAX_SIZE_BYTES) {
        return t('contribute.upload.errors.tooLarge');
      }
      return null;
    },
    [t]
  );

  const handleFile = useCallback(
    (file: File | undefined | null) => {
      if (!file) return;
      const errorMessage = validate(file);
      if (errorMessage) {
        setError(errorMessage);
        return;
      }
      setError(null);
      onFilePicked(file);
    },
    [validate, onFilePicked]
  );

  const onClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const onKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLDivElement>) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        onClick();
      }
    },
    [onClick]
  );

  return (
    <div className="w-full">
      <div
        role="button"
        tabIndex={0}
        aria-label={t('contribute.upload.dropzoneAria')}
        onClick={onClick}
        onKeyDown={onKeyDown}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          const file = event.dataTransfer.files?.[0];
          handleFile(file);
        }}
        className={cn(
          'relative flex flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed px-8 py-16 text-center transition-all',
          'cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2',
          isDragging
            ? 'border-amber-500 bg-amber-50/80 shadow-inner'
            : 'border-amber-300/70 bg-amber-50/30 hover:border-amber-400 hover:bg-amber-50/60'
        )}
      >
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-100 text-amber-600">
          <Upload className="h-8 w-8" aria-hidden="true" />
        </div>
        <div>
          <p className="text-lg font-semibold text-stone-800">
            {t('contribute.upload.dropPrompt')}
          </p>
          <p className="mt-1 text-sm text-stone-600">
            {t('contribute.upload.orClick')}
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-2 text-xs text-stone-500">
          <span className="inline-flex items-center gap-1 rounded-full bg-white/70 px-2 py-1">
            <FileText className="h-3 w-3" aria-hidden="true" />
            {t('contribute.upload.pdfOnly')}
          </span>
          <span className="rounded-full bg-white/70 px-2 py-1">
            {t('contribute.upload.maxSize')}
          </span>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="sr-only"
          onChange={(event) => handleFile(event.target.files?.[0])}
        />
      </div>

      {error && (
        <div
          role="alert"
          className="mt-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
