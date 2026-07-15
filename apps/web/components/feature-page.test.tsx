import { render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import { describe, expect, it } from 'vitest';
import { AsyncState, FeaturePage } from './feature-page';

describe('FeaturePage', () => {
  it('renders one page heading and accessible content', async () => {
    const { container } = render(
      <FeaturePage title="Daily challenge" intro="One shared puzzle.">
        <button type="button">Begin</button>
      </FeaturePage>,
    );
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Daily challenge');
    expect(screen.getByRole('button', { name: 'Begin' })).toBeEnabled();
    expect((await axe(container)).violations).toEqual([]);
  });
});

describe('AsyncState', () => {
  it('announces loading and error states', () => {
    const { rerender } = render(
      <AsyncState
        state="loading"
        loadingLabel="Loading games"
        errorLabel="Could not load"
        emptyLabel="No games"
      />,
    );
    expect(screen.getByRole('status')).toHaveTextContent('Loading games');
    rerender(
      <AsyncState
        state="error"
        loadingLabel="Loading games"
        errorLabel="Could not load"
        emptyLabel="No games"
      />,
    );
    expect(screen.getByRole('alert')).toHaveTextContent('Could not load');
    rerender(
      <AsyncState
        state="empty"
        loadingLabel="Loading games"
        errorLabel="Could not load"
        emptyLabel="No games"
      />,
    );
    expect(screen.getByText('No games')).toBeInTheDocument();
    rerender(
      <AsyncState
        state="ready"
        loadingLabel="Loading games"
        errorLabel="Could not load"
        emptyLabel="No games"
      >
        <p>Ready content</p>
      </AsyncState>,
    );
    expect(screen.getByText('Ready content')).toBeInTheDocument();
  });
});
