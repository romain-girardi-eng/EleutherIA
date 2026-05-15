/**
 * SharedTracePage — read-only render of a shared query trace.
 * Fetches /share/{token} from the backend (returns HTML), renders it in an
 * iframe so the backend's own styles apply without polluting the app.
 */

import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? '';

type Status = 'loading' | 'ready' | 'error' | 'expired';

export default function SharedTracePage() {
  const { token } = useParams<{ token: string }>();
  const [status, setStatus] = useState<Status>('loading');
  const [html, setHtml] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      return;
    }
    const url = `${API_URL}/share/${encodeURIComponent(token)}`;
    fetch(url)
      .then(async (res) => {
        const text = await res.text();
        if (res.status === 410) {
          setStatus('expired');
        } else if (!res.ok) {
          setStatus('error');
        } else {
          setHtml(text);
          setStatus('ready');
        }
      })
      .catch(() => setStatus('error'));
  }, [token]);

  if (status === 'loading') {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-amber-600" />
      </div>
    );
  }

  if (status === 'expired') {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-semibold text-stone-700">Ce lien de partage a expiré.</p>
          <a href="/" className="mt-4 inline-block text-amber-700 hover:underline">
            Retour à EleutherIA
          </a>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-semibold text-stone-700">Lien invalide ou introuvable.</p>
          <a href="/" className="mt-4 inline-block text-amber-700 hover:underline">
            Retour à EleutherIA
          </a>
        </div>
      </div>
    );
  }

  return (
    <iframe
      title="Résultat de recherche partagé"
      srcDoc={html}
      className="min-h-screen w-full border-0"
      sandbox="allow-same-origin"
    />
  );
}
