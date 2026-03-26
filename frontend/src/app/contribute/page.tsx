import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Contribute - Politia',
  description:
    'Join the open-source effort to bring transparency to Indian democracy. Contribute code, data, or infrastructure support.',
};

const detailedCards = [
  {
    title: 'Write Code',
    summary:
      'Help build India\u2019s most comprehensive political data platform.',
    details: [
      'Backend engineers: Python, FastAPI, PostgreSQL, DuckDB',
      'Frontend developers: Next.js, React, TypeScript',
      'ML engineers: NLP for parliamentary transcripts, OCR for affidavit PDFs',
      'Data engineers: DuckDB, Parquet, ETL pipelines',
      'DevOps: CI/CD, Docker, free-tier deployment optimization',
    ],
    stats: '204 tests. Clean architecture. Real impact.',
    cta: 'View Open Issues',
    href: 'https://github.com/naqeebali-shamsi/Politia/issues',
  },
  {
    title: 'Sponsor Infrastructure',
    summary:
      'We run entirely on free tiers \u2014 $0/month. Your support unlocks capabilities.',
    details: [
      '17,000 hours of parliament audio awaiting transcription',
      '500,000 affidavit PDFs to OCR and structure',
      'Semantic search across parliamentary proceedings',
      'Faster CI/CD and preview deployments',
      'Database scaling for historical election data',
    ],
    stats:
      'Even a small server donation unlocks months of work.',
    cta: 'Sponsor on GitHub',
    href: 'https://github.com/naqeebali-shamsi/Politia',
  },
  {
    title: 'Contribute Data',
    summary:
      'Government data is scattered across dozens of portals and PDFs.',
    details: [
      'Election Commission data: candidate affidavits, results',
      'State assembly records and proceedings',
      'MPLADS (MP Local Area Development Scheme) spending data',
      'Parliamentary question-answer records',
      'Committee reports and attendance records',
    ],
    stats:
      'Your contribution directly strengthens democratic accountability.',
    cta: 'Data Contribution Guide',
    href: 'https://github.com/naqeebali-shamsi/Politia/blob/master/CONTRIBUTING.md',
  },
];

export default function ContributePage() {
  return (
    <div>
      {/* Hero */}
      <section style={{ textAlign: 'center', padding: '3rem 0 2rem' }}>
        <h1
          style={{
            fontSize: '2rem',
            fontWeight: 700,
            marginBottom: '0.75rem',
            letterSpacing: '-0.5px',
          }}
        >
          Built for India, by India&apos;s developers
        </h1>
        <p
          style={{
            color: 'var(--text-secondary)',
            maxWidth: '620px',
            margin: '0 auto 1rem',
            fontSize: '0.9375rem',
            lineHeight: 1.7,
          }}
        >
          Politia is an open-source effort to bring transparency to Indian
          democracy. No corporate backing. No political agenda. Just public
          data, presented honestly.
        </p>
        <a
          href="https://github.com/naqeebali-shamsi/Politia"
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-primary"
          style={{ marginTop: '0.5rem' }}
        >
          View on GitHub
          <span aria-hidden="true" style={{ marginLeft: '0.375rem' }}>
            &rarr;
          </span>
        </a>
      </section>

      {/* Detailed Cards */}
      <section style={{ marginTop: '2rem' }}>
        <div className="contribute-detailed-grid">
          {detailedCards.map((card) => (
            <div key={card.title} className="card contribute-detailed-card">
              <h2 className="contribute-detailed-title">{card.title}</h2>
              <p className="contribute-detailed-summary">{card.summary}</p>
              <ul className="contribute-detailed-list">
                {card.details.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              <p className="contribute-detailed-stats">{card.stats}</p>
              <a
                href={card.href}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary contribute-detailed-cta"
              >
                {card.cta}
                <span aria-hidden="true" style={{ marginLeft: '0.375rem' }}>
                  &rarr;
                </span>
              </a>
            </div>
          ))}
        </div>
      </section>

      {/* Bottom Message */}
      <section className="contribute-page-bottom">
        <div className="contribute-page-bottom-inner">
          <p className="contribute-page-bottom-text">
            An effort against unemployment and corruption. Every line of code,
            every data point, every contribution makes Indian democracy more
            transparent.
          </p>
          <p className="contribute-page-bottom-join">
            Join{' '}
            <span role="img" aria-label="Indian flag">
              &#127470;&#127475;
            </span>
          </p>
          <a
            href="https://github.com/naqeebali-shamsi/Politia"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
            style={{ marginTop: '1rem' }}
          >
            github.com/naqeebali-shamsi/Politia
          </a>
        </div>
      </section>
    </div>
  );
}
