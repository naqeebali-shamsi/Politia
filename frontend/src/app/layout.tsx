import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';

export const metadata: Metadata = {
  title: 'Politia - Indian MP Accountability Dashboard',
  description:
    'Evidence-backed accountability dashboard for Indian Members of Parliament. Scores derived from official parliamentary records and election affidavits.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <div className="site-header-inner">
            <Link href="/" className="site-logo">
              Politia
            </Link>
            <nav className="site-nav">
              <Link href="/leaderboard">Leaderboard</Link>
              <Link href="/compare">Compare</Link>
              <Link href="/methodology">Methodology</Link>
            </nav>
          </div>
        </header>

        <div className="page-container">{children}</div>

        <footer className="site-footer">
          <p>
            Politia is an open-source civic accountability project. All data
            sourced from official parliamentary records and election affidavits.
          </p>
          <p style={{ marginTop: '0.5rem' }}>
            <Link href="/methodology">Methodology</Link>
            {' · '}
            Data may be incomplete or delayed. This is not an endorsement or
            condemnation of any politician.
          </p>
        </footer>
      </body>
    </html>
  );
}
