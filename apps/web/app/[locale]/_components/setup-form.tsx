'use client';

import { useTranslations } from 'next-intl';
import { useRef, useState } from 'react';
import { useRouter } from '@/i18n/navigation';
import { type Game, useApi } from '@/lib/api';
import { gameDifficulty, gameMode } from '@/lib/analytics-delivery';
import { useProductAnalytics } from '@/lib/use-product-analytics';

const colourIds = ['R', 'B', 'G', 'Y', 'W', 'K', 'O', 'P', 'C', 'M'] as const;
const symbols: Record<string, string> = {
  R: '●',
  B: '◆',
  G: '▲',
  Y: '■',
  W: '○',
  K: '✚',
  O: '⬟',
  P: '✦',
  C: '⬢',
  M: '♥',
};
const presets = {
  easy: { colourCount: 5, codeLength: 4, maxAttempts: 12, duplicatesAllowed: false },
  normal: { colourCount: 6, codeLength: 4, maxAttempts: 10, duplicatesAllowed: true },
  hard: { colourCount: 8, codeLength: 5, maxAttempts: 8, duplicatesAllowed: true },
  expert: { colourCount: 10, codeLength: 6, maxAttempts: 8, duplicatesAllowed: true },
} as const;

type Difficulty = keyof typeof presets | 'custom';
type Mode = 'solo' | 'practice' | 'pass_and_play';

export function SetupForm() {
  const t = useTranslations('Play');
  const tg = useTranslations('Game');
  const tc = useTranslations('Common');
  const api = useApi();
  const analytics = useProductAnalytics();
  const router = useRouter();
  const [mode, setMode] = useState<Mode>('solo');
  const [difficulty, setDifficulty] = useState<Difficulty>('normal');
  const [colourCount, setColourCount] = useState(6);
  const [codeLength, setCodeLength] = useState(4);
  const [maxAttempts, setMaxAttempts] = useState(10);
  const [duplicatesAllowed, setDuplicatesAllowed] = useState(true);
  const [visibility, setVisibility] = useState<'private' | 'shareable'>('private');
  const [secret, setSecret] = useState<string[]>([]);
  const [passAndPlayPhase, setPassAndPlayPhase] = useState<'entry' | 'handover'>('entry');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const confirmedSecretRef = useRef<string[] | null>(null);
  const creationKeyRef = useRef<string | null>(null);

  const selectedRules =
    difficulty === 'custom'
      ? { colourCount, codeLength, maxAttempts, duplicatesAllowed }
      : presets[difficulty];
  const activeColours = colourIds.slice(0, selectedRules.colourCount);
  const invalid =
    !selectedRules.duplicatesAllowed && selectedRules.colourCount < selectedRules.codeLength;

  const chooseSecretPeg = (colour: string) => {
    setSecret((current) => {
      if (!selectedRules.duplicatesAllowed && current.includes(colour)) return current;
      return [...current, colour].slice(0, selectedRules.codeLength);
    });
  };

  const resetSecret = () => {
    setSecret([]);
    setPassAndPlayPhase('entry');
    confirmedSecretRef.current = null;
    creationKeyRef.current = null;
  };

  const createGame = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (
      invalid ||
      (mode === 'pass_and_play' &&
        passAndPlayPhase === 'entry' &&
        secret.length !== selectedRules.codeLength)
    )
      return;
    if (mode === 'pass_and_play' && passAndPlayPhase === 'entry') {
      confirmedSecretRef.current = [...secret];
      setSecret([]);
      setPassAndPlayPhase('handover');
      setError(null);
      return;
    }
    setSubmitting(true);
    setError(null);
    creationKeyRef.current ??= crypto.randomUUID();
    const needsConfig = difficulty === 'custom' || mode === 'pass_and_play';
    const body: Record<string, unknown> = {
      mode,
      idempotencyKey: creationKeyRef.current,
      ...(needsConfig
        ? {
            config: {
              colours: [...activeColours],
              codeLength: selectedRules.codeLength,
              maxAttempts: selectedRules.maxAttempts,
              duplicatesAllowed: selectedRules.duplicatesAllowed,
              codeMaker: mode === 'pass_and_play' ? 'human' : 'computer',
              visibility,
              ranked: false,
              timeBonusCap: 300,
            },
          }
        : { difficulty }),
      ...(mode === 'pass_and_play' ? { secret: confirmedSecretRef.current } : {}),
    };
    try {
      const game = await api<Game>('/v1/games', { method: 'POST', body: JSON.stringify(body) });
      resetSecret();
      analytics('game_started', {
        mode: gameMode(game.mode),
        difficulty: gameDifficulty(game.difficulty),
      });
      router.push(`/play/${game.id}`);
    } catch {
      setError(t('createError'));
      setSubmitting(false);
    }
  };

  return (
    <form className="setup-form" onSubmit={(event) => void createGame(event)}>
      <fieldset className="choice-group">
        <legend>{t('mode')}</legend>
        <div className="segmented-options">
          {(['solo', 'practice', 'pass_and_play'] as const).map((value) => (
            <label key={value}>
              <input
                type="radio"
                name="mode"
                value={value}
                checked={mode === value}
                onChange={() => {
                  setMode(value);
                  resetSecret();
                }}
              />
              <span>{value === 'pass_and_play' ? t('human') : t(value)}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset className="choice-group">
        <legend>{t('difficulty')}</legend>
        <div className="difficulty-options">
          {(['easy', 'normal', 'hard', 'expert', 'custom'] as const).map((value) => (
            <label key={value} className="difficulty-option">
              <input
                type="radio"
                name="difficulty"
                value={value}
                checked={difficulty === value}
                onChange={() => {
                  setDifficulty(value);
                  resetSecret();
                  analytics('difficulty_selected', { difficulty: value });
                }}
              />
              <span>
                <strong>{t(value)}</strong>
                <small>{t(`${value}Detail`)}</small>
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      {difficulty === 'custom' ? (
        <div className="form-grid panel">
          <label>
            {t('colours')}
            <input
              type="number"
              name="colour-count"
              inputMode="numeric"
              autoComplete="off"
              min="5"
              max="10"
              value={colourCount}
              onChange={(event) => {
                setColourCount(Number(event.target.value));
                resetSecret();
              }}
            />
          </label>
          <label>
            {t('codeLength')}
            <input
              type="number"
              name="code-length"
              inputMode="numeric"
              autoComplete="off"
              min="3"
              max="6"
              value={codeLength}
              onChange={(event) => {
                setCodeLength(Number(event.target.value));
                resetSecret();
              }}
            />
          </label>
          <label>
            {t('maximumAttempts')}
            <input
              type="number"
              name="maximum-attempts"
              inputMode="numeric"
              autoComplete="off"
              min="1"
              max="20"
              value={maxAttempts}
              onChange={(event) => setMaxAttempts(Number(event.target.value))}
            />
          </label>
          <label className="check-row">
            <input
              type="checkbox"
              name="duplicates-allowed"
              checked={duplicatesAllowed}
              onChange={(event) => {
                setDuplicatesAllowed(event.target.checked);
                resetSecret();
              }}
            />
            <span>{t('duplicates')}</span>
          </label>
          <label>
            {t('visibility')}
            <select
              name="visibility"
              autoComplete="off"
              value={visibility}
              onChange={(event) => setVisibility(event.target.value as 'private' | 'shareable')}
            >
              <option value="private">{tc('private')}</option>
              <option value="shareable">{tc('shareable')}</option>
            </select>
          </label>
          {invalid ? (
            <p className="inline-error" role="alert">
              {t('invalidCustom')}
            </p>
          ) : null}
        </div>
      ) : null}

      {mode === 'pass_and_play' && passAndPlayPhase === 'entry' ? (
        <fieldset className="secret-picker panel">
          <legend>{t('secret')}</legend>
          <p>{t('secretHelp')}</p>
          <div className="secret-row concealed-secret" role="group" aria-label={t('secret')}>
            {Array.from({ length: selectedRules.codeLength }, (_, index) => {
              const colour = secret[index];
              return (
                <span
                  key={index}
                  className="peg slot"
                  role="img"
                  aria-label={
                    colour
                      ? t('secretPositionFilled', { position: index + 1 })
                      : t('secretPositionEmpty', { position: index + 1 })
                  }
                >
                  {colour ? '●' : index + 1}
                </span>
              );
            })}
          </div>
          <div className="palette">
            {activeColours.map((colour) => (
              <button
                key={colour}
                type="button"
                className={`peg peg-${colour}`}
                onClick={() => chooseSecretPeg(colour)}
                aria-label={tg(`colors.${colour}`)}
              >
                {symbols[colour]}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="text-button"
            disabled={secret.length === 0}
            onClick={() => setSecret((current) => current.slice(0, -1))}
          >
            {tg('clear')}
          </button>
        </fieldset>
      ) : null}

      {mode === 'pass_and_play' && passAndPlayPhase === 'handover' ? (
        <section className="handover-panel panel" aria-labelledby="handover-title">
          <p className="mode-label">{t('secretConcealed')}</p>
          <h2 id="handover-title">{t('handoverTitle')}</h2>
          <p>{t('handoverBody')}</p>
          <button type="button" className="text-button" onClick={resetSecret}>
            {t('changeSecret')}
          </button>
        </section>
      ) : null}

      {error ? (
        <p className="inline-error" role="alert">
          {error}
        </p>
      ) : null}
      <button
        className="button primary"
        type="submit"
        disabled={
          submitting ||
          invalid ||
          (mode === 'pass_and_play' &&
            passAndPlayPhase === 'entry' &&
            secret.length !== selectedRules.codeLength)
        }
      >
        {submitting
          ? t('starting')
          : mode === 'pass_and_play' && passAndPlayPhase === 'entry'
            ? t('confirmSecret')
            : mode === 'pass_and_play'
              ? t('beginBreakerTurn')
              : t('start')}
      </button>
    </form>
  );
}
