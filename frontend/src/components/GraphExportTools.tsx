import { Download, FileImage, FileText, BookMarked, X } from 'lucide-react';
import { useState } from 'react';
import type cytoscape from 'cytoscape';

interface GraphExportToolsProps {
  cyRef: React.MutableRefObject<cytoscape.Core | null>;
}

export default function GraphExportTools({ cyRef }: GraphExportToolsProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);
  const [showExportMenu, setShowExportMenu] = useState(false);

  const showSuccess = (message: string) => {
    setExportSuccess(message);
    setTimeout(() => setExportSuccess(null), 3000);
  };

  // Export graph as PNG
  const exportAsPNG = () => {
    if (!cyRef.current) {
      alert('Graph not ready. Please wait for it to load.');
      return;
    }

    setIsExporting(true);
    try {
      const cy = cyRef.current;

      // Check if graph has elements
      if (cy.elements().length === 0) {
        alert('No graph elements to export.');
        setIsExporting(false);
        return;
      }

      // Get PNG as base64 data URI
      const png64 = cy.png({
        full: true,
        scale: 2,
        bg: '#ffffff',
        maxWidth: 4000,
        maxHeight: 4000,
      });

      // Verify we got valid data
      if (!png64 || png64.length < 100) {
        console.error('Invalid PNG data:', png64);
        alert('Failed to generate PNG. Please try again.');
        setIsExporting(false);
        return;
      }

      // Create download link with data URI
      const link = document.createElement('a');
      link.download = `eleutheriate-graph-${Date.now()}.png`;
      link.href = png64;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      showSuccess('Graph exported as PNG');
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export graph. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  // Export graph as SVG (using PNG as fallback since Cytoscape.js doesn't have direct SVG export)
  const exportAsSVG = () => {
    if (!cyRef.current) return;

    setIsExporting(true);
    try {
      // Note: Cytoscape.js doesn't have native SVG export
      // For now, we'll export as high-quality PNG
      // Users can convert to SVG using external tools if needed
      const png = cyRef.current.png({
        full: true,
        scale: 3, // Higher scale for better quality
        bg: '#ffffff',
      });

      const link = document.createElement('a');
      link.download = `eleutheriate-graph-highres-${Date.now()}.png`;
      link.href = png;
      link.click();

      showSuccess('Graph exported as high-res PNG (SVG alternative)');
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export graph. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  // Export graph as JSON (for Cytoscape.js import)
  const exportAsJSON = () => {
    if (!cyRef.current) return;

    setIsExporting(true);
    try {
      const json = cyRef.current.json();
      const blob = new Blob([JSON.stringify(json, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.download = `eleutheriate-graph-${Date.now()}.json`;
      link.href = url;
      link.click();
      URL.revokeObjectURL(url);

      showSuccess('Graph exported as JSON');
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export graph. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  // Export bibliography from visible nodes
  const exportBibliography = () => {
    if (!cyRef.current) return;

    setIsExporting(true);
    try {
      const visibleNodes = cyRef.current.nodes(':visible');
      const allAncientSources = new Set<string>();
      const allModernScholarship = new Set<string>();

      visibleNodes.forEach(node => {
        const data = node.data();
        if (data.ancient_sources && Array.isArray(data.ancient_sources)) {
          data.ancient_sources.forEach((source: string) => allAncientSources.add(source));
        }
        if (data.modern_scholarship && Array.isArray(data.modern_scholarship)) {
          data.modern_scholarship.forEach((source: string) => allModernScholarship.add(source));
        }
      });

      let bibText = '# Bibliography - EleutherIA\n';
      bibText += `Generated: ${new Date().toLocaleDateString()}\n`;
      bibText += `Nodes included: ${visibleNodes.length}\n\n`;

      if (allAncientSources.size > 0) {
        bibText += '## Ancient Sources\n\n';
        Array.from(allAncientSources).sort().forEach((source, i) => {
          bibText += `${i + 1}. ${source}\n`;
        });
        bibText += '\n';
      }

      if (allModernScholarship.size > 0) {
        bibText += '## Modern Scholarship\n\n';
        Array.from(allModernScholarship).sort().forEach((source, i) => {
          bibText += `${i + 1}. ${source}\n`;
        });
      }

      bibText += '\n---\n';
      bibText += 'Source: Girardi, Romain. (2025). EleutherIA: Ancient Free Will Database.\n';
      bibText += 'DOI: 10.5281/zenodo.17379490\n';
      bibText += 'https://free-will.app\n';

      const blob = new Blob([bibText], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.download = `eleutheriate-bibliography-${Date.now()}.txt`;
      link.href = url;
      link.click();
      URL.revokeObjectURL(url);

      showSuccess(`Bibliography exported (${allAncientSources.size + allModernScholarship.size} sources)`);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export bibliography. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  // Export visible nodes as CSV
  const exportAsCSV = () => {
    if (!cyRef.current) return;

    setIsExporting(true);
    try {
      const visibleNodes = cyRef.current.nodes(':visible');

      // CSV headers
      let csv = 'ID,Label,Type,Category,Period,School,Description\n';

      visibleNodes.forEach(node => {
        const data = node.data();
        const row = [
          `"${data.id || ''}"`,
          `"${(data.label || '').replace(/"/g, '""')}"`,
          `"${data.type || ''}"`,
          `"${data.category || ''}"`,
          `"${data.period || ''}"`,
          `"${data.school || ''}"`,
          `"${(data.description || '').replace(/"/g, '""').substring(0, 200)}..."`,
        ].join(',');
        csv += row + '\n';
      });

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.download = `eleutheriate-nodes-${Date.now()}.csv`;
      link.href = url;
      link.click();
      URL.revokeObjectURL(url);

      showSuccess(`${visibleNodes.length} nodes exported as CSV`);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export CSV. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div>
      {/* Toggle Button */}
      <button
        onClick={() => setShowExportMenu(!showExportMenu)}
        className="bg-white shadow-lg rounded-lg px-3 py-2 hover:bg-gray-50 transition-colors flex items-center gap-2 text-sm font-medium"
        aria-label={showExportMenu ? 'Hide export menu' : 'Show export menu'}
      >
        {showExportMenu ? <X className="w-4 h-4" /> : <Download className="w-4 h-4" />}
        <span className="hidden sm:inline">Export</span>
      </button>

      {/* Export Menu */}
      {showExportMenu && (
        <div className="absolute top-12 right-0 bg-white shadow-xl rounded-lg overflow-hidden">
          <div className="p-3 border-b border-gray-200">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Download className="w-4 h-4" />
              Export Graph
            </h3>
          </div>

          <div className="p-2 space-y-1">
          <button
            onClick={exportAsPNG}
            disabled={isExporting}
            className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 rounded transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FileImage className="w-4 h-4 text-primary-600" />
            <span>Export as PNG</span>
          </button>

          <button
            onClick={exportAsSVG}
            disabled={isExporting}
            className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 rounded transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FileImage className="w-4 h-4 text-primary-600" />
            <span>Export as SVG</span>
          </button>

          <button
            onClick={exportAsCSV}
            disabled={isExporting}
            className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 rounded transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FileText className="w-4 h-4 text-primary-600" />
            <span>Export as CSV</span>
          </button>

          <button
            onClick={exportAsJSON}
            disabled={isExporting}
            className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 rounded transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FileText className="w-4 h-4 text-primary-600" />
            <span>Export as JSON</span>
          </button>

          <button
            onClick={exportBibliography}
            disabled={isExporting}
            className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 rounded transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <BookMarked className="w-4 h-4 text-primary-600" />
            <span>Export Bibliography</span>
          </button>
        </div>

        {exportSuccess && (
          <div className="p-2 bg-green-50 border-t border-green-200">
            <p className="text-xs text-green-800 text-center">✓ {exportSuccess}</p>
          </div>
        )}

        {isExporting && (
          <div className="p-2 bg-primary-50 border-t border-primary-200">
            <p className="text-xs text-primary-800 text-center animate-pulse">Exporting...</p>
          </div>
        )}
        </div>
      )}
    </div>
  );
}
