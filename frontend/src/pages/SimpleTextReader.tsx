import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AuroraBackground } from '../components/ui/aurora-background';

interface SimpleText {
  id: string;
  title: string;
  author: string;
  language: string;
  raw_text: string;
}

export default function SimpleTextReader() {
  const { t } = useTranslation();
  const { textId } = useParams<{ textId: string }>();
  const [text, setText] = useState<SimpleText | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (!textId) return;

    console.log('SimpleTextReader: Starting fetch for textId:', textId);

    // Fetch work and passages from works API
    const loadWorkAndPassages = async () => {
      try {
        // Get API URL from environment (works for both localhost and production)
        const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

        // Load work metadata
        const workRes = await fetch(`${API_URL}/api/works/${textId}`);
        console.log('Work response status:', workRes.status);
        if (!workRes.ok) {
          throw new Error(`HTTP error! status: ${workRes.status}`);
        }
        const work = await workRes.json();

        // Load passages
        const passagesRes = await fetch(`${API_URL}/api/works/${textId}/passages`);
        let raw_text = '';
        if (passagesRes.ok) {
          const passagesData = await passagesRes.json();
          const passages = passagesData.passages || [];
          // Concatenate all passage texts
          raw_text = passages.map((p: { text_content: string }) => p.text_content).join('\n\n');
        }

        console.log('Data received:', {
          id: work.work_id,
          title: work.title,
          author: work.author,
          raw_text_length: raw_text.length,
          has_raw_text: !!raw_text
        });

        setText({
          id: work.work_id,
          title: work.title,
          author: work.author,
          language: work.language,
          raw_text
        });
        setLoading(false);
      } catch (err: unknown) {
        console.error('Fetch error:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
        setLoading(false);
      }
    };

    loadWorkAndPassages();
  }, [textId]);

  if (loading) {
    return (
      <AuroraBackground className="!min-h-screen !h-auto py-12">
        <div style={{ padding: '20px', fontFamily: 'sans-serif' }} className="max-w-7xl mx-auto relative z-10">
        <h1>{t('simpleTextReader.loading')}</h1>
        <p>{t('simpleTextReader.fetchingTextId', { textId })}</p>
        </div>
      </AuroraBackground>
    );
  }

  if (error) {
    return (
      <AuroraBackground className="!min-h-screen !h-auto py-12">
        <div style={{ padding: '20px', fontFamily: 'sans-serif' }} className="max-w-7xl mx-auto relative z-10">
        <h1 style={{ color: 'red' }}>{t('simpleTextReader.error')}</h1>
        <p>{error}</p>
        <p>{t('simpleTextReader.textId')}: {textId}</p>
        <Link to="/texts" style={{ color: 'blue', textDecoration: 'underline' }}>
          {t('simpleTextReader.backToTexts')}
        </Link>
        </div>
      </AuroraBackground>
    );
  }

  if (!text) {
    return (
      <AuroraBackground className="!min-h-screen !h-auto py-12">
        <div style={{ padding: '20px', fontFamily: 'sans-serif' }} className="max-w-7xl mx-auto relative z-10">
        <h1>{t('simpleTextReader.noTextFound')}</h1>
        <p>{t('simpleTextReader.textId')}: {textId}</p>
        <Link to="/texts" style={{ color: 'blue', textDecoration: 'underline' }}>
          {t('simpleTextReader.backToTexts')}
        </Link>
        </div>
      </AuroraBackground>
    );
  }

  return (
    <AuroraBackground className="!min-h-screen !h-auto py-12">
      <div style={{ padding: '20px', fontFamily: 'serif', maxWidth: '800px', margin: '0 auto' }} className="relative z-10">
      <Link to="/texts" style={{ color: 'blue', textDecoration: 'underline', marginBottom: '20px', display: 'block' }}>
        ← {t('simpleTextReader.backToTexts')}
      </Link>

      <h1 style={{ fontSize: '28px', marginBottom: '10px' }}>{text.title || t('simpleTextReader.untitled')}</h1>

      <p style={{ color: '#666', marginBottom: '20px' }}>
        {t('simpleTextReader.by')} {text.author || t('simpleTextReader.unknown')} • {text.language || t('simpleTextReader.unknownLanguage')}
      </p>

      <div style={{
        marginBottom: '20px',
        padding: '10px',
        backgroundColor: '#f0f0f0',
        borderRadius: '5px'
      }}>
        <strong>{t('simpleTextReader.textStatistics')}:</strong>
        <ul>
          <li>{t('simpleTextReader.rawTextLength')}: {text.raw_text ? text.raw_text.length.toLocaleString() : 0} {t('simpleTextReader.characters')}</li>
          <li>{t('simpleTextReader.wordsApprox')}: {text.raw_text ? text.raw_text.split(/\s+/).length.toLocaleString() : 0}</li>
          <li>{t('simpleTextReader.hasRawText')}: {text.raw_text ? t('simpleTextReader.yes') : t('simpleTextReader.no')}</li>
          <li>{t('simpleTextReader.textId')}: {text.id}</li>
        </ul>
      </div>

      <div style={{
        border: '1px solid #ccc',
        padding: '20px',
        backgroundColor: 'white',
        lineHeight: '1.8',
        fontSize: '18px',
        whiteSpace: 'pre-wrap'
      }}>
        <h2 style={{ fontSize: '20px', marginBottom: '15px' }}>{t('simpleTextReader.textContent')}:</h2>
        {text.raw_text ? (
          <div>{text.raw_text}</div>
        ) : (
          <p style={{ color: 'red', fontStyle: 'italic' }}>{t('simpleTextReader.noTextContentAvailable')}</p>
        )}
      </div>
      </div>
    </AuroraBackground>
  );
}
