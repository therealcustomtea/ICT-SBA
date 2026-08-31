// Imports the dependency used by this module.
import { render, screen } from '@testing-library/react';
// Imports the dependency used by this module.
import { axe } from 'jest-axe';
// Imports the dependency used by this module.
import { describe, expect, it } from 'vitest';
// Imports the dependency used by this module.
import { AsyncState, FeaturePage } from './feature-page';

// Calls describe with the supplied values.
describe('FeaturePage', () => {
  // Calls it with the supplied values.
  it('renders one page heading and accessible content', async () => {
    // Executes this line as the next step in the surrounding logic.
    const { container } = render(
      // Renders the FeaturePage interface element or component.
      <FeaturePage title="Daily challenge" intro="One shared puzzle.">
        {/* Renders the button interface element or component. */}
        <button type="button">Begin</button>
        {/* Closes the FeaturePage interface element. */}
      </FeaturePage>,
      // Closes the expression, call, or declaration started above.
    );
    // Calls expect with the supplied values.
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Daily challenge');
    // Calls expect with the supplied values.
    expect(screen.getByRole('button', { name: 'Begin' })).toBeEnabled();
    // Calls expect with the supplied values.
    expect((await axe(container)).violations).toEqual([]);
    // Closes the expression, call, or declaration started above.
  });
  // Closes the expression, call, or declaration started above.
});

// Calls describe with the supplied values.
describe('AsyncState', () => {
  // Calls it with the supplied values.
  it('announces loading and error states', () => {
    // Executes this line as the next step in the surrounding logic.
    const { rerender } = render(
      // Renders the AsyncState interface element or component.
      <AsyncState
        /* Provides the state value to the surrounding call or element. */
        state="loading"
        /* Provides the loadingLabel value to the surrounding call or element. */
        loadingLabel="Loading games"
        /* Provides the errorLabel value to the surrounding call or element. */
        errorLabel="Could not load"
        /* Provides the emptyLabel value to the surrounding call or element. */
        emptyLabel="No games"
        /* Supplies this item to the surrounding call or collection. */
      />,
      // Closes the expression, call, or declaration started above.
    );
    // Calls expect with the supplied values.
    expect(screen.getByRole('status')).toHaveTextContent('Loading games');
    // Calls rerender with the supplied values.
    rerender(
      // Renders the AsyncState interface element or component.
      <AsyncState
        /* Provides the state value to the surrounding call or element. */
        state="error"
        /* Provides the loadingLabel value to the surrounding call or element. */
        loadingLabel="Loading games"
        /* Provides the errorLabel value to the surrounding call or element. */
        errorLabel="Could not load"
        /* Provides the emptyLabel value to the surrounding call or element. */
        emptyLabel="No games"
        /* Supplies this item to the surrounding call or collection. */
      />,
      // Closes the expression, call, or declaration started above.
    );
    // Calls expect with the supplied values.
    expect(screen.getByRole('alert')).toHaveTextContent('Could not load');
    // Calls rerender with the supplied values.
    rerender(
      // Renders the AsyncState interface element or component.
      <AsyncState
        /* Provides the state value to the surrounding call or element. */
        state="empty"
        /* Provides the loadingLabel value to the surrounding call or element. */
        loadingLabel="Loading games"
        /* Provides the errorLabel value to the surrounding call or element. */
        errorLabel="Could not load"
        /* Provides the emptyLabel value to the surrounding call or element. */
        emptyLabel="No games"
        /* Supplies this item to the surrounding call or collection. */
      />,
      // Closes the expression, call, or declaration started above.
    );
    // Calls expect with the supplied values.
    expect(screen.getByText('No games')).toBeInTheDocument();
    // Calls rerender with the supplied values.
    rerender(
      // Renders the AsyncState interface element or component.
      <AsyncState
        /* Provides the state value to the surrounding call or element. */
        state="ready"
        /* Provides the loadingLabel value to the surrounding call or element. */
        loadingLabel="Loading games"
        /* Provides the errorLabel value to the surrounding call or element. */
        errorLabel="Could not load"
        /* Provides the emptyLabel value to the surrounding call or element. */
        emptyLabel="No games"
        /* Closes the expression, call, or declaration started above. */
      >
        {/* Renders the p interface element or component. */}
        <p>Ready content</p>
        {/* Closes the AsyncState interface element. */}
      </AsyncState>,
      // Closes the expression, call, or declaration started above.
    );
    // Calls expect with the supplied values.
    expect(screen.getByText('Ready content')).toBeInTheDocument();
    // Closes the expression, call, or declaration started above.
  });
  // Closes the expression, call, or declaration started above.
});
