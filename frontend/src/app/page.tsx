import Link from 'next/link';
import HomeContent from '@/components/HomeContent';
import ContributeSection from '@/components/ContributeSection';

export default function HomePage() {
  return (
    <div>
      {/* ── Hero ── */}
      <section style={{ textAlign: 'center', padding: '3rem 0 2rem' }}>
        <h1
          style={{
            fontSize: '2rem',
            fontWeight: 700,
            marginBottom: '0.5rem',
            letterSpacing: '-0.5px',
          }}
        >
          Indian MP Accountability Dashboard
        </h1>
        <p
          style={{
            color: 'var(--text-secondary)',
            maxWidth: '560px',
            margin: '0 auto 1.5rem',
            fontSize: '0.9375rem',
          }}
        >
          Track how your representatives perform in Parliament. Every score
          traces back to official records — attendance, questions, affidavits,
          and declared criminal cases.
        </p>
      </section>

      {/* Client component handles API calls */}
      <HomeContent />

      {/* ── Quick links ── */}
      <section style={{ marginTop: '3rem' }}>
        <div className="grid-3">
          <div className="card">
            <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem' }}>
              Transparent Scoring
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              Every score is composed from verifiable components: parliamentary
              participation, financial disclosure completeness, and declared
              criminal records.
            </p>
            <Link
              href="/methodology"
              style={{ display: 'inline-block', marginTop: '0.75rem', fontSize: '0.8125rem' }}
            >
              Read methodology
            </Link>
          </div>
          <div className="card">
            <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem' }}>
              Compare MPs
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              Place any two or three MPs side by side. See how they differ on
              attendance, asset declarations, and criminal disclosures.
            </p>
            <Link
              href="/compare"
              style={{ display: 'inline-block', marginTop: '0.75rem', fontSize: '0.8125rem' }}
            >
              Start comparing
            </Link>
          </div>
          <div className="card">
            <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem' }}>
              Official Sources Only
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              No AI-generated summaries, no media opinions. All data comes from
              Parliament records and Election Commission affidavits.
            </p>
            <Link
              href="/methodology#sources"
              style={{ display: 'inline-block', marginTop: '0.75rem', fontSize: '0.8125rem' }}
            >
              View sources
            </Link>
          </div>
        </div>
      </section>

      {/* ── Contribute ── */}
      <ContributeSection />
    </div>
  );
}
