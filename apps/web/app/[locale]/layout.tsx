// Imports the dependency used by this module.
import type { Metadata } from 'next';
// Imports the dependency used by this module.
import { hasLocale, NextIntlClientProvider } from 'next-intl';
// Imports the dependency used by this module.
import { getMessages, getTranslations, setRequestLocale } from 'next-intl/server';
// Imports the dependency used by this module.
import { notFound } from 'next/navigation';
// Imports the dependency used by this module.
import { AppShell } from '@/components/app-shell';
// Imports the dependency used by this module.
import { routing } from '@/i18n/routing';
// Imports the dependency used by this module.
import { LocaleDocumentLanguage } from './_components/locale-document-language';

// Declares the LocaleLayoutProps data shape or implementation.
type LocaleLayoutProps = Readonly<{
  // Defines the children field in the surrounding object or type.
  children: React.ReactNode;
  // Defines the params field in the surrounding object or type.
  params: Promise<{ locale: string }>;
  // Closes the expression, call, or declaration started above.
}>;

// Exports this declaration for use by other modules.
export function generateStaticParams() {
  // Returns this result to the caller and ends the current function.
  return routing.locales.map((locale) => ({ locale }));
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export async function generateMetadata({
  // Supplies this item to the surrounding call or collection.
  params,
  // Begins the nested block or object completed below.
}: Pick<LocaleLayoutProps, 'params'>): Promise<Metadata> {
  // Executes this line as the next step in the surrounding logic.
  const { locale } = await params;
  // Checks this condition before running the nested branch.
  if (!hasLocale(routing.locales, locale)) return {};
  // Computes and stores t for subsequent operations.
  const t = await getTranslations({ locale, namespace: 'Meta' });
  // Returns this result to the caller and ends the current function.
  return {
    // Defines the title field in the surrounding object or type.
    title: { default: t('title'), template: `%s · ${t('title')}` },
    // Defines the description field in the surrounding object or type.
    description: t('description'),
    // Defines the applicationName field in the surrounding object or type.
    applicationName: 'Cipherboard',
    // Defines the manifest field in the surrounding object or type.
    manifest: '/manifest.webmanifest',
    // Defines the appleWebApp field in the surrounding object or type.
    appleWebApp: { capable: true, title: 'Cipherboard' },
    // Closes the expression, call, or declaration started above.
  };
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration as the module default.
export default async function LocaleLayout({ children, params }: LocaleLayoutProps) {
  // Executes this line as the next step in the surrounding logic.
  const { locale } = await params;
  // Checks this condition before running the nested branch.
  if (!hasLocale(routing.locales, locale)) notFound();
  // Calls setRequestLocale with the supplied values.
  setRequestLocale(locale);
  // Computes and stores messages for subsequent operations.
  const messages = await getMessages();

  // Returns this result to the caller and ends the current function.
  return (
    // Renders the NextIntlClientProvider interface element or component.
    <NextIntlClientProvider messages={messages}>
      {/* Renders the LocaleDocumentLanguage interface element or component. */}
      <LocaleDocumentLanguage locale={locale} />
      {/* Renders the AppShell interface element or component. */}
      <AppShell>{children}</AppShell>
      {/* Closes the NextIntlClientProvider interface element. */}
    </NextIntlClientProvider>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
