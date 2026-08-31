// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { useTranslations } from 'next-intl';
// Imports the dependency used by this module.
import { useRef, useState } from 'react';
// Imports the dependency used by this module.
import { useRouter } from '@/i18n/navigation';
// Imports the dependency used by this module.
import { type Game, useApi } from '@/lib/api';
// Imports the dependency used by this module.
import { gameDifficulty, gameMode } from '@/lib/analytics-delivery';
// Imports the dependency used by this module.
import { useProductAnalytics } from '@/lib/use-product-analytics';

// Computes and stores colourIds for subsequent operations.
const colourIds = ['R', 'B', 'G', 'Y', 'W', 'K', 'O', 'P', 'C', 'M'] as const;
// Computes and stores symbols for subsequent operations.
const symbols: Record<string, string> = {
  // Defines the R field in the surrounding object or type.
  R: '●',
  // Defines the B field in the surrounding object or type.
  B: '◆',
  // Defines the G field in the surrounding object or type.
  G: '▲',
  // Defines the Y field in the surrounding object or type.
  Y: '■',
  // Defines the W field in the surrounding object or type.
  W: '○',
  // Defines the K field in the surrounding object or type.
  K: '✚',
  // Defines the O field in the surrounding object or type.
  O: '⬟',
  // Defines the P field in the surrounding object or type.
  P: '✦',
  // Defines the C field in the surrounding object or type.
  C: '⬢',
  // Defines the M field in the surrounding object or type.
  M: '♥',
  // Closes the expression, call, or declaration started above.
};
// Computes and stores presets for subsequent operations.
const presets = {
  // Defines the easy field in the surrounding object or type.
  easy: { colourCount: 5, codeLength: 4, maxAttempts: 12, duplicatesAllowed: false },
  // Defines the normal field in the surrounding object or type.
  normal: { colourCount: 6, codeLength: 4, maxAttempts: 10, duplicatesAllowed: true },
  // Defines the hard field in the surrounding object or type.
  hard: { colourCount: 8, codeLength: 5, maxAttempts: 8, duplicatesAllowed: true },
  // Defines the expert field in the surrounding object or type.
  expert: { colourCount: 10, codeLength: 6, maxAttempts: 8, duplicatesAllowed: true },
  // Executes this line as the next step in the surrounding logic.
} as const;

// Declares the Difficulty data shape or implementation.
type Difficulty = keyof typeof presets | 'custom';
// Declares the Mode data shape or implementation.
type Mode = 'solo' | 'practice' | 'pass_and_play';

// Exports this declaration for use by other modules.
export function SetupForm() {
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Play');
  // Computes and stores tg for subsequent operations.
  const tg = useTranslations('Game');
  // Computes and stores tc for subsequent operations.
  const tc = useTranslations('Common');
  // Computes and stores api for subsequent operations.
  const api = useApi();
  // Computes and stores analytics for subsequent operations.
  const analytics = useProductAnalytics();
  // Computes and stores router for subsequent operations.
  const router = useRouter();
  // Executes this line as the next step in the surrounding logic.
  const [mode, setMode] = useState<Mode>('solo');
  // Executes this line as the next step in the surrounding logic.
  const [difficulty, setDifficulty] = useState<Difficulty>('normal');
  // Executes this line as the next step in the surrounding logic.
  const [colourCount, setColourCount] = useState(6);
  // Executes this line as the next step in the surrounding logic.
  const [codeLength, setCodeLength] = useState(4);
  // Executes this line as the next step in the surrounding logic.
  const [maxAttempts, setMaxAttempts] = useState(10);
  // Executes this line as the next step in the surrounding logic.
  const [duplicatesAllowed, setDuplicatesAllowed] = useState(true);
  // Executes this line as the next step in the surrounding logic.
  const [visibility, setVisibility] = useState<'private' | 'shareable'>('private');
  // Executes this line as the next step in the surrounding logic.
  const [secret, setSecret] = useState<string[]>([]);
  // Executes this line as the next step in the surrounding logic.
  const [passAndPlayPhase, setPassAndPlayPhase] = useState<'entry' | 'handover'>('entry');
  // Executes this line as the next step in the surrounding logic.
  const [submitting, setSubmitting] = useState(false);
  // Executes this line as the next step in the surrounding logic.
  const [error, setError] = useState<string | null>(null);
  // Computes and stores confirmedSecretRef for subsequent operations.
  const confirmedSecretRef = useRef<string[] | null>(null);
  // Computes and stores creationKeyRef for subsequent operations.
  const creationKeyRef = useRef<string | null>(null);

  // Computes and stores selectedRules for subsequent operations.
  const selectedRules =
    // Provides the difficulty value to the surrounding call or element.
    difficulty === 'custom'
      ? // Continues the surrounding operation with this required value or expression.
        // Executes this line as the next step in the surrounding logic.
        { colourCount, codeLength, maxAttempts, duplicatesAllowed }
      : // Continues the surrounding operation with this required value or expression.
        // Executes this line as the next step in the surrounding logic.
        presets[difficulty];
  // Computes and stores activeColours for subsequent operations.
  const activeColours = colourIds.slice(0, selectedRules.colourCount);
  // Computes and stores invalid for subsequent operations.
  const invalid =
    // Executes this line as the next step in the surrounding logic.
    !selectedRules.duplicatesAllowed && selectedRules.colourCount < selectedRules.codeLength;

  // Computes and stores chooseSecretPeg for subsequent operations.
  const chooseSecretPeg = (colour: string) => {
    // Calls setSecret with the supplied values.
    setSecret((current) => {
      // Checks this condition before running the nested branch.
      if (!selectedRules.duplicatesAllowed && current.includes(colour)) return current;
      // Returns this result to the caller and ends the current function.
      return [...current, colour].slice(0, selectedRules.codeLength);
      // Closes the expression, call, or declaration started above.
    });
    // Closes the expression, call, or declaration started above.
  };

  // Computes and stores resetSecret for subsequent operations.
  const resetSecret = () => {
    // Calls setSecret with the supplied values.
    setSecret([]);
    // Calls setPassAndPlayPhase with the supplied values.
    setPassAndPlayPhase('entry');
    // Executes this line as the next step in the surrounding logic.
    confirmedSecretRef.current = null;
    // Executes this line as the next step in the surrounding logic.
    creationKeyRef.current = null;
    // Closes the expression, call, or declaration started above.
  };

  // Computes and stores createGame for subsequent operations.
  const createGame = async (event: React.FormEvent<HTMLFormElement>) => {
    // Calls event.preventDefault with the supplied values.
    event.preventDefault();
    // Checks this condition before running the nested branch.
    if (
      // Executes this line as the next step in the surrounding logic.
      invalid ||
      // Executes this line as the next step in the surrounding logic.
      (mode === 'pass_and_play' &&
        // Provides the passAndPlayPhase value to the surrounding call or element.
        passAndPlayPhase === 'entry' &&
        // Executes this line as the next step in the surrounding logic.
        secret.length !== selectedRules.codeLength)
      // Closes the expression, call, or declaration started above.
    )
      // Returns this result to the caller and ends the current function.
      return;
    // Checks this condition before running the nested branch.
    if (mode === 'pass_and_play' && passAndPlayPhase === 'entry') {
      // Executes this line as the next step in the surrounding logic.
      confirmedSecretRef.current = [...secret];
      // Calls setSecret with the supplied values.
      setSecret([]);
      // Calls setPassAndPlayPhase with the supplied values.
      setPassAndPlayPhase('handover');
      // Calls setError with the supplied values.
      setError(null);
      // Returns this result to the caller and ends the current function.
      return;
      // Closes the expression, call, or declaration started above.
    }
    // Calls setSubmitting with the supplied values.
    setSubmitting(true);
    // Calls setError with the supplied values.
    setError(null);
    // Executes this line as the next step in the surrounding logic.
    creationKeyRef.current ??= crypto.randomUUID();
    // Computes and stores needsConfig for subsequent operations.
    const needsConfig = difficulty === 'custom' || mode === 'pass_and_play';
    // Computes and stores body for subsequent operations.
    const body: Record<string, unknown> = {
      // Supplies this item to the surrounding call or collection.
      mode,
      // Defines the idempotencyKey field in the surrounding object or type.
      idempotencyKey: creationKeyRef.current,
      // Executes this line as the next step in the surrounding logic.
      ...(needsConfig
        ? // Continues the surrounding operation with this required value or expression.
          // Begins the nested block or object completed below.
          {
            // Defines the config field in the surrounding object or type.
            config: {
              // Defines the colours field in the surrounding object or type.
              colours: [...activeColours],
              // Defines the codeLength field in the surrounding object or type.
              codeLength: selectedRules.codeLength,
              // Defines the maxAttempts field in the surrounding object or type.
              maxAttempts: selectedRules.maxAttempts,
              // Defines the duplicatesAllowed field in the surrounding object or type.
              duplicatesAllowed: selectedRules.duplicatesAllowed,
              // Defines the codeMaker field in the surrounding object or type.
              codeMaker: mode === 'pass_and_play' ? 'human' : 'computer',
              // Supplies this item to the surrounding call or collection.
              visibility,
              // Defines the ranked field in the surrounding object or type.
              ranked: false,
              // Defines the timeBonusCap field in the surrounding object or type.
              timeBonusCap: 300,
              // Closes the expression, call, or declaration started above.
            },
            // Closes the expression, call, or declaration started above.
          }
        : // Continues the surrounding operation with this required value or expression.
          // Supplies this item to the surrounding call or collection.
          { difficulty }),
      // Supplies this item to the surrounding call or collection.
      ...(mode === 'pass_and_play' ? { secret: confirmedSecretRef.current } : {}),
      // Closes the expression, call, or declaration started above.
    };
    // Starts an operation whose expected failures are handled below.
    try {
      // Computes and stores game for subsequent operations.
      const game = await api<Game>('/v1/games', { method: 'POST', body: JSON.stringify(body) });
      // Calls resetSecret with the supplied values.
      resetSecret();
      // Calls analytics with the supplied values.
      analytics('game_started', {
        // Defines the mode field in the surrounding object or type.
        mode: gameMode(game.mode),
        // Defines the difficulty field in the surrounding object or type.
        difficulty: gameDifficulty(game.difficulty),
        // Closes the expression, call, or declaration started above.
      });
      // Calls router.push with the supplied values.
      router.push(`/play/${game.id}`);
      // Handles a failure from the protected operation.
    } catch {
      // Calls setError with the supplied values.
      setError(t('createError'));
      // Calls setSubmitting with the supplied values.
      setSubmitting(false);
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Returns this result to the caller and ends the current function.
  return (
    // Renders the form interface element or component.
    <form className="setup-form" onSubmit={(event) => void createGame(event)}>
      {/* Renders the fieldset interface element or component. */}
      <fieldset className="choice-group">
        {/* Renders the legend interface element or component. */}
        <legend>{t('mode')}</legend>
        {/* Renders the div interface element or component. */}
        <div className="segmented-options">
          {/* Executes this line as the next step in the surrounding logic. */}
          {(['solo', 'practice', 'pass_and_play'] as const).map((value) => (
            // Renders the label interface element or component.
            <label key={value}>
              {/* Renders the input interface element or component. */}
              <input
                /* Provides the type value to the surrounding call or element. */
                type="radio"
                /* Provides the name value to the surrounding call or element. */
                name="mode"
                /* Provides the value value to the surrounding call or element. */
                value={value}
                /* Provides the checked value to the surrounding call or element. */
                checked={mode === value}
                /* Provides the onChange value to the surrounding call or element. */
                onChange={() => {
                  // Calls setMode with the supplied values.
                  setMode(value);
                  // Calls resetSecret with the supplied values.
                  resetSecret();
                  // Closes the expression, call, or declaration started above.
                }}
                /* Executes this line as the next step in the surrounding logic. */
              />
              {/* Renders the span interface element or component. */}
              <span>{value === 'pass_and_play' ? t('human') : t(value)}</span>
              {/* Closes the label interface element. */}
            </label>
            // Closes the expression, call, or declaration started above.
          ))}
          {/* Closes the div interface element. */}
        </div>
        {/* Closes the fieldset interface element. */}
      </fieldset>

      {/* Renders the fieldset interface element or component. */}
      <fieldset className="choice-group">
        {/* Renders the legend interface element or component. */}
        <legend>{t('difficulty')}</legend>
        {/* Renders the div interface element or component. */}
        <div className="difficulty-options">
          {/* Executes this line as the next step in the surrounding logic. */}
          {(['easy', 'normal', 'hard', 'expert', 'custom'] as const).map((value) => (
            // Renders the label interface element or component.
            <label key={value} className="difficulty-option">
              {/* Renders the input interface element or component. */}
              <input
                /* Provides the type value to the surrounding call or element. */
                type="radio"
                /* Provides the name value to the surrounding call or element. */
                name="difficulty"
                /* Provides the value value to the surrounding call or element. */
                value={value}
                /* Provides the checked value to the surrounding call or element. */
                checked={difficulty === value}
                /* Provides the onChange value to the surrounding call or element. */
                onChange={() => {
                  // Calls setDifficulty with the supplied values.
                  setDifficulty(value);
                  // Calls resetSecret with the supplied values.
                  resetSecret();
                  // Calls analytics with the supplied values.
                  analytics('difficulty_selected', { difficulty: value });
                  // Closes the expression, call, or declaration started above.
                }}
                /* Executes this line as the next step in the surrounding logic. */
              />
              {/* Renders the span interface element or component. */}
              <span>
                {/* Renders the strong interface element or component. */}
                <strong>{t(value)}</strong>
                {/* Renders the small interface element or component. */}
                <small>{t(`${value}Detail`)}</small>
                {/* Closes the span interface element. */}
              </span>
              {/* Closes the label interface element. */}
            </label>
            // Closes the expression, call, or declaration started above.
          ))}
          {/* Closes the div interface element. */}
        </div>
        {/* Closes the fieldset interface element. */}
      </fieldset>

      {/* Executes this line as the next step in the surrounding logic. */}
      {difficulty === 'custom' ? (
        // Renders the div interface element or component.
        <div className="form-grid panel">
          {/* Renders the label interface element or component. */}
          <label>
            {/* Executes this line as the next step in the surrounding logic. */}
            {t('colours')}
            {/* Renders the input interface element or component. */}
            <input
              /* Provides the type value to the surrounding call or element. */
              type="number"
              /* Provides the name value to the surrounding call or element. */
              name="colour-count"
              /* Provides the inputMode value to the surrounding call or element. */
              inputMode="numeric"
              /* Provides the autoComplete value to the surrounding call or element. */
              autoComplete="off"
              /* Provides the min value to the surrounding call or element. */
              min="5"
              /* Provides the max value to the surrounding call or element. */
              max="10"
              /* Provides the value value to the surrounding call or element. */
              value={colourCount}
              /* Provides the onChange value to the surrounding call or element. */
              onChange={(event) => {
                // Calls setColourCount with the supplied values.
                setColourCount(Number(event.target.value));
                // Calls resetSecret with the supplied values.
                resetSecret();
                // Closes the expression, call, or declaration started above.
              }}
              /* Executes this line as the next step in the surrounding logic. */
            />
            {/* Closes the label interface element. */}
          </label>
          {/* Renders the label interface element or component. */}
          <label>
            {/* Executes this line as the next step in the surrounding logic. */}
            {t('codeLength')}
            {/* Renders the input interface element or component. */}
            <input
              /* Provides the type value to the surrounding call or element. */
              type="number"
              /* Provides the name value to the surrounding call or element. */
              name="code-length"
              /* Provides the inputMode value to the surrounding call or element. */
              inputMode="numeric"
              /* Provides the autoComplete value to the surrounding call or element. */
              autoComplete="off"
              /* Provides the min value to the surrounding call or element. */
              min="3"
              /* Provides the max value to the surrounding call or element. */
              max="6"
              /* Provides the value value to the surrounding call or element. */
              value={codeLength}
              /* Provides the onChange value to the surrounding call or element. */
              onChange={(event) => {
                // Calls setCodeLength with the supplied values.
                setCodeLength(Number(event.target.value));
                // Calls resetSecret with the supplied values.
                resetSecret();
                // Closes the expression, call, or declaration started above.
              }}
              /* Executes this line as the next step in the surrounding logic. */
            />
            {/* Closes the label interface element. */}
          </label>
          {/* Renders the label interface element or component. */}
          <label>
            {/* Executes this line as the next step in the surrounding logic. */}
            {t('maximumAttempts')}
            {/* Renders the input interface element or component. */}
            <input
              /* Provides the type value to the surrounding call or element. */
              type="number"
              /* Provides the name value to the surrounding call or element. */
              name="maximum-attempts"
              /* Provides the inputMode value to the surrounding call or element. */
              inputMode="numeric"
              /* Provides the autoComplete value to the surrounding call or element. */
              autoComplete="off"
              /* Provides the min value to the surrounding call or element. */
              min="1"
              /* Provides the max value to the surrounding call or element. */
              max="20"
              /* Provides the value value to the surrounding call or element. */
              value={maxAttempts}
              /* Provides the onChange value to the surrounding call or element. */
              onChange={(event) => setMaxAttempts(Number(event.target.value))}
              /* Executes this line as the next step in the surrounding logic. */
            />
            {/* Closes the label interface element. */}
          </label>
          {/* Renders the label interface element or component. */}
          <label className="check-row">
            {/* Renders the input interface element or component. */}
            <input
              /* Provides the type value to the surrounding call or element. */
              type="checkbox"
              /* Provides the name value to the surrounding call or element. */
              name="duplicates-allowed"
              /* Provides the checked value to the surrounding call or element. */
              checked={duplicatesAllowed}
              /* Provides the onChange value to the surrounding call or element. */
              onChange={(event) => {
                // Calls setDuplicatesAllowed with the supplied values.
                setDuplicatesAllowed(event.target.checked);
                // Calls resetSecret with the supplied values.
                resetSecret();
                // Closes the expression, call, or declaration started above.
              }}
              /* Executes this line as the next step in the surrounding logic. */
            />
            {/* Renders the span interface element or component. */}
            <span>{t('duplicates')}</span>
            {/* Closes the label interface element. */}
          </label>
          {/* Renders the label interface element or component. */}
          <label>
            {/* Executes this line as the next step in the surrounding logic. */}
            {t('visibility')}
            {/* Renders the select interface element or component. */}
            <select
              /* Provides the name value to the surrounding call or element. */
              name="visibility"
              /* Provides the autoComplete value to the surrounding call or element. */
              autoComplete="off"
              /* Provides the value value to the surrounding call or element. */
              value={visibility}
              /* Provides the onChange value to the surrounding call or element. */
              onChange={(event) => setVisibility(event.target.value as 'private' | 'shareable')}
              /* Closes the expression, call, or declaration started above. */
            >
              {/* Renders the option interface element or component. */}
              <option value="private">{tc('private')}</option>
              {/* Renders the option interface element or component. */}
              <option value="shareable">{tc('shareable')}</option>
              {/* Closes the select interface element. */}
            </select>
            {/* Closes the label interface element. */}
          </label>
          {/* Executes this line as the next step in the surrounding logic. */}
          {invalid ? (
            // Renders the p interface element or component.
            <p className="inline-error" role="alert">
              {/* Executes this line as the next step in the surrounding logic. */}
              {t('invalidCustom')}
              {/* Closes the p interface element. */}
            </p>
          ) : // Continues the surrounding operation with this required value or expression.
          // Executes this line as the next step in the surrounding logic.
          null}
          {/* Closes the div interface element. */}
        </div>
      ) : // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      null}

      {/* Executes this line as the next step in the surrounding logic. */}
      {mode === 'pass_and_play' && passAndPlayPhase === 'entry' ? (
        // Renders the fieldset interface element or component.
        <fieldset className="secret-picker panel">
          {/* Renders the legend interface element or component. */}
          <legend>{t('secret')}</legend>
          {/* Renders the p interface element or component. */}
          <p>{t('secretHelp')}</p>
          {/* Renders the div interface element or component. */}
          <div className="secret-row concealed-secret" role="group" aria-label={t('secret')}>
            {/* Begins the nested block or object completed below. */}
            {Array.from({ length: selectedRules.codeLength }, (_, index) => {
              // Computes and stores colour for subsequent operations.
              const colour = secret[index];
              // Returns this result to the caller and ends the current function.
              return (
                // Renders the span interface element or component.
                <span
                  /* Provides the key value to the surrounding call or element. */
                  key={index}
                  /* Provides the className value to the surrounding call or element. */
                  className="peg slot"
                  /* Provides the role value to the surrounding call or element. */
                  role="img"
                  /* Begins the nested block or object completed below. */
                  aria-label={
                    // Executes this line as the next step in the surrounding logic.
                    colour
                      ? /* Continues the surrounding operation with this required value or expression. */
                        // Executes this line as the next step in the surrounding logic.
                        t('secretPositionFilled', { position: index + 1 })
                      : /* Continues the surrounding operation with this required value or expression. */
                        // Executes this line as the next step in the surrounding logic.
                        t('secretPositionEmpty', { position: index + 1 })
                    // Closes the expression, call, or declaration started above.
                  }
                  /* Closes the expression, call, or declaration started above. */
                >
                  {/* Executes this line as the next step in the surrounding logic. */}
                  {colour ? '●' : index + 1}
                  {/* Closes the span interface element. */}
                </span>
                // Closes the expression, call, or declaration started above.
              );
              // Closes the expression, call, or declaration started above.
            })}
            {/* Closes the div interface element. */}
          </div>
          {/* Renders the div interface element or component. */}
          <div className="palette">
            {/* Executes this line as the next step in the surrounding logic. */}
            {activeColours.map((colour) => (
              // Renders the button interface element or component.
              <button
                /* Provides the key value to the surrounding call or element. */
                key={colour}
                /* Provides the type value to the surrounding call or element. */
                type="button"
                /* Provides the className value to the surrounding call or element. */
                className={`peg peg-${colour}`}
                /* Provides the onClick value to the surrounding call or element. */
                onClick={() => chooseSecretPeg(colour)}
                /* Executes this line as the next step in the surrounding logic. */
                aria-label={tg(`colors.${colour}`)}
                /* Closes the expression, call, or declaration started above. */
              >
                {/* Executes this line as the next step in the surrounding logic. */}
                {symbols[colour]}
                {/* Closes the button interface element. */}
              </button>
              // Closes the expression, call, or declaration started above.
            ))}
            {/* Closes the div interface element. */}
          </div>
          {/* Renders the button interface element or component. */}
          <button
            /* Provides the type value to the surrounding call or element. */
            type="button"
            /* Provides the className value to the surrounding call or element. */
            className="text-button"
            /* Provides the disabled value to the surrounding call or element. */
            disabled={secret.length === 0}
            /* Provides the onClick value to the surrounding call or element. */
            onClick={() => setSecret((current) => current.slice(0, -1))}
            /* Closes the expression, call, or declaration started above. */
          >
            {/* Executes this line as the next step in the surrounding logic. */}
            {tg('clear')}
            {/* Closes the button interface element. */}
          </button>
          {/* Closes the fieldset interface element. */}
        </fieldset>
      ) : // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      null}

      {/* Executes this line as the next step in the surrounding logic. */}
      {mode === 'pass_and_play' && passAndPlayPhase === 'handover' ? (
        // Renders the section interface element or component.
        <section className="handover-panel panel" aria-labelledby="handover-title">
          {/* Renders the p interface element or component. */}
          <p className="mode-label">{t('secretConcealed')}</p>
          {/* Renders the h2 interface element or component. */}
          <h2 id="handover-title">{t('handoverTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('handoverBody')}</p>
          {/* Renders the button interface element or component. */}
          <button type="button" className="text-button" onClick={resetSecret}>
            {/* Executes this line as the next step in the surrounding logic. */}
            {t('changeSecret')}
            {/* Closes the button interface element. */}
          </button>
          {/* Closes the section interface element. */}
        </section>
      ) : // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      null}

      {/* Executes this line as the next step in the surrounding logic. */}
      {error ? (
        // Renders the p interface element or component.
        <p className="inline-error" role="alert">
          {/* Executes this line as the next step in the surrounding logic. */}
          {error}
          {/* Closes the p interface element. */}
        </p>
      ) : // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      null}
      {/* Renders the button interface element or component. */}
      <button
        /* Provides the className value to the surrounding call or element. */
        className="button primary"
        /* Provides the type value to the surrounding call or element. */
        type="submit"
        /* Provides the disabled value to the surrounding call or element. */
        disabled={
          // Executes this line as the next step in the surrounding logic.
          submitting ||
          // Executes this line as the next step in the surrounding logic.
          invalid ||
          // Executes this line as the next step in the surrounding logic.
          (mode === 'pass_and_play' &&
            // Provides the passAndPlayPhase value to the surrounding call or element.
            passAndPlayPhase === 'entry' &&
            // Executes this line as the next step in the surrounding logic.
            secret.length !== selectedRules.codeLength)
          // Closes the expression, call, or declaration started above.
        }
        /* Closes the expression, call, or declaration started above. */
      >
        {/* Executes this line as the next step in the surrounding logic. */}
        {submitting
          ? // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            t('starting')
          : // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            mode === 'pass_and_play' && passAndPlayPhase === 'entry'
            ? // Continues the surrounding operation with this required value or expression.
              // Executes this line as the next step in the surrounding logic.
              t('confirmSecret')
            : // Continues the surrounding operation with this required value or expression.
              // Executes this line as the next step in the surrounding logic.
              mode === 'pass_and_play'
              ? // Continues the surrounding operation with this required value or expression.
                // Executes this line as the next step in the surrounding logic.
                t('beginBreakerTurn')
              : // Continues the surrounding operation with this required value or expression.
                // Executes this line as the next step in the surrounding logic.
                t('start')}
        {/* Closes the button interface element. */}
      </button>
      {/* Closes the form interface element. */}
    </form>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
