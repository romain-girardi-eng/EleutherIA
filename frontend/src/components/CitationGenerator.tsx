import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Copy, Check, BookOpen, Download, FileText } from 'lucide-react';

// Inline type definition to avoid module caching issues
interface Citation {
  id?: string;
  text: string;
  source: string;
  format?: 'apa' | 'mla' | 'chicago' | 'bibtex';
  citation?: string;
  url?: string;
  doi?: string;
  node_id?: string;
}

interface CitationGeneratorProps {
  citations: Citation[];
  className?: string;
}

export const CitationGenerator: React.FC<CitationGeneratorProps> = ({
  citations,
  className = ''
}) => {
  const [selectedFormat, setSelectedFormat] = useState<'apa' | 'mla' | 'chicago' | 'bibtex'>('apa');
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const formatStyles = {
    apa: {
      name: 'APA 7th',
      description: 'American Psychological Association',
      bgColor: 'bg-slate-50',
      borderColor: 'border-slate-500',
      textColor: 'text-slate-900'
    },
    mla: {
      name: 'MLA 9th',
      description: 'Modern Language Association',
      bgColor: 'bg-stone-50',
      borderColor: 'border-stone-500',
      textColor: 'text-stone-900'
    },
    chicago: {
      name: 'Chicago 17th',
      description: 'Chicago Manual of Style',
      bgColor: 'bg-zinc-50',
      borderColor: 'border-zinc-500',
      textColor: 'text-zinc-900'
    },
    bibtex: {
      name: 'BibTeX',
      description: 'LaTeX Bibliography',
      bgColor: 'bg-gray-50',
      borderColor: 'border-gray-500',
      textColor: 'text-gray-900'
    }
  };

  const handleCopy = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleCopyAll = async () => {
    const allCitations = citations
      .map(c => formatCitation(c, selectedFormat))
      .join('\n\n');
    try {
      await navigator.clipboard.writeText(allCitations);
      setCopiedIndex(-1);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const formatCitation = (citation: Citation, format: string): string => {
    // Format the ancient source for proper academic citation
    const source = citation.source;

    switch (format) {
      case 'apa':
        // APA style for ancient texts: Author. (Date). Title.
        return citation.citation || source;
      case 'mla':
        // MLA style for ancient texts: Author. Title.
        return citation.citation || source;
      case 'chicago':
        // Chicago style for ancient texts
        return citation.citation || source;
      case 'bibtex':
        const id = (citation.id || citation.source || 'citation').replace(/[^a-zA-Z0-9]/g, '_');
        return `@book{${id},\n  author = {${source.split(',')[0]}},\n  title = {${source.split(',').slice(1).join(',').trim()}},\n  note = {Ancient source}\n}`;
      default:
        return citation.citation || source;
    }
  };

  const handleExport = () => {
    const allCitations = citations
      .map(c => formatCitation(c, selectedFormat))
      .join('\n\n');

    const blob = new Blob([allCitations], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `citations_${selectedFormat}_${Date.now()}.${selectedFormat === 'bibtex' ? 'bib' : 'txt'}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const currentStyle = formatStyles[selectedFormat];

  return (
    <div className={`${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 text-white p-6 rounded-t-2xl">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-white/20 rounded-xl">
            <BookOpen className="w-8 h-8" />
          </div>
          <div className="flex-1">
            <h2 className="text-2xl font-bold mb-2">Citation Generator</h2>
            <p className="text-white/90">
              {citations.length} {citations.length === 1 ? 'citation' : 'citations'} available in multiple formats
            </p>
          </div>
        </div>
      </div>

      {/* Format Selector */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex flex-wrap gap-3 mb-4">
          {Object.entries(formatStyles).map(([format, style]) => (
            <button
              key={format}
              onClick={() => setSelectedFormat(format as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border-2 font-medium transition-all ${
                selectedFormat === format
                  ? `${style.bgColor} ${style.borderColor} ${style.textColor} shadow-md`
                  : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
              }`}
            >
              <div className="text-left">
                <div className="font-bold text-sm">{style.name}</div>
                <div className="text-xs opacity-75">{style.description}</div>
              </div>
            </button>
          ))}
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleCopyAll}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg transition-colors"
          >
            {copiedIndex === -1 ? (
              <>
                <Check className="w-4 h-4" />
                Copied All!
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Copy All
              </>
            )}
          </button>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-800 text-white font-semibold rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            Export {selectedFormat.toUpperCase()}
          </button>
        </div>
      </div>

      {/* Citations List */}
      <div className="bg-white p-6 rounded-b-2xl shadow-xl max-h-[600px] overflow-y-auto">
        <div className="space-y-4">
          {citations.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg">No citations available</p>
              <p className="text-sm">Citations will appear here after you ask a question</p>
            </div>
          ) : (
            citations.map((citation, index) => {
              const formattedCitation = formatCitation(citation, selectedFormat);
              const isCopied = copiedIndex === index;
              const uniqueKey = `citation-${index}-${citation.node_id || citation.id || citation.source.substring(0, 20)}`;

              return (
                <motion.div
                  key={uniqueKey}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="group relative p-4 bg-gray-50 hover:bg-gray-100 border-2 border-gray-200 hover:border-primary-300 rounded-xl transition-all"
                >
                  {/* Citation Number */}
                  <div className="absolute -left-3 -top-3 w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold text-sm shadow-lg">
                    {index + 1}
                  </div>

                  {/* Citation Source (what to cite) */}
                  <div className="mb-3 pl-6">
                    <div className="text-xs font-semibold text-gray-600 uppercase mb-1">Citation:</div>
                    <pre className="text-base text-gray-900 font-serif whitespace-pre-wrap leading-relaxed font-semibold">
                      {formattedCitation}
                    </pre>
                  </div>

                  {/* Context (what the source says) */}
                  <div className="mb-3 pl-6 p-3 bg-gray-50 rounded-lg border-l-4 border-primary-300">
                    <div className="text-xs font-semibold text-gray-600 uppercase mb-1">Context:</div>
                    <p className="text-sm text-gray-700 leading-relaxed italic">
                      {citation.text}
                    </p>
                  </div>

                  {/* Metadata */}
                  <div className="flex flex-wrap gap-2 mb-3 pl-6">
                    {citation.node_id && (
                      <span className="px-2 py-1 bg-slate-100 text-slate-800 text-xs rounded-full font-medium">
                        Node: {citation.node_id.replace(/_/g, ' ')}
                      </span>
                    )}
                    {citation.doi && (
                      <span className="px-2 py-1 bg-stone-100 text-stone-800 text-xs rounded-full font-medium">
                        DOI: {citation.doi}
                      </span>
                    )}
                    {citation.url && (
                      <a
                        href={citation.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-2 py-1 bg-primary-100 text-primary-800 text-xs rounded-full font-medium hover:bg-primary-200 transition-colors"
                      >
                        View Online →
                      </a>
                    )}
                  </div>

                  {/* Copy Button */}
                  <button
                    onClick={() => handleCopy(formattedCitation, index)}
                    className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                      isCopied
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {isCopied ? (
                      <>
                        <Check className="w-4 h-4" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        Copy Citation
                      </>
                    )}
                  </button>
                </motion.div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

export default CitationGenerator;
