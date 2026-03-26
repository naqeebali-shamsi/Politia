import Link from 'next/link';

const cards = [
  {
    title: 'Write Code',
    description:
      'Help build India\u2019s most comprehensive political data platform. We need backend engineers (Python/FastAPI), frontend developers (Next.js), ML engineers (NLP, OCR), and data engineers (DuckDB, Parquet). 204 tests. Clean architecture. Real impact.',
    cta: 'View Open Issues',
    href: 'https://github.com/naqeebali-shamsi/Politia/issues',
  },
  {
    title: 'Sponsor Infrastructure',
    description:
      'We run entirely on free tiers \u2014 $0/month. But we have 17,000 hours of parliament audio to transcribe, 500,000 affidavit PDFs to OCR, and semantic search that needs room to grow. Even a small server donation unlocks months of work.',
    cta: 'Sponsor on GitHub',
    href: 'https://github.com/naqeebali-shamsi/Politia',
  },
  {
    title: 'Contribute Data',
    description:
      'Government data is scattered across dozens of portals and PDFs. If you have access to Election Commission data, state assembly records, MPLADS spending data, or parliamentary proceedings, your contribution directly strengthens democratic accountability.',
    cta: 'Data Contribution Guide',
    href: 'https://github.com/naqeebali-shamsi/Politia/blob/master/CONTRIBUTING.md',
  },
];

export default function ContributeSection() {
  return (
    <section className="contribute-section">
      <div className="contribute-header">
        <h2 className="contribute-headline">
          Built for India, by India&apos;s developers
        </h2>
        <p className="contribute-subtext">
          Politia is an open-source effort to bring transparency to Indian
          democracy. No corporate backing. No political agenda. Just public
          data, presented honestly.
        </p>
      </div>

      <div className="grid-3 contribute-cards">
        {cards.map((card) => (
          <div key={card.title} className="card contribute-card">
            <h3 className="contribute-card-title">{card.title}</h3>
            <p className="contribute-card-desc">{card.description}</p>
            <a
              href={card.href}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary contribute-card-cta"
            >
              {card.cta}
              <span aria-hidden="true" style={{ marginLeft: '0.375rem' }}>
                &rarr;
              </span>
            </a>
          </div>
        ))}
      </div>

      <p className="contribute-bottom-message">
        An effort against unemployment and corruption. Every line of code,
        every data point, every contribution makes Indian democracy more
        transparent.{' '}
        <Link href="/contribute">
          Join{' '}
          <span role="img" aria-label="Indian flag">
            &#127470;&#127475;
          </span>
        </Link>
      </p>
    </section>
  );
}
