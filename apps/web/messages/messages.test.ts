import { describe, expect, it } from 'vitest';
import en from './en.json';
import zhHant from './zh-Hant.json';

function flatten(value: unknown, prefix = ''): Array<[string, string]> {
  if (typeof value === 'string') return [[prefix, value]];
  if (!value || typeof value !== 'object') return [];
  return Object.entries(value).flatMap(([key, nested]) =>
    flatten(nested, prefix ? `${prefix}.${key}` : key),
  );
}

describe('translation catalogs', () => {
  it('keeps English and Traditional Chinese keys complete and non-empty', () => {
    const english = new Map(flatten(en));
    const traditionalChinese = new Map(flatten(zhHant));

    expect([...traditionalChinese.keys()].sort()).toEqual([...english.keys()].sort());
    expect([...english.values()].every((value) => value.trim().length > 0)).toBe(true);
    expect([...traditionalChinese.values()].every((value) => value.trim().length > 0)).toBe(true);
  });
});
