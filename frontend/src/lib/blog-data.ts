export interface BlogAuthor {
  name: string;
  role: string;
  avatar: string;
}

export interface BlogMetaItem {
  label: string;
  value: string;
}

export interface BlogTocItem {
  id: string;
  title: string;
}

export interface BlogArticle {
  slug: string;
  title: string;
  excerpt: string;
  category: 'Architecture' | 'Data Journey' | 'Open Source';
  date: string;
  readTime: string;
  heroImage: string;
  author: BlogAuthor;
  metadata: BlogMetaItem[];
  toc: BlogTocItem[];
  content: string;
}

const authors: Record<string, BlogAuthor> = {
  team: {
    name: 'Politia Team',
    role: 'Engineering',
    avatar: '',
  },
};

export const articles: BlogArticle[] = [
  {
    slug: 'building-politia',
    title: 'Building India\'s Most Comprehensive Political Data Platform',
    excerpt:
      'How we went from zero to 500K records with a hexagonal backend, survived a P0 audit that found 72.5% of scores were meaningless, and rebuilt everything from the ground up.',
    category: 'Architecture',
    date: '2026-03-20',
    readTime: '12 min read',
    heroImage: '',
    author: authors.team,
    metadata: [
      { label: 'Tech Stack', value: 'FastAPI, Next.js 16, PostgreSQL' },
      { label: 'Data Scale', value: '500K+ records' },
      { label: 'Architecture', value: 'Hexagonal / SOLID' },
      { label: 'Infrastructure Cost', value: '$0 (free tier)' },
      { label: 'Data Sources', value: '6 primary datasets' },
      { label: 'Time to MVP', value: '6 days' },
    ],
    toc: [
      { id: 'the-problem', title: 'The Problem' },
      { id: 'architecture-decisions', title: 'Architecture Decisions' },
      { id: 'the-data-pipeline', title: 'The Data Pipeline' },
      { id: 'the-scoring-formula', title: 'The Scoring Formula' },
      { id: 'the-p0-audit', title: 'The P0 Audit' },
      { id: 'entity-resolution', title: 'Entity Resolution' },
      { id: 'what-we-learned', title: 'What We Learned' },
    ],
    content: `
<section id="the-problem">
<h2>The Problem</h2>
<p>India has 543 Members of Parliament in the Lok Sabha alone. Citizens vote every five years, but between elections, there is almost no accessible, structured way to track how representatives actually perform. Parliamentary attendance data exists on government portals. Criminal records sit in election affidavits. Asset declarations are buried in PDFs. But nobody had stitched it all together into a single, evidence-backed accountability score.</p>
<p>We set out to build Politia: a platform that treats every claim as a data point that must trace back to an official source. No AI-generated summaries, no media opinions. Just records.</p>
<blockquote>Every score on Politia traces back to an official parliamentary record or election affidavit. If we cannot source it, we do not display it.</blockquote>
</section>

<section id="architecture-decisions">
<h2>Architecture Decisions</h2>
<p>We chose a <strong>hexagonal architecture</strong> with strict SOLID principles for the backend. This was not academic perfectionism -- it was survival. When you are normalizing data from six different sources with different schemas, field names, and levels of completeness, you need clear boundaries.</p>
<ul>
<li><strong>FastAPI</strong> for the backend -- async by default, Pydantic models as the contract layer between ingestion and API</li>
<li><strong>PostgreSQL on Neon</strong> -- free tier, serverless scaling, branching for safe migrations</li>
<li><strong>Next.js 16 on Vercel</strong> -- React 19 server components for the frontend, zero client JS where possible</li>
<li><strong>Cloudflare R2</strong> -- object storage for raw affidavit PDFs and bulk data exports</li>
<li><strong>GitHub Actions</strong> -- cron jobs for periodic data refresh, zero infrastructure cost</li>
</ul>
<p>The entire stack runs on free tiers. Total infrastructure cost: <strong>$0/month</strong>.</p>
</section>

<section id="the-data-pipeline">
<h2>The Data Pipeline</h2>
<p>The key insight that saved us weeks of work: <strong>most of the data we needed already existed as structured downloads</strong>. We did not need to build scrapers for 80% of our requirements.</p>
<ul>
<li><strong>Vonter/india-representatives-activity</strong> -- MP performance data from PRS Legislative Research, already in JSON/CSV</li>
<li><strong>datameet/india-election-data</strong> -- All Lok Sabha election results since independence, clean CSV</li>
<li><strong>TCPD-IED via LokDhaba</strong> -- Election data from 1962 onward with unique politician IDs (critical for entity resolution)</li>
<li><strong>Parliamentary candidates affidavit data</strong> -- Affidavits from 2004 to 2019, structured</li>
<li><strong>OpenSanctions in_sansad</strong> -- All current MPs with biographical data in JSON</li>
<li><strong>data.gov.in</strong> -- Attendance records, committee memberships, bills participation in CSV</li>
</ul>
<p>Scraping was only needed for two sources: MyNeta 2024 election data and the latest PRS session data. Everything else was download-normalize-ingest.</p>
</section>

<section id="the-scoring-formula">
<h2>The Scoring Formula</h2>
<p>The scoring formula went through two major versions. Version 1 was intuitive but deeply flawed. It attempted to score MPs on a 0-100 scale across five dimensions:</p>
<ul>
<li><strong>Parliamentary Activity</strong> (30%) -- attendance, questions asked, debates participated in</li>
<li><strong>Financial Integrity</strong> (25%) -- asset disclosure completeness, wealth growth rate</li>
<li><strong>Criminal Record</strong> (20%) -- number and severity of declared criminal cases</li>
<li><strong>Education &amp; Background</strong> (15%) -- educational qualifications, professional background</li>
<li><strong>Constituency Work</strong> (10%) -- MPLADS fund utilization</li>
</ul>
<p>This looked reasonable on paper. It was not.</p>
</section>

<section id="the-p0-audit">
<h2>The P0 Audit</h2>
<p>We ran a comprehensive audit of every score in the database and the results were devastating. <strong>72.5% of all computed scores were effectively meaningless</strong> because they relied on fields that had no data.</p>
<p>The audit uncovered five critical problems:</p>
<ul>
<li><strong>Ghost fields:</strong> The formula referenced data columns that did not exist in any of our six data sources. Education level, MPLADS utilization, and constituency development metrics were scored as zeros, dragging down every MP</li>
<li><strong>Entity resolution failures:</strong> 147 MPs could not be matched across datasets because name variations (Scindia vs Scindia vs Jyotiraditya M. Scindia) broke our naive string matching</li>
<li><strong>Integrity-rewards-ignorance bug:</strong> MPs who never filed an affidavit scored higher on "financial integrity" than those who filed and declared assets, because missing data defaulted to a neutral score while actual declarations got penalized for wealth</li>
<li><strong>Criminal severity not weighted:</strong> An MP with one murder charge scored the same as one with a traffic violation</li>
<li><strong>2019 data missing entirely:</strong> The 2019 election -- the most recent completed election at the time -- had zero records ingested</li>
</ul>
<p>We killed the scoring formula, fixed entity resolution using TCPD unique IDs as the canonical key, ingested 2014 and 2024 election data, and rebuilt the formula from scratch with <strong>data sufficiency gates</strong>: if a score component has less than 50% of its required data points, it is marked as "insufficient data" rather than computed from garbage.</p>
<blockquote>A score computed from missing data is worse than no score at all. It creates false confidence.</blockquote>
</section>

<section id="entity-resolution">
<h2>Entity Resolution</h2>
<p>Matching the same politician across six different datasets is harder than it sounds. Consider Jyotiraditya Scindia:</p>
<ul>
<li>Election Commission: "JYOTIRADITYA M. SCINDIA"</li>
<li>PRS Legislative: "Jyotiraditya Madhavrao Scindia"</li>
<li>MyNeta: "Shri Jyotiraditya M Scindia"</li>
<li>Parliament records: "SCINDIA, SHRI JYOTIRADITYA M."</li>
</ul>
<p>Our solution: use the <strong>TCPD-IED unique politician ID</strong> as the canonical identifier. TCPD has already done the painstaking work of assigning stable IDs to politicians across elections since 1962. We match each source to TCPD first, then join everything through that ID.</p>
<p>For sources without TCPD IDs, we use a multi-pass fuzzy matching pipeline: exact name + constituency match first, then normalized name + state + party, then Levenshtein distance with manual review for ambiguous cases.</p>
</section>

<section id="what-we-learned">
<h2>What We Learned</h2>
<ul>
<li><strong>Download before you scrape.</strong> 80% of Indian political data already exists in structured form on GitHub and academic portals. The instinct to build scrapers first wasted time we did not have</li>
<li><strong>Audit your scores before you ship.</strong> The P0 audit was painful but it saved us from shipping a dashboard that would have given voters provably wrong information</li>
<li><strong>Entity resolution is the hardest problem.</strong> Not the ML, not the UI, not the infrastructure. Matching "JYOTIRADITYA M. SCINDIA" to "Shri Jyotiraditya M Scindia" across six datasets is where the real engineering challenge lives</li>
<li><strong>Free tiers are production-ready.</strong> Neon Postgres, Vercel, Cloudflare R2, GitHub Actions -- zero cost, zero compromises for our scale</li>
<li><strong>Data sufficiency gates are non-negotiable.</strong> Never compute a score from incomplete data. Show "insufficient data" instead. Users trust you more when you admit what you do not know</li>
</ul>
</section>
`,
  },
  {
    slug: 'data-insights',
    title: 'When Crime Pays: What 500K Election Records Reveal',
    excerpt:
      'Criminals win elections 2.3x more often. Scindia\'s family wealth grew 10,294%. 147 ghost MPs vanished from records. Here is what half a million data points tell us about Indian democracy.',
    category: 'Data Journey',
    date: '2026-03-22',
    readTime: '10 min read',
    heroImage: '',
    author: authors.team,
    metadata: [
      { label: 'Records Analyzed', value: '500,000+' },
      { label: 'Elections Covered', value: '1962 -- 2024' },
      { label: 'Data Sources', value: '6 official datasets' },
      { label: 'MPs Tracked', value: '4,000+ unique politicians' },
      { label: 'Affidavits Parsed', value: '15,000+' },
      { label: 'Methodology', value: 'Open, auditable' },
    ],
    toc: [
      { id: 'the-criminal-advantage', title: 'The Criminal Advantage' },
      { id: 'the-crorepati-takeover', title: 'The Crorepati Takeover' },
      { id: 'wealth-growth', title: 'Wealth Growth Outliers' },
      { id: 'ghost-mps', title: 'The 147 Ghost MPs' },
      { id: 'party-discipline', title: 'Party Discipline Rankings' },
      { id: 'what-the-data-says', title: 'What the Data Says' },
    ],
    content: `
<section id="the-criminal-advantage">
<h2>The Criminal Advantage</h2>
<p>This is the finding that stops people mid-sentence: <strong>candidates with declared criminal cases win elections 2.3 times more often than clean candidates</strong>.</p>
<p>This is not a bug in the data. It is a consistent pattern across multiple election cycles, confirmed by both our analysis and independent research by ADR (Association for Democratic Reforms). The win rate for candidates with criminal cases is approximately 15.5%, compared to 6.7% for those without.</p>
<ul>
<li><strong>Serious criminal cases</strong> (IPC sections related to murder, kidnapping, extortion) correlate with even higher win rates in certain states</li>
<li><strong>Bihar, UP, and Maharashtra</strong> consistently lead in the proportion of elected MPs with criminal backgrounds</li>
<li><strong>The trend is worsening:</strong> the percentage of MPs with criminal cases has increased from 24% in 2004 to 43% in 2024</li>
</ul>
<p>Why does crime pay at the ballot box? The data suggests three factors: name recognition (criminal cases generate media coverage), the ability to fund expensive campaigns, and the capacity to "get things done" through extra-legal channels -- which voters in under-served constituencies sometimes value over clean governance.</p>
<blockquote>43% of MPs elected in 2024 have declared criminal cases against them. This is not an aberration -- it is the trend line.</blockquote>
</section>

<section id="the-crorepati-takeover">
<h2>The Crorepati Takeover</h2>
<p>A "crorepati" is someone with assets exceeding 1 crore INR (approximately $120,000 USD). In 2004, 30% of elected MPs were crorepatis. By 2024, that number has risen to <strong>93%</strong>.</p>
<p>The median asset declaration for an elected MP in 2024 is approximately INR 5.2 crore. The average is significantly higher, skewed by ultra-wealthy MPs with declarations exceeding INR 1,000 crore.</p>
<ul>
<li><strong>Entry barrier:</strong> Running for Parliament now effectively requires crore-level wealth, shutting out middle-class and lower-income candidates</li>
<li><strong>Campaign spending:</strong> Despite official limits of INR 95 lakh per constituency, actual spending routinely exceeds INR 20-50 crore according to multiple analyses</li>
<li><strong>Party tickets:</strong> Parties increasingly allocate tickets to candidates who can self-fund campaigns, creating a wealth filter before voters even get a choice</li>
</ul>
</section>

<section id="wealth-growth">
<h2>Wealth Growth Outliers</h2>
<p>By comparing successive affidavit declarations, we can track how politicians' declared wealth changes over time. Some of the numbers are staggering.</p>
<ul>
<li><strong>Jyotiraditya Scindia:</strong> Declared assets grew from approximately INR 38 crore to INR 3,950 crore -- a growth of 10,294% across his parliamentary career</li>
<li><strong>Several MPs</strong> show wealth growth rates exceeding 1,000% between consecutive elections, far outpacing any market index or business benchmark</li>
<li><strong>The median wealth growth</strong> for re-elected MPs is approximately 200-300% per term -- still significantly above inflation and market returns</li>
</ul>
<p>To be clear: wealth growth alone does not prove corruption. Legitimate business ventures, inheritance, and market appreciation can explain some growth. But when a salaried MP's declared assets grow by 10,000%, the numbers demand scrutiny.</p>
</section>

<section id="ghost-mps">
<h2>The 147 Ghost MPs</h2>
<p>During our P0 audit, we discovered <strong>147 MPs who existed in election results but could not be matched to any parliamentary activity records</strong>. They won elections. They presumably took office. But in our combined dataset of six sources, they left no trace of parliamentary participation.</p>
<ul>
<li><strong>Zero questions asked</strong> in Parliament</li>
<li><strong>Zero debates participated in</strong></li>
<li><strong>No attendance records</strong> in our dataset</li>
<li><strong>No committee memberships</strong> on record</li>
</ul>
<p>Some of these are data gaps -- MPs from older elections where digital records are sparse. But a significant portion are from recent terms. These are MPs who won a seat in the world's largest democracy and then, by the data's account, disappeared.</p>
<p>This is exactly why Politia uses data sufficiency gates. Rather than scoring these MPs as zero-performers (which might be unfair if records are simply missing), we mark them as "insufficient data" and flag the gap.</p>
</section>

<section id="party-discipline">
<h2>Party Discipline Rankings</h2>
<p>One of the most interesting cross-tabulations: parliamentary participation rates broken down by party affiliation.</p>
<ul>
<li><strong>Communist parties (CPI, CPI-M)</strong> consistently produce the highest-attendance, most-active MPs despite having the fewest seats. Their MPs ask the most questions per capita and participate in the most debates. They also declare the <em>lowest</em> average assets -- the poorest but most disciplined representatives</li>
<li><strong>Regional parties</strong> show high variance: some (like BJD and AIADMK) have strong participation, while others have significant absenteeism</li>
<li><strong>National parties (BJP, INC)</strong> cluster around the median, with wide internal variation depending on individual MPs</li>
</ul>
<p>The correlation between party wealth and parliamentary activity is <em>negative</em>. Parties with wealthier MPs tend to have lower average participation rates. The causation is unclear, but the pattern is persistent.</p>
</section>

<section id="what-the-data-says">
<h2>What the Data Says</h2>
<p>We are not editorializing. Politia does not tell you who to vote for. But the data paints a clear picture:</p>
<ul>
<li><strong>Indian democracy is increasingly a rich person's game.</strong> 93% of MPs are crorepatis. The entry barrier is rising every cycle</li>
<li><strong>Criminal records are an electoral advantage, not a liability.</strong> The 2.3x win rate premium for candidates with criminal cases has been stable for two decades</li>
<li><strong>Parliamentary participation varies wildly.</strong> Some MPs ask 500+ questions per term. Others ask zero. Voters deserve to know which category their representative falls into</li>
<li><strong>Data transparency is still primitive.</strong> The fact that 147 MPs can "vanish" from records shows how much work remains in making Indian democracy truly transparent</li>
</ul>
<p>Every number in this article is derived from official Election Commission affidavits, PRS Legislative Research data, and parliamentary records. The methodology is open. The data is auditable. If a number is wrong, we want to know.</p>
</section>
`,
  },
  {
    slug: 'roadmap',
    title: 'Open Source Roadmap: From 50MB to 16TB',
    excerpt:
      'The plan to build India\'s largest open political data lakehouse -- DuckDB analytics, 17,000 hours of parliament audio, semantic search, OCR pipeline, and how you can contribute.',
    category: 'Open Source',
    date: '2026-03-25',
    readTime: '8 min read',
    heroImage: '',
    author: authors.team,
    metadata: [
      { label: 'Current Size', value: '~50 MB (PostgreSQL)' },
      { label: 'Target Size', value: '16 TB (lakehouse)' },
      { label: 'License', value: 'Open Source' },
      { label: 'Analytics Engine', value: 'DuckDB' },
      { label: 'Audio Data', value: '17,000 hours' },
      { label: 'Phases', value: '5 planned' },
    ],
    toc: [
      { id: 'where-we-are', title: 'Where We Are' },
      { id: 'the-vision', title: 'The Vision' },
      { id: 'phase-1', title: 'Phase 1: Foundation' },
      { id: 'phase-2', title: 'Phase 2: The Lakehouse' },
      { id: 'phase-3', title: 'Phase 3: Audio & NLP' },
      { id: 'phase-4', title: 'Phase 4: Semantic Search' },
      { id: 'phase-5', title: 'Phase 5: Community Scale' },
      { id: 'contributing', title: 'How to Contribute' },
    ],
    content: `
<section id="where-we-are">
<h2>Where We Are</h2>
<p>Politia today runs on a PostgreSQL database that is approximately 50 MB. It contains election results, MP biographical data, parliamentary activity records, asset declarations, and criminal case disclosures from six official data sources. The backend is a FastAPI application with a hexagonal architecture. The frontend is Next.js 16 with React 19 server components.</p>
<p>It works. It is fast. It is free to run. But it is a fraction of what Indian political data could be.</p>
</section>

<section id="the-vision">
<h2>The Vision</h2>
<p>We want to build <strong>India's largest open political data lakehouse</strong> -- a single, queryable repository that contains every piece of public information about every elected representative, from independence to today.</p>
<p>The full dataset, when assembled, would be approximately <strong>16 TB</strong>:</p>
<ul>
<li><strong>Structured data</strong> (~2 GB): Election results, affidavits, attendance records, committee memberships, voting records from 1952 to present</li>
<li><strong>Documents</strong> (~500 GB): Scanned affidavits, FIR copies, property declarations, committee reports in PDF</li>
<li><strong>Parliamentary audio</strong> (~15 TB): Approximately 17,000 hours of Lok Sabha and Rajya Sabha proceedings available from Sansad TV archives</li>
<li><strong>News corpus</strong> (~500 GB): Timestamped news articles about MPs from major outlets, for cross-referencing claims against records</li>
</ul>
<blockquote>The goal is not to hoard data. It is to make every public record about every public servant genuinely, usably public.</blockquote>
</section>

<section id="phase-1">
<h2>Phase 1: Foundation (Current)</h2>
<p>This is where we are today. The core platform with six data sources, the scoring formula v2 with data sufficiency gates, and the accountability dashboard.</p>
<ul>
<li><strong>Done:</strong> Election data ingestion (2004-2024), entity resolution via TCPD IDs, scoring formula v2, P0 audit complete</li>
<li><strong>In progress:</strong> 2019 affidavit data normalization, criminal case severity weighting, MyNeta 2024 scraper</li>
<li><strong>Stack:</strong> FastAPI + PostgreSQL + Next.js 16 on free tiers</li>
</ul>
</section>

<section id="phase-2">
<h2>Phase 2: The Lakehouse</h2>
<p>PostgreSQL is excellent for transactional queries -- "give me this MP's score" -- but it is the wrong tool for analytical queries like "show me wealth growth percentiles by party across all elections since 2004."</p>
<p>Phase 2 introduces <strong>DuckDB</strong> as an analytical layer sitting on Parquet files stored in Cloudflare R2:</p>
<ul>
<li><strong>Parquet export pipeline:</strong> Nightly export from PostgreSQL to columnar Parquet files, optimized for analytical queries</li>
<li><strong>DuckDB for analytics:</strong> In-process OLAP engine that can query Parquet files directly from R2 -- no server needed</li>
<li><strong>Public data API:</strong> Anyone can download the Parquet files and run their own analysis locally with DuckDB</li>
<li><strong>Bulk data downloads:</strong> CSV and Parquet exports available for researchers, journalists, and civic tech projects</li>
</ul>
<p>DuckDB can process analytical queries over millions of rows in milliseconds on a single machine. No Spark cluster needed. No EMR bills. Just files and a binary.</p>
</section>

<section id="phase-3">
<h2>Phase 3: Audio & NLP</h2>
<p>This is the ambitious phase. Indian Parliament has approximately <strong>17,000 hours of recorded proceedings</strong> available through Sansad TV. This audio is currently unsearchable -- you cannot find what your MP said about a specific topic without manually scrubbing through hours of footage.</p>
<ul>
<li><strong>Speech-to-text pipeline:</strong> Whisper large-v3 for transcription, handling Hindi-English code-switching that is ubiquitous in parliamentary proceedings</li>
<li><strong>Speaker diarization:</strong> Identify which MP is speaking at any given moment, linked to our entity database</li>
<li><strong>Topic extraction:</strong> Automated tagging of parliamentary discussions by topic (agriculture, defense, education, etc.)</li>
<li><strong>Searchable transcripts:</strong> Full-text search across all parliamentary proceedings, linked to specific MPs and dates</li>
</ul>
<p>Processing 17,000 hours of audio is expensive at cloud rates. Our plan: community-distributed processing where contributors donate compute cycles, similar to how Folding@Home distributes protein folding calculations.</p>
</section>

<section id="phase-4">
<h2>Phase 4: Semantic Search</h2>
<p>Once we have structured data, documents, and transcripts, the next step is making it all semantically searchable.</p>
<ul>
<li><strong>Vector embeddings</strong> for all text content -- affidavits, transcripts, committee reports</li>
<li><strong>Natural language queries:</strong> "Which MPs spoke about farmer subsidies in the 2023 monsoon session?" returns ranked results with source links</li>
<li><strong>Cross-reference engine:</strong> Automatically flag when an MP's statements in Parliament contradict their affidavit declarations or voting record</li>
<li><strong>Claim verification:</strong> Link political claims to underlying data points -- "MP X says they raised 50 questions" can be verified against the actual parliamentary record</li>
</ul>
</section>

<section id="phase-5">
<h2>Phase 5: Community Scale</h2>
<p>The final phase is about making Politia a platform that the civic tech community owns and extends:</p>
<ul>
<li><strong>State legislature expansion:</strong> Apply the same framework to MLAs across all 28 states and 8 union territories</li>
<li><strong>API marketplace:</strong> Third-party developers can build applications on top of the Politia data layer</li>
<li><strong>OCR pipeline:</strong> Community-driven digitization of older paper records -- affidavits, property declarations, FIRs -- that exist only as scanned images</li>
<li><strong>Journalist toolkit:</strong> Pre-built queries and data exports designed for investigative journalism workflows</li>
<li><strong>Academic access:</strong> Structured datasets with DOIs for citation in political science research</li>
</ul>
</section>

<section id="contributing">
<h2>How to Contribute</h2>
<p>Politia is open source. Here is how you can help:</p>
<ul>
<li><strong>Data normalization:</strong> We have raw datasets that need cleaning. If you know Python and pandas, there is always a CSV that needs wrangling</li>
<li><strong>Frontend development:</strong> The dashboard is Next.js 16 with React 19. We need data visualization components, comparison tools, and mobile UX improvements</li>
<li><strong>Entity resolution:</strong> The hardest problem. Matching politician names across datasets requires both algorithmic approaches and domain knowledge about Indian politics</li>
<li><strong>OCR and document processing:</strong> Older affidavits are scanned PDFs. We need OCR pipelines that handle Hindi, English, and mixed-script documents</li>
<li><strong>Research and validation:</strong> Cross-check our data against known facts. File issues when numbers don't match. The integrity of the platform depends on community verification</li>
</ul>
<p>Start by checking the GitHub issues tagged <code>good-first-issue</code>. Read the methodology page for context on how scores are computed. And if you find a bug in the data, please report it -- the P0 audit taught us that data bugs are the most dangerous kind.</p>
</section>
`,
  },
];

export function getArticleBySlug(slug: string): BlogArticle | undefined {
  return articles.find((a) => a.slug === slug);
}

export function getRelatedArticles(currentSlug: string): BlogArticle[] {
  return articles.filter((a) => a.slug !== currentSlug).slice(0, 3);
}
