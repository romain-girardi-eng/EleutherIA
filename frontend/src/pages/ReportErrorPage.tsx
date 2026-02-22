import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { GradientButton } from '../components/ui/gradient-button';
import { useToast } from '../components/ui/Toast';

type ErrorType =
  | 'philological'
  | 'bibliographic'
  | 'relationship'
  | 'metadata'
  | 'data_quality'
  | 'technical'
  | 'other';

export default function ReportErrorPage() {
  const { t } = useTranslation();
  const { showToast } = useToast();
  const [errorType, setErrorType] = useState<ErrorType>('philological');
  const [nodeId, setNodeId] = useState('');
  const [edgeInfo, setEdgeInfo] = useState('');
  const [description, setDescription] = useState('');
  const [suggestedCorrection, setSuggestedCorrection] = useState('');
  const [sources, setSources] = useState('');
  const [contactName, setContactName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactOrcid, setContactOrcid] = useState('');

  const errorTypeOptions = [
    { value: 'philological', label: t('reportError.errorTypes.philological'), description: 'Incorrect citation, misattribution, wrong Greek/Latin terminology' },
    { value: 'bibliographic', label: t('reportError.errorTypes.bibliographic'), description: 'Incorrect modern scholarship reference or citation' },
    { value: 'relationship', label: t('reportError.errorTypes.relationship'), description: 'Wrong or missing relationship between entities' },
    { value: 'metadata', label: t('reportError.errorTypes.metadata'), description: 'Wrong dates, periods, schools, or classifications' },
    { value: 'data_quality', label: 'Data Quality Issue', description: 'Duplicates, inconsistencies, or formatting issues' },
    { value: 'technical', label: t('reportError.errorTypes.technical'), description: 'Interface bugs, search problems, or performance issues' },
    { value: 'other', label: t('reportError.errorTypes.other'), description: 'Any other type of issue' },
  ];

  const generateReport = () => {
    const selectedOption = errorTypeOptions.find(opt => opt.value === errorType);

    return `# EleutherIA Error Report

## Error Type
${selectedOption?.label}

## Details
${nodeId ? `**Node/Entity ID**: ${nodeId}\n` : ''}${edgeInfo ? `**Edge/Relationship**: ${edgeInfo}\n` : ''}
**Description of Error**:
${description}

${suggestedCorrection ? `## Suggested Correction\n${suggestedCorrection}\n` : ''}
${sources ? `## Supporting Sources\n${sources}\n` : ''}
${contactName || contactEmail || contactOrcid ? `## Contact Information\n${contactName ? `Name: ${contactName}\n` : ''}${contactEmail ? `Email: ${contactEmail}\n` : ''}${contactOrcid ? `ORCID: ${contactOrcid}\n` : ''}` : ''}
---
*Generated via EleutherIA Error Report Form*
*Date: ${new Date().toISOString().split('T')[0]}*
`;
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(generateReport());
    showToast('Error report copied to clipboard! You can now paste it into a GitHub issue or email.', 'success');
  };

  const openGitHubIssue = () => {
    const title = encodeURIComponent(`[Error Report] ${errorTypeOptions.find(opt => opt.value === errorType)?.label}`);
    const body = encodeURIComponent(generateReport());
    window.open(`https://github.com/romain-girardi-eng/EleutherIA/issues/new?title=${title}&body=${body}`, '_blank');
  };

  const sendViaEmail = () => {
    const subject = encodeURIComponent(`EleutherIA Error Report: ${errorTypeOptions.find(opt => opt.value === errorType)?.label}`);
    const body = encodeURIComponent(generateReport());
    window.location.href = `mailto:romain.girardi@univ-cotedazur.fr?subject=${subject}&body=${body}`;
  };

  return (
    <div className="min-h-screen w-full pt-20 pb-12 bg-transparent">
      <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
      {/* Header */}
      <section className="academic-card">
        <h1 className="text-3xl font-serif font-display font-bold mb-4">{t('reportError.title')}</h1>
        <div className="prose max-w-none text-academic-text space-y-3">
          <p>
            {t('reportError.intro')}
          </p>
          <div className="bg-academic-bg p-4 rounded border-l-4 border-primary-600">
            <p className="text-sm mb-2"><strong>{t('reportError.howHandled')}</strong></p>
            <ul className="text-sm space-y-1 list-disc list-inside">
              <li>All reports are reviewed within the context of ancient sources and modern scholarship</li>
              <li>Accepted corrections are acknowledged in the project's change log</li>
              <li>Contributors may be cited in documentation if they wish</li>
              <li>Substantive corrections may result in co-authorship on future versions</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Error Report Form */}
      <section className="academic-card">
        <h2 className="text-2xl font-serif font-display font-bold mb-6">{t('reportError.errorDetails')}</h2>

        <div className="space-y-6">
          {/* Error Type */}
          <div>
            <label className="block text-sm font-semibold mb-2">{t('reportError.errorType')}</label>
            <div className="space-y-2">
              {errorTypeOptions.map((option) => (
                <label key={option.value} className="flex items-start cursor-pointer">
                  <input
                    type="radio"
                    name="errorType"
                    value={option.value}
                    checked={errorType === option.value}
                    onChange={(e) => setErrorType(e.target.value as ErrorType)}
                    className="mt-1 mr-3"
                  />
                  <div>
                    <div className="font-medium">{option.label}</div>
                    <div className="text-sm text-academic-muted">{option.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Node/Entity ID */}
          <div>
            <label htmlFor="nodeId" className="block text-sm font-semibold mb-2">
              {t('reportError.nodeId')}
            </label>
            <input
              id="nodeId"
              type="text"
              value={nodeId}
              onChange={(e) => setNodeId(e.target.value)}
              placeholder={t('reportError.nodeIdPlaceholder')}
              className="w-full px-4 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <p className="text-xs text-academic-muted mt-1">
              You can find IDs by exploring the Knowledge Graph or using the Search feature
            </p>
          </div>

          {/* Edge/Relationship */}
          <div>
            <label htmlFor="edgeInfo" className="block text-sm font-semibold mb-2">
              {t('reportError.edgeId')}
            </label>
            <input
              id="edgeInfo"
              type="text"
              value={edgeInfo}
              onChange={(e) => setEdgeInfo(e.target.value)}
              placeholder={t('reportError.edgeIdPlaceholder')}
              className="w-full px-4 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-semibold mb-2">
              {t('reportError.description')}
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={6}
              placeholder={t('reportError.descriptionPlaceholder')}
              className="w-full px-4 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
              required
            />
          </div>

          {/* Suggested Correction */}
          <div>
            <label htmlFor="suggestedCorrection" className="block text-sm font-semibold mb-2">
              {t('reportError.suggestedCorrection')}
            </label>
            <textarea
              id="suggestedCorrection"
              value={suggestedCorrection}
              onChange={(e) => setSuggestedCorrection(e.target.value)}
              rows={4}
              placeholder={t('reportError.correctionPlaceholder')}
              className="w-full px-4 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Supporting Sources */}
          <div>
            <label htmlFor="sources" className="block text-sm font-semibold mb-2">
              {t('reportError.supportingSources')}
            </label>
            <textarea
              id="sources"
              value={sources}
              onChange={(e) => setSources(e.target.value)}
              rows={4}
              placeholder={t('reportError.sourcesPlaceholder')}
              className="w-full px-4 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <p className="text-xs text-academic-muted mt-1">
              Academic citations strengthen your report and facilitate verification
            </p>
          </div>

          {/* Contact Information */}
          <div className="border-t border-academic-border pt-6">
            <h3 className="text-lg font-semibold mb-4">{t('reportError.contactInfo')}</h3>
            <p className="text-sm text-academic-muted mb-4">
              Providing your contact information allows us to follow up with questions and acknowledge your contribution.
            </p>

            <div className="space-y-4">
              <div>
                <label htmlFor="contactName" className="block text-sm font-semibold mb-2">
                  {t('reportError.name')}
                </label>
                <input
                  id="contactName"
                  type="text"
                  value={contactName}
                  onChange={(e) => setContactName(e.target.value)}
                  placeholder={t('reportError.namePlaceholder')}
                  className="w-full px-4 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label htmlFor="contactEmail" className="block text-sm font-semibold mb-2">
                  {t('reportError.email')}
                </label>
                <input
                  id="contactEmail"
                  type="email"
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                  placeholder={t('reportError.emailPlaceholder')}
                  className="w-full px-4 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label htmlFor="contactOrcid" className="block text-sm font-semibold mb-2">
                  {t('reportError.orcid')}
                </label>
                <input
                  id="contactOrcid"
                  type="text"
                  value={contactOrcid}
                  onChange={(e) => setContactOrcid(e.target.value)}
                  placeholder={t('reportError.orcidPlaceholder')}
                  className="w-full px-4 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Submission Options */}
      <section className="academic-card">
        <h2 className="text-2xl font-serif font-display font-bold mb-4">{t('reportError.submitReport')}</h2>
        <p className="text-sm text-academic-muted mb-6">
          Choose how you'd like to submit your error report:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <GradientButton
            onClick={openGitHubIssue}
            disabled={!description}
            variant="highlight"
            size="lg"
            className="flex flex-col items-center p-6 text-center h-auto"
          >
            <svg className="w-8 h-8 mb-2" fill="currentColor" viewBox="0 0 24 24">
              <path fillRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z" clipRule="evenodd" />
            </svg>
            <span className="font-semibold">{t('reportError.githubIssue')}</span>
            <span className="text-xs opacity-80 mt-1">{t('reportError.githubDesc')}</span>
          </GradientButton>

          <GradientButton
            onClick={sendViaEmail}
            disabled={!description}
            variant="academic"
            size="lg"
            className="flex flex-col items-center p-6 text-center h-auto"
          >
            <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <span className="font-semibold">{t('reportError.emailReport')}</span>
            <span className="text-xs opacity-80 mt-1">{t('reportError.emailDesc')}</span>
          </GradientButton>

          <GradientButton
            onClick={copyToClipboard}
            disabled={!description}
            variant="default"
            size="lg"
            className="flex flex-col items-center p-6 text-center h-auto"
          >
            <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
            </svg>
            <span className="font-semibold">{t('reportError.copyClipboard')}</span>
            <span className="text-xs opacity-80 mt-1">{t('reportError.copyDesc')}</span>
          </GradientButton>
        </div>
      </section>

      {/* Guidelines */}
      <section className="academic-card bg-academic-bg">
        <h2 className="text-xl font-serif font-display font-bold mb-4">{t('reportError.guidelines')}</h2>
        <div className="prose max-w-none text-sm space-y-3">
          <p><strong>{t('reportError.whatToReport')}</strong></p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>Factual errors in citations, dates, attributions</li>
            <li>Missing or incorrect relationships between entities</li>
            <li>Inconsistencies in terminology or translations</li>
            <li>Missing important sources or bibliography</li>
            <li>Technical issues affecting functionality</li>
          </ul>

          <p><strong>{t('reportError.whatNotToReport')}</strong></p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>Alternative interpretations (these are scholarly debates, not errors)</li>
            <li>Requests for new features</li>
            <li>Suggestions for scope expansion beyond 4th c. BCE - 6th c. CE</li>
          </ul>

          <p className="text-xs italic">
            For questions about interpretation or to discuss scholarly debates, please reach out directly via email
            or academic channels.
          </p>
        </div>
      </section>
      </div>
    </div>
  );
}
