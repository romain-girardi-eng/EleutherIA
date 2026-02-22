import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Database,
  Activity,
  Shield,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Server,
  HardDrive
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import { formatNumber, formatRelativeTime } from '../i18n/config';

interface DatabaseStats {
  kg_nodes: number;
  kg_edges: number;
  ancient_works: number;
  passages: number;
  total_characters: number;
  works_by_language: Array<{ language: string; count: number }>;
  works_by_period: Array<{ period: string; count: number }>;
}

interface HealthStatus {
  overall_status: string;
  services: {
    postgres: string;
    qdrant: string;
    llm: string;
    data_quality: string;
  };
  timestamp: string;
}

interface DataQualitySummary {
  summary: {
    total_issues: number;
    critical_issues: number;
    warnings: number;
  };
  health_score: {
    overall_score: number;
    status: string;
    components: Record<string, number>;
  };
  timestamp: string;
}

const AdminDashboard: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { isAuthenticated } = useAuth();
  const [stats, setStats] = useState<DatabaseStats | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [quality, setQuality] = useState<DataQualitySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    if (isAuthenticated) {
      fetchAllData();
    }
  }, [isAuthenticated]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [statsRes, healthRes, qualityRes] = await Promise.all([
        apiClient.get<DatabaseStats>('/api/admin/statistics'),
        apiClient.get<HealthStatus>('/api/admin/health-check'),
        apiClient.get<DataQualitySummary>('/api/admin/data-quality/summary')
      ]);
      setStats(statsRes.data);
      setHealth(healthRes.data);
      setQuality(qualityRes.data);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Failed to fetch admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  const refreshMetrics = async () => {
    setRefreshing(true);
    try {
      await apiClient.post('/api/admin/refresh-metrics');
      await fetchAllData();
    } catch (err) {
      console.error('Failed to refresh metrics:', err);
    } finally {
      setRefreshing(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'degraded':
      case 'needs_attention':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'critical':
      case 'error':
      case 'disconnected':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-stone-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-700';
      case 'degraded':
      case 'needs_attention':
        return 'bg-yellow-100 text-yellow-700';
      case 'critical':
      case 'error':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-parchment-50 text-stone-600';
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen w-full pt-20 pb-12 bg-transparent">
        <div className="text-center py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <Shield className="w-16 h-16 text-academic-muted mx-auto mb-4" />
          <h2 className="text-xl font-display font-semibold mb-2">{t('admin.authRequired')}</h2>
          <p className="text-academic-muted">{t('admin.authRequiredDesc')}</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen w-full pt-20 pb-12 bg-transparent">
        <div className="flex items-center justify-center min-h-[60vh] max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center space-y-4">
            <RefreshCw className="w-12 h-12 animate-spin text-primary-600 mx-auto" />
            <p className="text-academic-muted">{t('common.loading')}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full pt-20 pb-12 bg-transparent">
      <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold text-academic-text flex items-center gap-3">
            <LayoutDashboard className="w-8 h-8 text-primary-600" />
            {t('admin.title')}
          </h1>
          <p className="text-academic-muted mt-2">
            Last updated: {formatRelativeTime(lastUpdate, i18n.language)}
          </p>
        </div>
        <Button
          onClick={refreshMetrics}
          disabled={refreshing}
          variant="outline"
          className="flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          {t('admin.refreshMetrics')}
        </Button>
      </div>

      {/* Health Status Overview */}
      {health && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              {t('admin.healthChecks')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4 mb-4">
              <span className="text-lg font-semibold">{t('admin.overall')}</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(health.overall_status)}`}>
                {health.overall_status.toUpperCase()}
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(health.services).map(([service, status]) => (
                <div key={service} className="flex items-center gap-3 p-3 bg-parchment-50 rounded-lg">
                  {getStatusIcon(status)}
                  <div>
                    <p className="font-medium capitalize">{service.replace('_', ' ')}</p>
                    <p className="text-xs text-academic-muted capitalize">{status}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Database Statistics */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <Database className="w-10 h-10 text-blue-500 bg-blue-50 p-2 rounded-lg" />
                  <div>
                    <p className="text-sm text-academic-muted">{t('admin.kgNodes')}</p>
                    <p className="text-2xl font-bold">{formatNumber(stats.kg_nodes, i18n.language)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <Server className="w-10 h-10 text-green-500 bg-green-50 p-2 rounded-lg" />
                  <div>
                    <p className="text-sm text-academic-muted">{t('admin.kgEdges')}</p>
                    <p className="text-2xl font-bold">{formatNumber(stats.kg_edges, i18n.language)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <HardDrive className="w-10 h-10 text-purple-500 bg-purple-50 p-2 rounded-lg" />
                  <div>
                    <p className="text-sm text-academic-muted">{t('admin.ancientWorks')}</p>
                    <p className="text-2xl font-bold">{formatNumber(stats.ancient_works, i18n.language)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <Database className="w-10 h-10 text-orange-500 bg-orange-50 p-2 rounded-lg" />
                  <div>
                    <p className="text-sm text-academic-muted">{t('admin.passagesCount')}</p>
                    <p className="text-2xl font-bold">{formatNumber(stats.passages, i18n.language)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      )}

      {/* Data Quality Score */}
      {quality && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              {t('admin.dataQuality')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="relative w-32 h-32 mx-auto">
                  <svg className="w-full h-full" viewBox="0 0 100 100">
                    <circle
                      cx="50"
                      cy="50"
                      r="45"
                      fill="none"
                      stroke="#e5e7eb"
                      strokeWidth="10"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="45"
                      fill="none"
                      stroke={quality.health_score.overall_score >= 75 ? '#10b981' : quality.health_score.overall_score >= 50 ? '#f59e0b' : '#ef4444'}
                      strokeWidth="10"
                      strokeDasharray={`${quality.health_score.overall_score * 2.83} 283`}
                      strokeLinecap="round"
                      transform="rotate(-90 50 50)"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-3xl font-bold">{quality.health_score.overall_score}</span>
                  </div>
                </div>
                <p className="mt-2 font-medium">{t('admin.overallScore')}</p>
                <p className={`text-sm ${getStatusColor(quality.health_score.status)} px-2 py-1 rounded-full inline-block mt-1`}>
                  {quality.health_score.status}
                </p>
              </div>

              <div className="space-y-3">
                <h4 className="font-semibold">{t('admin.qualityIssues')}</h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">{t('admin.criticalIssues')}</span>
                    <span className="font-mono text-red-600">{quality.summary.critical_issues}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">{t('admin.warnings')}</span>
                    <span className="font-mono text-yellow-600">{quality.summary.warnings}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">{t('admin.totalIssues')}</span>
                    <span className="font-mono">{quality.summary.total_issues}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="font-semibold">{t('admin.componentScores')}</h4>
                <div className="space-y-2">
                  {quality.health_score.components && Object.entries(quality.health_score.components).map(([component, score]) => (
                    <div key={component}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="capitalize">{component.replace('_', ' ')}</span>
                        <span className="font-mono">{score}%</span>
                      </div>
                      <div className="w-full bg-amber-200/60 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${score >= 75 ? 'bg-green-500' : score >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
                          style={{ width: `${score}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Works by Language and Period */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>{t('admin.worksByLanguage')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {stats.works_by_language.map(item => (
                  <div key={item.language}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="capitalize">{item.language}</span>
                      <span className="font-mono">{item.count}</span>
                    </div>
                    <div className="w-full bg-amber-200/60 rounded-full h-2">
                      <div
                        className="h-2 rounded-full bg-primary-600"
                        style={{ width: `${(item.count / stats.ancient_works) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t('admin.worksByPeriod')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {stats.works_by_period.slice(0, 8).map(item => (
                  <div key={item.period}>
                    <div className="flex justify-between text-sm mb-1">
                      <span>{item.period}</span>
                      <span className="font-mono">{item.count}</span>
                    </div>
                    <div className="w-full bg-amber-200/60 rounded-full h-2">
                      <div
                        className="h-2 rounded-full bg-green-600"
                        style={{ width: `${(item.count / stats.ancient_works) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      </div>
    </div>
  );
};

export default AdminDashboard;
