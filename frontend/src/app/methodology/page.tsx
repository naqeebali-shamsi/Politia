import Link from 'next/link';

export default function MethodologyPage() {
  return (
    <div style={{ maxWidth: '720px' }}>
      <div className="breadcrumb">
        <Link href="/">Home</Link>
        <span className="breadcrumb-sep">/</span>
        <span>Methodology</span>
      </div>

      <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>
        Scoring Methodology
      </h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', fontSize: '0.9375rem' }}>
        How Politia calculates accountability scores, what data it uses, and
        what its limitations are. We believe transparency about our own methods
        is as important as the transparency we measure.
      </p>

      {/* Formula */}
      <section className="card" style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.75rem' }}>
          The Formula
        </h2>
        <code
          style={{
            display: 'block',
            padding: '0.75rem 1rem',
            background: 'var(--bg-muted)',
            borderRadius: 'var(--radius)',
            fontSize: '0.875rem',
            marginBottom: '1rem',
          }}
        >
          Overall Score = Participation Score + Disclosure Score - Integrity Risk Adjustment
        </code>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
          Each component is calculated independently and contributes to the
          final score. The Overall Score typically ranges from 0 to 100, though
          negative values are possible if integrity risk penalties are high.
        </p>
      </section>

      {/* Participation */}
      <section className="card" style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.75rem' }}>
          1. Participation Score
        </h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: '0.75rem' }}>
          Measures how actively an MP engages in parliamentary proceedings. The
          component scores are weighted and summed:
        </p>
        <ul style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', paddingLeft: '1.25rem', lineHeight: 2 }}>
          <li>
            <strong>Attendance</strong> -- Percentage of sessions attended,
            sourced from Lok Sabha / Rajya Sabha official records.
          </li>
          <li>
            <strong>Questions Asked</strong> -- Number of parliamentary
            questions raised, normalized against the session average.
          </li>
          <li>
            <strong>Debates Participated</strong> -- Active participation in
            parliamentary debates.
          </li>
          <li>
            <strong>Private Bills Introduced</strong> -- Legislative initiative
            shown through private member bills.
          </li>
        </ul>
      </section>

      {/* Disclosure */}
      <section className="card" style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.75rem' }}>
          2. Disclosure Score
        </h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: '0.75rem' }}>
          Measures the completeness and transparency of financial disclosures
          filed as part of election affidavits:
        </p>
        <ul style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', paddingLeft: '1.25rem', lineHeight: 2 }}>
          <li>
            <strong>Affidavit Completeness</strong> -- Whether all mandatory
            fields in the affidavit were filled.
          </li>
          <li>
            <strong>Assets Declared</strong> -- Whether movable and immovable
            assets were properly itemized.
          </li>
          <li>
            <strong>Liabilities Declared</strong> -- Whether outstanding
            liabilities were disclosed.
          </li>
        </ul>
      </section>

      {/* Integrity */}
      <section className="card" style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.75rem' }}>
          3. Integrity Risk Adjustment
        </h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: '0.75rem' }}>
          A penalty subtracted from the overall score, based on self-declared
          criminal cases in election affidavits:
        </p>
        <ul style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', paddingLeft: '1.25rem', lineHeight: 2 }}>
          <li>
            <strong>Criminal Cases Penalty</strong> -- Based on the number of
            declared criminal cases pending against the candidate.
          </li>
          <li>
            <strong>Serious Cases Penalty</strong> -- Additional penalty for
            cases involving serious charges (e.g., those under IPC sections
            carrying sentences of 5+ years).
          </li>
        </ul>
        <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.75rem' }}>
          Important: These are self-declared cases from sworn affidavits, not
          convictions. Pending cases do not imply guilt. However, the volume and
          severity of declared cases is a factual data point voters may wish to
          consider.
        </p>
      </section>

      {/* Sources */}
      <section id="sources" className="card" style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.75rem' }}>
          Data Sources
        </h2>
        <ul style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', paddingLeft: '1.25rem', lineHeight: 2 }}>
          <li>
            <strong>Parliament of India</strong> -- Lok Sabha and Rajya Sabha
            official websites for attendance, questions, debates, and bills.
          </li>
          <li>
            <strong>Election Commission of India</strong> -- Official election
            results, candidate data.
          </li>
          <li>
            <strong>Association for Democratic Reforms / MyNeta.info</strong> --
            Digitized election affidavit data including assets, liabilities, and
            criminal records.
          </li>
        </ul>
        <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.75rem' }}>
          Politia does not use AI-generated summaries, social media analysis,
          media sentiment, or any subjective data. Every data point traces to a
          verifiable official record.
        </p>
      </section>

      {/* Limitations */}
      <section className="card" style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.75rem' }}>
          Known Limitations
        </h2>
        <ul style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', paddingLeft: '1.25rem', lineHeight: 2 }}>
          <li>
            Data may lag official sources by days or weeks. Scores reflect the
            last available data, not real-time records.
          </li>
          <li>
            Constituency-level work, committee contributions, and behind-the-scenes
            legislative drafting are not captured by these metrics.
          </li>
          <li>
            The scoring formula weights are a design choice. Different weightings
            would produce different rankings. We publish the formula for scrutiny.
          </li>
          <li>
            Rajya Sabha members have structurally different roles; direct
            comparison across chambers should be made cautiously.
          </li>
          <li>
            Incomplete or erroneously filed affidavits can affect disclosure
            scores. We report what is filed, not what is true.
          </li>
          <li>
            Newer MPs may have fewer data points, potentially disadvantaging them
            in participation scores.
          </li>
        </ul>
      </section>

      {/* Non-partisan */}
      <section className="card">
        <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.75rem' }}>
          Non-partisan Commitment
        </h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
          Politia applies the same formula to every MP regardless of party,
          state, or ideology. We do not editorialize, recommend candidates, or
          attach interpretive labels beyond what the numbers show. The data is
          structured for citizens to draw their own conclusions.
        </p>
      </section>
    </div>
  );
}
