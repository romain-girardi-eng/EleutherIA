import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import {
  Network,
  TrendingUp,
  Users,
  Clock,
  Download,
  Star,
  GitBranch
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import apiClient from '../api/client';
import { formatNumber } from '../i18n/config';
import { AILoader } from '../components/ui/ai-loader';

interface InfluentialNode {
  id: string;
  label: string;
  type: string;
  period: string;
  school: string;
  influence_score: number;
  in_degree: number;
  out_degree: number;
}

interface BridgeFigure {
  id: string;
  label: string;
  type: string;
  school: string;
  period: string;
  connected_schools: string[];
  connected_periods: string[];
  bridge_score: number;
}

interface Cluster {
  id: number;
  size: number;
  nodes: string[];
  sample_labels: string[];
}

interface CitationAnalysis {
  summary: {
    total_nodes: number;
    total_edges: number;
    edge_types: string[];
  };
  top_influential: InfluentialNode[];
  clusters: Cluster[];
  bridges: BridgeFigure[];
  temporal_flow: Record<string, Record<string, number>>;
}

const CitationNetworkPage: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [analysis, setAnalysis] = useState<CitationAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'influential' | 'clusters' | 'bridges' | 'temporal'>('influential');

  useEffect(() => {
    fetchAnalysis();
  }, []);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<CitationAnalysis>('/api/admin/citation-network');
      setAnalysis(response.data);
    } catch (err: unknown) {
      // Handle authentication errors specifically (401 or 403)
      const axiosErr = err as { response?: { status?: number; data?: { error?: string } } };
      if (axiosErr.response?.status === 401 || axiosErr.response?.status === 403) {
        setError('Authentication required. Please log in to view citation network analysis.');
      } else if (axiosErr.response?.data?.error) {
        // Show specific error message from backend
        setError(`Error: ${axiosErr.response.data.error}`);
      } else {
        setError('Failed to load citation network analysis');
      }
      console.error('Citation network error:', err);
    } finally {
      setLoading(false);
    }
  };

  const exportForGephi = async () => {
    try {
      const response = await apiClient.get('/api/admin/citation-network/export-gephi');
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'eleutherai_citation_network.json';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen w-full pt-28 pb-12 bg-transparent">
      <div className="flex items-center justify-center min-h-[60vh] relative z-10">
        <div className="text-center space-y-4">
          <AILoader text="Loading" size="lg" />
          <p className="text-academic-muted mt-6">{t('common.loading')}</p>
        </div>
      </div>
      </div>
    );
  }

  if (error) {
    const isAuthError = error.includes('Authentication required');
    return (
      <div className="min-h-screen w-full pt-28 pb-12 bg-transparent">
      <div className="text-center py-12 space-y-4 relative z-10">
        <p className="text-red-600">{error}</p>
        {isAuthError ? (
          <Button onClick={() => window.location.href = '/login'} className="mt-4">
            Go to Login
          </Button>
        ) : (
          <Button onClick={fetchAnalysis} className="mt-4">
            {t('common.retry')}
          </Button>
        )}
      </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full pt-28 pb-12 bg-transparent">
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-display font-bold text-academic-text flex items-center gap-3">
            <Network className="w-8 h-8 text-primary-600 shrink-0" />
            {t('citationNetwork.title')}
          </h1>
          <p className="text-academic-muted mt-2">
            {t('citationNetwork.subtitle')}
          </p>
        </div>
        <Button onClick={exportForGephi} variant="outline" className="flex items-center gap-2 self-start sm:self-auto">
          <Download className="w-4 h-4" />
          {t('citationNetwork.exportGephi')}
        </Button>
      </div>

      {/* Summary Cards */}
      {analysis && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Network className="w-8 h-8 text-blue-500" />
                <div>
                  <p className="text-sm text-academic-muted">{t('citationNetwork.totalNodes')}</p>
                  <p className="text-2xl font-bold">{formatNumber(analysis.summary.total_nodes, i18n.language)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <GitBranch className="w-8 h-8 text-green-500" />
                <div>
                  <p className="text-sm text-academic-muted">{t('citationNetwork.totalEdges')}</p>
                  <p className="text-2xl font-bold">{formatNumber(analysis.summary.total_edges, i18n.language)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Users className="w-8 h-8 text-purple-500" />
                <div>
                  <p className="text-sm text-academic-muted">{t('citationNetwork.clusters')}</p>
                  <p className="text-2xl font-bold">{analysis.clusters.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Star className="w-8 h-8 text-yellow-500" />
                <div>
                  <p className="text-sm text-academic-muted">{t('citationNetwork.bridges')}</p>
                  <p className="text-2xl font-bold">{analysis.bridges.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto border-b border-academic-border">
        {[
          { key: 'influential', icon: TrendingUp, label: t('citationNetwork.influenceScores') },
          { key: 'clusters', icon: Users, label: t('citationNetwork.clusters') },
          { key: 'bridges', icon: GitBranch, label: t('citationNetwork.bridges') },
          { key: 'temporal', icon: Clock, label: t('citationNetwork.temporalFlow') }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as typeof activeTab)}
            className={`flex shrink-0 items-center gap-2 whitespace-nowrap px-4 py-3 min-h-11 border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-academic-muted hover:text-academic-text'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {analysis && (
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === 'influential' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  {t('citationNetwork.topInfluential')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-3">{t('citationNetwork.rank')}</th>
                        <th className="text-left p-3">{t('citationNetwork.node')}</th>
                        <th className="text-left p-3">{t('citationNetwork.type')}</th>
                        <th className="text-left p-3">{t('citationNetwork.period')}</th>
                        <th className="text-left p-3">{t('citationNetwork.school')}</th>
                        <th className="text-right p-3">{t('citationNetwork.score')}</th>
                        <th className="text-right p-3">{t('citationNetwork.inOut')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analysis.top_influential.map((node, index) => (
                        <tr key={node.id} className="border-b hover:bg-parchment-50">
                          <td className="p-3 font-bold text-primary-600">#{index + 1}</td>
                          <td className="p-3 font-medium">{node.label}</td>
                          <td className="p-3">
                            <span className="px-2 py-1 bg-parchment-50 rounded text-xs">
                              {node.type}
                            </span>
                          </td>
                          <td className="p-3 text-sm">{node.period}</td>
                          <td className="p-3 text-sm">{node.school}</td>
                          <td className="p-3 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <div className="w-20 bg-amber-200/60 rounded-full h-2">
                                <div
                                  className="bg-primary-600 h-2 rounded-full"
                                  style={{ width: `${node.influence_score}%` }}
                                />
                              </div>
                              <span className="font-mono text-sm">{node.influence_score.toFixed(1)}</span>
                            </div>
                          </td>
                          <td className="p-3 text-right text-sm text-academic-muted">
                            {node.in_degree}/{node.out_degree}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'clusters' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  {t('citationNetwork.clusters')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {analysis.clusters.map(cluster => (
                    <div key={cluster.id} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold">{t('citationNetwork.clusterTitle', { id: cluster.id + 1 })}</h4>
                        <span className="px-2 py-1 bg-primary-100 text-primary-700 rounded text-sm">
                          {t('citationNetwork.nodesCount', { count: cluster.size })}
                        </span>
                      </div>
                      <div className="space-y-2">
                        <p className="text-sm text-academic-muted">{t('citationNetwork.sampleNodes')}</p>
                        <ul className="list-disc list-inside text-sm space-y-1">
                          {cluster.sample_labels.map((label, i) => (
                            <li key={i}>{label}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'bridges' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <GitBranch className="w-5 h-5" />
                  {t('citationNetwork.bridges')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-academic-muted mb-4">
                  {t('citationNetwork.bridgeDescription')}
                </p>
                <div className="space-y-4">
                  {analysis.bridges.map(bridge => (
                    <div key={bridge.id} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-lg">{bridge.label}</h4>
                        <span className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm font-medium">
                          {t('citationNetwork.bridgeScore', { score: bridge.bridge_score })}
                        </span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-3">
                        <div>
                          <p className="text-xs font-semibold text-academic-muted uppercase mb-1">
                            {t('citationNetwork.connectedSchools', { count: bridge.connected_schools.length })}
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {bridge.connected_schools.map(school => (
                              <span key={school} className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                                {school}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-academic-muted uppercase mb-1">
                            {t('citationNetwork.connectedPeriods', { count: bridge.connected_periods.length })}
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {bridge.connected_periods.map(period => (
                              <span key={period} className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
                                {period}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'temporal' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  {t('citationNetwork.temporalFlowTitle')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-academic-muted mb-4">
                  {t('citationNetwork.temporalDescription')}
                </p>
                <div className="space-y-6">
                  {Object.entries(analysis.temporal_flow)
                    .sort(([a], [b]) => parseInt(a) - parseInt(b))
                    .map(([century, nodes]) => (
                      <div key={century} className="border-l-4 border-primary-600 pl-4">
                        <h4 className="font-semibold mb-2">
                          {parseInt(century) < 0
                            ? t('citationNetwork.centuryBCE', { century: Math.abs(parseInt(century)) })
                            : t('citationNetwork.centuryCE', { century })}
                        </h4>
                        <div className="space-y-2">
                          {Object.entries(nodes)
                            .sort(([, a], [, b]) => b - a)
                            .map(([nodeId, score]) => {
                              const node = analysis.top_influential.find(n => n.id === nodeId);
                              return (
                                <div key={nodeId} className="flex items-center gap-2">
                                  <div className="w-32 truncate text-sm">
                                    {node?.label || nodeId}
                                  </div>
                                  <div className="flex-1 bg-amber-200/60 rounded-full h-2">
                                    <div
                                      className="bg-primary-600 h-2 rounded-full"
                                      style={{ width: `${score}%` }}
                                    />
                                  </div>
                                  <span className="text-xs text-academic-muted w-12 text-right">
                                    {score.toFixed(1)}
                                  </span>
                                </div>
                              );
                            })}
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          )}
        </motion.div>
      )}
    </div>
    </div>
  );
};

export default CitationNetworkPage;
