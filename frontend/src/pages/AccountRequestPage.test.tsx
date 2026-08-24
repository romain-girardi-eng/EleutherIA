import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { I18nextProvider } from 'react-i18next';
import { MemoryRouter } from 'react-router-dom';
import i18n from '../i18n/config';
import AccountRequestPage from './AccountRequestPage';
import { apiClient } from '../api/client';

vi.mock('../api/client', () => ({
  apiClient: {
    requestAccount: vi.fn(),
  },
}));

function renderPage() {
  return render(
    <I18nextProvider i18n={i18n}>
      <MemoryRouter initialEntries={['/request-account']}>
        <AccountRequestPage />
      </MemoryRouter>
    </I18nextProvider>,
  );
}

describe('AccountRequestPage', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    await i18n.changeLanguage('en');
    vi.mocked(apiClient.requestAccount).mockResolvedValue({
      message: 'Your account request has been received.',
      request_id: 'EAR-TEST123',
    });
  });

  it('collects only the scoped request data across three steps', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText(/Full name/), 'Ada Researcher');
    await user.type(screen.getByLabelText(/Email address/), 'ada@example.org');
    await user.type(screen.getByLabelText(/Institution or affiliation/), 'Ancient Studies Lab');
    await user.selectOptions(screen.getByLabelText(/Current role/), 'researcher');
    await user.click(screen.getByRole('button', { name: 'Continue' }));

    await user.type(
      await screen.findByLabelText(/Research context and intended project/),
      'I compare Stoic and early Christian accounts of responsible agency.',
    );
    await user.click(screen.getByLabelText('Academic research'));
    await user.click(screen.getByRole('button', { name: 'Continue' }));

    expect(
      await screen.findByText('Full privacy information (GDPR Article 13)'),
    ).toBeInTheDocument();
    await user.click(
      screen.getByLabelText(/I have read the privacy information above/),
    );
    await user.click(screen.getByRole('button', { name: 'Send request' }));

    await waitFor(() => expect(apiClient.requestAccount).toHaveBeenCalledTimes(1));
    expect(apiClient.requestAccount).toHaveBeenCalledWith({
      full_name: 'Ada Researcher',
      email: 'ada@example.org',
      affiliation: 'Ancient Studies Lab',
      role: 'researcher',
      research_focus: 'I compare Stoic and early Christian accounts of responsible agency.',
      intended_use: ['research'],
      privacy_acknowledged: true,
      privacy_notice_version: '2026-08-24',
      locale: 'en',
      website: '',
    });
    expect(
      await screen.findByText('Your request has entered the review queue.'),
    ).toBeInTheDocument();
    expect(screen.getByText('Reference EAR-TEST123')).toBeInTheDocument();
  });

  it('keeps the applicant on the first step until required identity fields are valid', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: 'Continue' }));

    expect(screen.getByText('Enter your full name.')).toBeInTheDocument();
    expect(screen.getByText('Enter a valid email address.')).toBeInTheDocument();
    expect(screen.getByText('Select the role that best matches you.')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Who should we welcome?' })).toBeInTheDocument();
  });
});
