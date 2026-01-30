import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import {
  Edit3,
  Send,
  CheckCircle,
  AlertCircle,
  FileText,
  Book,
  User
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { useAuth } from '../context/AuthContext';
import { AuroraBackground } from '../components/ui/aurora-background';

interface ContributionForm {
  targetType: 'kg_node' | 'passage' | 'work';
  targetId: string;
  changeType: 'correction' | 'addition' | 'removal';
  proposedChange: string;
  justification: string;
  sources: string;
  contactEmail: string;
}

const SubmitCorrectionPage: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<ContributionForm>({
    targetType: 'kg_node',
    targetId: '',
    changeType: 'correction',
    proposedChange: '',
    justification: '',
    sources: '',
    contactEmail: user?.email || ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    // Simulate submission (in real implementation, this would call an API)
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));

      // For now, just log the contribution
      console.log('Contribution submitted:', form);

      setSubmitted(true);
    } catch (_err) {
      setError('Failed to submit contribution. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof ContributionForm, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  if (submitted) {
    return (
      <AuroraBackground className="!min-h-screen !h-auto py-12">
      <div className="max-w-2xl mx-auto py-12 relative z-10">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="text-center"
        >
          <CheckCircle className="w-20 h-20 text-green-500 mx-auto mb-6" />
          <h1 className="text-3xl font-bold text-academic-text mb-4">
            {t('community.thankYou')}
          </h1>
          <p className="text-academic-muted text-lg mb-6">
            {t('community.pendingReview')}
          </p>
          <p className="text-sm text-academic-muted mb-8">
            {t('community.guidelinesIntro')}
          </p>
          <Button onClick={() => setSubmitted(false)} variant="outline">
            {t('community.submitAnother')}
          </Button>
        </motion.div>
      </div>
      </AuroraBackground>
    );
  }

  return (
    <AuroraBackground className="!min-h-screen !h-auto py-12">
    <div className="max-w-4xl mx-auto space-y-6 relative z-10">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-academic-text flex items-center gap-3">
          <Edit3 className="w-8 h-8 text-primary-600" />
          {t('community.submitCorrection')}
        </h1>
        <p className="text-academic-muted mt-2">
          {t('community.pageIntro')}
        </p>
      </div>

      {/* Guidelines */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-yellow-500" />
            {t('community.guidelinesTitle')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-academic-muted">
            <li className="flex items-start gap-2">
              <span className="text-primary-600 font-bold">1.</span>
              {t('community.guideline1')}
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary-600 font-bold">2.</span>
              {t('community.guideline2')}
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary-600 font-bold">3.</span>
              {t('community.guideline3')}
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary-600 font-bold">4.</span>
              {t('community.guideline4')}
            </li>
          </ul>
        </CardContent>
      </Card>

      {/* Contribution Form */}
      <Card>
        <CardHeader>
          <CardTitle>{t('community.contributionForm')}</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Target Type */}
            <div>
              <label className="block text-sm font-medium mb-2">
                {t('community.whatCorrecting')}
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { value: 'kg_node', label: t('community.kgNode'), icon: FileText },
                  { value: 'passage', label: t('community.ancientPassage'), icon: Book },
                  { value: 'work', label: t('community.workMetadata'), icon: User }
                ].map(option => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => handleInputChange('targetType', option.value)}
                    className={`p-4 border rounded-lg flex flex-col items-center gap-2 transition-colors ${
                      form.targetType === option.value
                        ? 'border-primary-600 bg-primary-50 text-primary-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <option.icon className="w-6 h-6" />
                    <span className="text-sm font-medium">{option.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Target ID */}
            <div>
              <label className="block text-sm font-medium mb-2">
                {t('community.nodeToEdit')} (ID or URL)
              </label>
              <input
                type="text"
                value={form.targetId}
                onChange={(e) => handleInputChange('targetId', e.target.value)}
                placeholder={t('community.targetIdPlaceholder')}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                required
              />
            </div>

            {/* Change Type */}
            <div>
              <label className="block text-sm font-medium mb-2">
                {t('community.changeType')}
              </label>
              <select
                value={form.changeType}
                onChange={(e) => handleInputChange('changeType', e.target.value)}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="correction">{t('community.correction')}</option>
                <option value="addition">{t('community.addition')}</option>
                <option value="removal">{t('community.removal')}</option>
              </select>
            </div>

            {/* Proposed Change */}
            <div>
              <label className="block text-sm font-medium mb-2">
                {t('community.proposedChange')}
              </label>
              <textarea
                value={form.proposedChange}
                onChange={(e) => handleInputChange('proposedChange', e.target.value)}
                placeholder={t('community.proposedChangeDesc')}
                rows={6}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                required
              />
            </div>

            {/* Justification */}
            <div>
              <label className="block text-sm font-medium mb-2">
                {t('community.justification')}
              </label>
              <textarea
                value={form.justification}
                onChange={(e) => handleInputChange('justification', e.target.value)}
                placeholder={t('community.justificationDesc')}
                rows={4}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                required
              />
            </div>

            {/* Supporting Sources */}
            <div>
              <label className="block text-sm font-medium mb-2">
                {t('community.sources')}
              </label>
              <textarea
                value={form.sources}
                onChange={(e) => handleInputChange('sources', e.target.value)}
                placeholder={t('community.sourcesPlaceholder')}
                rows={3}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                required
              />
              <p className="text-xs text-academic-muted mt-1">
                {t('community.sourcesHint')}
              </p>
            </div>

            {/* Contact Email */}
            <div>
              <label className="block text-sm font-medium mb-2">
                {t('community.contactEmail')}
              </label>
              <input
                type="email"
                value={form.contactEmail}
                onChange={(e) => handleInputChange('contactEmail', e.target.value)}
                placeholder={t('community.emailInputPlaceholder')}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                required
              />
              <p className="text-xs text-academic-muted mt-1">
                {t('community.emailHint')}
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 text-red-700 p-3 rounded-lg flex items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                {error}
              </div>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={submitting}
              className="w-full flex items-center justify-center gap-2"
            >
              {submitting ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  >
                    <Send className="w-5 h-5" />
                  </motion.div>
                  {t('community.submitting')}
                </>
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  {t('community.submit')}
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Attribution Notice */}
      <Card>
        <CardContent className="p-4">
          <p className="text-sm text-academic-muted">
            <strong>{t('community.noteTitle')}</strong> {t('community.noteText')}
          </p>
        </CardContent>
      </Card>
    </div>
    </AuroraBackground>
  );
};

export default SubmitCorrectionPage;
