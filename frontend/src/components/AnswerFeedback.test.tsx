import { createRef } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { I18nextProvider } from 'react-i18next';
import i18n from '../i18n/config';
import {
  getMyAnswerFeedback,
  submitAnswerFeedback,
  submitAnswerReport,
} from '../api/feedback';
import AnswerFeedback from './AnswerFeedback';
import { ToastProvider } from './ui/Toast';

vi.mock('../api/feedback', () => ({
  getMyAnswerFeedback: vi.fn(),
  submitAnswerFeedback: vi.fn(),
  submitAnswerReport: vi.fn(),
}));

const TRACE_ID = 'bbbbbbbb-0000-0000-0000-000000000001';

function renderFeedback() {
  const answerRef = createRef<HTMLDivElement>();
  const rendered = render(
    <I18nextProvider i18n={i18n}>
      <ToastProvider>
        <div ref={answerRef} data-testid="answer-copy">
          Chrysippus compares causal motion to a rolling cylinder.
        </div>
        <AnswerFeedback
          traceId={TRACE_ID}
          model="kimi-k2.6"
          answerContainerRef={answerRef}
        />
      </ToastProvider>
    </I18nextProvider>,
  );
  return { ...rendered, answerRef };
}

describe('AnswerFeedback', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    await i18n.changeLanguage('en');
    vi.mocked(getMyAnswerFeedback).mockResolvedValue({
      trace_id: TRACE_ID,
      rating: null,
      comment: null,
    });
    vi.mocked(submitAnswerFeedback).mockResolvedValue({
      id: 'feedback-1',
      trace_id: TRACE_ID,
      rating: 4,
      comment: null,
      report_type: null,
      report_text: null,
      answer_excerpt: null,
      app_commit: null,
      model: 'kimi-k2.6',
      created_at: '2026-08-17T10:00:00Z',
    });
    vi.mocked(submitAnswerReport).mockResolvedValue({
      id: 'report-1',
      trace_id: TRACE_ID,
      rating: null,
      comment: null,
      report_type: 'wrong_citation',
      report_text: 'The citation points to the wrong passage.',
      answer_excerpt: 'Chrysippus compares causal motion',
      app_commit: null,
      model: 'kimi-k2.6',
      created_at: '2026-08-17T10:00:01Z',
    });
  });

  it('loads and displays the user’s existing rating', async () => {
    vi.mocked(getMyAnswerFeedback).mockResolvedValue({
      trace_id: TRACE_ID,
      rating: 3,
      comment: null,
    });
    renderFeedback();

    const thirdStar = await screen.findByRole('button', { name: '3 out of 5' });
    await waitFor(() => expect(thirdStar).not.toBeDisabled());
    expect(thirdStar).toHaveAttribute('aria-pressed', 'true');
    expect(getMyAnswerFeedback).toHaveBeenCalledWith(TRACE_ID, expect.any(AbortSignal));
  });

  it('submits a one-tap rating optimistically, then invites a longer impression', async () => {
    const user = userEvent.setup();
    renderFeedback();
    const fourthStar = await screen.findByRole('button', { name: '4 out of 5' });
    await waitFor(() => expect(fourthStar).not.toBeDisabled());

    await user.click(fourthStar);

    expect(fourthStar).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText('What felt right, weak, or missing?')).toBeInTheDocument();
    expect(submitAnswerFeedback).toHaveBeenCalledWith(
      expect.objectContaining({
        trace_id: TRACE_ID,
        rating: 4,
        model: 'kimi-k2.6',
      }),
    );

    await user.type(screen.getByLabelText('Your impression'), 'The sources are precise.');
    await user.click(screen.getByRole('button', { name: 'Send my impression' }));
    expect(submitAnswerFeedback).toHaveBeenLastCalledWith(
      expect.objectContaining({
        trace_id: TRACE_ID,
        comment: 'The sources are precise.',
      }),
    );
  });

  it('attaches selected answer text to a typed report', async () => {
    const user = userEvent.setup();
    renderFeedback();
    await waitFor(() =>
      expect(screen.getByRole('button', { name: '1 out of 5' })).not.toBeDisabled(),
    );

    const answer = screen.getByTestId('answer-copy');
    const textNode = answer.firstChild;
    if (!textNode) throw new Error('answer text node missing');
    const range = document.createRange();
    range.setStart(textNode, 0);
    range.setEnd(textNode, 34);
    const selection = window.getSelection();
    selection?.removeAllRanges();
    selection?.addRange(range);

    await user.click(
      screen.getByRole('button', {
        name: 'Report an error / suggest an improvement',
      }),
    );

    expect(screen.getByText('Selected excerpt')).toBeInTheDocument();
    expect(screen.getByText('Chrysippus compares causal motion')).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText('Report type'), 'wrong_citation');
    await user.type(
      screen.getByLabelText('Details'),
      'The citation points to the wrong passage.',
    );
    await user.click(screen.getByRole('button', { name: 'Send report' }));

    expect(submitAnswerReport).toHaveBeenCalledWith(
      expect.objectContaining({
        trace_id: TRACE_ID,
        report_type: 'wrong_citation',
        report_text: 'The citation points to the wrong passage.',
        answer_excerpt: 'Chrysippus compares causal motion',
        model: 'kimi-k2.6',
      }),
    );
  });
});
