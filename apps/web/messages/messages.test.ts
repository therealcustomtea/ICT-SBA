// Imports the dependency used by this module.
import { describe, expect, it } from 'vitest';
// Imports the dependency used by this module.
import en from './en.json';
// Imports the dependency used by this module.
import zhHant from './zh-Hant.json';

// Defines the flatten function and its callable behavior.
function flatten(value: unknown, prefix = ''): Array<[string, string]> {
  // Checks this condition before running the nested branch.
  if (typeof value === 'string') return [[prefix, value]];
  // Checks this condition before running the nested branch.
  if (!value || typeof value !== 'object') return [];
  // Returns this result to the caller and ends the current function.
  return Object.entries(value).flatMap(
    ([key, nested]) =>
      // Calls flatten with the supplied values.
      flatten(nested, prefix ? `${prefix}.${key}` : key),
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Calls describe with the supplied values.
describe('translation catalogs', () => {
  // Calls it with the supplied values.
  it('keeps English and Traditional Chinese keys complete and non-empty', () => {
    // Computes and stores english for subsequent operations.
    const english = new Map(flatten(en));
    // Computes and stores traditionalChinese for subsequent operations.
    const traditionalChinese = new Map(flatten(zhHant));

    // Calls expect with the supplied values.
    expect([...traditionalChinese.keys()].sort()).toEqual([...english.keys()].sort());
    // Calls expect with the supplied values.
    expect([...english.values()].every((value) => value.trim().length > 0)).toBe(true);
    // Calls expect with the supplied values.
    expect([...traditionalChinese.values()].every((value) => value.trim().length > 0)).toBe(true);
    // Closes the expression, call, or declaration started above.
  });
  // Closes the expression, call, or declaration started above.
});
