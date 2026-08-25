import { useState } from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { I18nextProvider } from 'react-i18next';
import { beforeAll, describe, expect, it, vi } from 'vitest';
import i18n from '../../i18n/config';
import ChatInput, { type GraphRagModelOption } from './ChatInput';

const OPTIONS: GraphRagModelOption[] = [
  { key: 'gpt-5.6-sol', label: 'GPT-5.6 Sol', provider: 'codex', available: true },
  { key: 'claude-opus-5', label: 'Claude Opus 5', provider: 'claude', available: true },
  { key: 'gemini-3.1-pro', label: 'Gemini 3.1 Pro', provider: 'gemini', available: true },
  {
    key: 'gemini-3.7-flash-high',
    label: 'Gemini 3.7 Flash High',
    provider: 'gemini',
    available: true,
  },
  { key: 'unavailable', label: 'Unavailable', provider: 'gemini', available: false },
];

beforeAll(async () => {
  Element.prototype.hasPointerCapture = vi.fn(() => false);
  Element.prototype.setPointerCapture = vi.fn();
  Element.prototype.releasePointerCapture = vi.fn();
  Element.prototype.scrollIntoView = vi.fn();
  await i18n.changeLanguage('en');
});

function Harness() {
  const [model, setModel] = useState('auto');
  return (
    <I18nextProvider i18n={i18n}>
      <ChatInput
        query=""
        setQuery={vi.fn()}
        streaming={false}
        canSubmit
        maxConcurrentRuns={3}
        inputRef={{ current: null }}
        onSubmit={vi.fn()}
        onStop={vi.fn()}
        selectedModel={model}
        modelOptions={OPTIONS}
        onModelChange={setModel}
      />
    </I18nextProvider>
  );
}

describe('ChatInput model selector', () => {
  it('defaults to Auto and lets the user pin all stages to Gemini', async () => {
    const user = userEvent.setup();
    render(<Harness />);

    const trigger = screen.getByRole('combobox', {
      name: 'Choose the model for new questions',
    });
    expect(trigger).toHaveTextContent('Auto');

    await user.click(trigger);
    expect(screen.queryByText('Unavailable')).not.toBeInTheDocument();
    expect(screen.getByRole('option', { name: /Gemini 3.7 Flash High/i })).toBeVisible();
    await user.click(screen.getByRole('option', { name: /Gemini 3.1 Pro/i }));

    expect(trigger).toHaveTextContent('Gemini 3.1 Pro');
  });
});
