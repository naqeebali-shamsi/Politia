# Politia Promotional Posts

---

## Section 1: r/SideProject

**Title:** [Politia] - Open-source Indian MP accountability dashboard, 500K election records, $0/month to run

I wanted a simple answer to "what has my MP actually done?" and found that India's political data is scattered across a dozen government portals, PDFs, and websites that nobody has time to piece together. So I spent a few months building Politia.

Live: https://politia.vercel.app
GitHub: https://github.com/naqeebali-shamsi/Politia

What it does: pulls together 500K+ election records going back to the 1950s, 296K parliamentary questions with semantic search, wealth disclosures from affidavits, criminal case data, attendance records, and a scoring engine that weights it all into a transparent composite score. Every score links back to source data. No black boxes.

The most interesting finding: candidates with criminal cases win elections at 2.3x the rate of clean candidates. That's not an opinion -- that's what falls out of the data across multiple election cycles.

Stack: FastAPI (hexagonal architecture), PostgreSQL on Neon with pgvector for 42K+ semantic embeddings, DuckDB as a local lakehouse (sub-15ms on 500K records), Next.js 16 + React 19 frontend on Vercel, IsolationForest for wealth anomaly detection, GeoJSON maps for all 543 constituencies. 204 automated tests. The entire thing runs on free tiers -- Neon, Render, Vercel. Total cost: $0/month.

I pair-programmed most of this with Claude Code, which honestly changed how fast I could ship as a solo dev. Entity resolution across inconsistent government datasets -- where the same politician is "Rahul Gandhi", "Sh. Rahul Gandhi", and "GANDHI, RAHUL" in three different sources -- would have taken months to untangle alone.

What's not done yet: 17,000 hours of parliament debate audio needs Whisper transcription, 500K affidavit PDFs need OCR, and semantic search needs more compute to scale past Neon's free tier.

I could use help with contributions (repo has tagged issues and documented architecture). Also looking for a domain sponsor -- politia.in is available but the budget for this project is literally zero, so if anyone knows of free/sponsored domain programs for open-source civic tech, I'd appreciate a pointer.

---

## Section 2: r/opensource

**Flair:** Promotional

**Title:** Politia: open-source Indian MP accountability dashboard looking for contributors -- data engineering, ML, frontend, and infrastructure

Politia is an open-source dashboard that scores Indian Members of Parliament using publicly available data -- election records, wealth disclosures, criminal cases, attendance, parliamentary questions. Everything traced back to official sources, no editorializing.

GitHub: https://github.com/naqeebali-shamsi/Politia
Live demo: https://politia.vercel.app
API docs: https://politia-api.onrender.com/docs
License: MIT

**Where contributions would have the most impact right now:**

- **Data engineering:** We have 17,000 hours of parliament debate audio sitting unprocessed (needs Whisper transcription pipeline) and 500K affidavit PDFs that need OCR. The entity resolution pipeline (rapidfuzz + sentence-transformers) can ingest new sources, but someone who's worked with Indian government data formats would be invaluable.

- **ML/Data science:** The wealth anomaly detection uses IsolationForest and flagged 547 suspicious patterns. There's room to improve the scoring model and add new signal types. The semantic search runs on pgvector with 42K+ embeddings across 296K parliamentary questions -- scaling this is an open problem.

- **Frontend:** Next.js 16 + React 19. The constituency maps (GeoJSON for all 543 seats) need work, and there are UX improvements tagged in issues. Side-by-side MP comparison and leaderboard views are live but could be better.

- **Infrastructure:** This runs entirely on free tiers ($0/month -- Neon, Render, Vercel). That's great for accessibility but it means we can't run the transcription or OCR pipelines. If you work at a company that sponsors open-source compute, or if you have ideas for free GPU access, that would unblock the biggest chunk of the roadmap.

**What's already built:**

FastAPI backend with hexagonal architecture (ports and adapters), PostgreSQL/pgvector on Neon, DuckDB lakehouse for analytics, 204 automated tests with TDD throughout. The codebase is structured to be contributor-friendly -- clean separation of concerns, documented architecture, tagged issues.

The dataset covers 500K+ election records from the 1950s to present, with some gaps in post-2019 state data. The scoring system is transparent and every metric is sourced.

CONTRIBUTING.md, issue templates, code of conduct, and architecture docs are all in the repo. Built solo with Claude Code as a pair programmer -- looking to turn this into a proper community project.

---

## Section 3: r/developersIndia

**Title:** We have 70 years of election data but no easy way to hold our MPs accountable -- so I built an open-source dashboard

**Note to self:** Post in the Showcase Sunday megathread. Timing matters -- post early Sunday morning IST for maximum visibility.

Every election season we argue about candidates based on WhatsApp forwards, but the actual data -- attendance, wealth disclosures, criminal cases, questions asked -- is buried in government PDFs that nobody digs through. I spent a few months building Politia to fix that.

Live: https://politia.vercel.app
GitHub: https://github.com/naqeebali-shamsi/Politia

**What the data shows (some of this genuinely surprised me):**

The crorepati share among Lok Sabha candidates went from 12.6% in 2004 to 45.7% in 2019. Scindia went from declaring 3.6 Cr in 2004 to 374.6 Cr in 2019 -- that's 10,294% growth while drawing an MP salary. The wealth anomaly model (IsolationForest) flagged 547 patterns like this.

Criminal candidates win at 2.3x the rate of clean candidates. Across parties, states, decades -- it's structural.

147 "Ghost MPs" -- elected members who never asked a single question or participated in a debate. Your taxes paid their salary.

Two elections in Indian history were decided by exactly 9 votes each.

Communist MPs are the poorest (0.3 Cr average assets) but most disciplined with 85% average attendance. Make of that what you will.

**Tech stack:** FastAPI with hexagonal architecture, Postgres/pgvector on Neon (42K+ embeddings across 296K parliamentary questions), DuckDB lakehouse for analytics (sub-15ms on 500K records), Next.js 16 + React 19 frontend, GeoJSON maps for all 543 constituencies. 204 tests, TDD throughout. Total infra cost: ₹0/month. Everything on free tiers.

Built with Claude Code as my pair programmer. Entity resolution across Indian government datasets -- where "Rahul Gandhi", "Sh. Rahul Gandhi", and "GANDHI, RAHUL" are the same person across three sources -- would have taken months alone.

**Where I need help:** This is MIT-licensed and I want Indian devs involved. Tagged issues in the repo for all skill levels. Big unlocks: Whisper transcription for 17K hours of parliament audio, OCR for 500K affidavit PDFs, newer ECI data, state assembly datasets. If your company can sponsor some compute, that would unblock the transcription pipeline entirely.

The goal: every constituency in India gets a data-backed scorecard for their representative. Not opinions, just public records presented transparently. We're about 40% there with Lok Sabha. State assemblies are next.

---

## Section 4: r/india

**Title:** Almost half of Lok Sabha candidates are now crorepatis, up from 12.6% in 2004 -- and candidates with criminal cases win at 2.3x the rate of clean ones

In 2004, about 12.6% of Lok Sabha candidates declared assets over 1 crore. By 2019, that number hit 45.7%. That's not inflation -- the rate of increase far outpaces it.

I've been digging through publicly available election data going back to the 1950s -- around 500K records total -- and some patterns are hard to ignore:

Candidates with criminal cases win elections at 2.3 times the rate of candidates without cases. This holds across parties and states. It's not a partisan thing, it's structural.

There are 147 sitting or former MPs who never asked a single parliamentary question or participated in a debate during their entire term. Never. Not once.

One MP's declared wealth grew by over 10,000% across three elections while serving in office.

Two elections in Indian history were decided by exactly 9 votes each -- so yes, your vote does matter.

Communist MPs turn out to be the poorest (0.3 Cr average assets) but have the highest discipline at 85% average attendance.

I ended up building a small open-source tool to make this data searchable: https://politia.vercel.app -- it pulls together election records, wealth disclosures from affidavits, criminal cases, attendance, and parliamentary questions into one place. The scoring methodology is public and I'm actively looking for feedback on whether it's fair. Code is at https://github.com/naqeebali-shamsi/Politia if anyone wants to poke at it. Runs on a budget of zero rupees per month.

All of this comes from publicly available government data (Election Commission, Lok Sabha archives, ADR). No editorializing, no party bias -- just the numbers.

If you work with election data or civic tech, or if you just want to tell me the scoring is wrong, I'd love to hear from you.

---

## Section 5: X/Twitter Thread

**Tweet 1:**
Criminal candidates win Indian elections at 2.3x the rate of clean candidates. Not for one party -- across all parties, all states, all decades. I analyzed 500K+ election records going back to 1951. Here's what the data shows. https://politia.vercel.app

**Tweet 2:**
In 2004, 12.6% of Lok Sabha candidates declared assets over 1 crore. By 2019, it was 45.7%. One MP's declared wealth grew 10,294% across three elections -- from 3.6 Cr to 374.6 Cr -- while drawing an MP salary.

**Tweet 3:**
147 "Ghost MPs" -- elected members who never asked a single parliamentary question or participated in a single debate during their entire term. They collected their salary and did nothing on the record. Your taxes paid for that.

**Tweet 4:**
Two elections in Indian history were decided by exactly 9 votes each. Your vote literally decides elections. Not metaphorically -- mathematically.

**Tweet 5:**
Communist MPs are the poorest (0.3 Cr avg assets) but most disciplined at 85% average attendance. The data doesn't care about narratives.

**Tweet 6:**
I built Politia to make this data searchable -- 500K election records, 296K parliamentary questions with semantic search, wealth disclosures, criminal cases, attendance. All sourced to official records. MIT licensed. Runs on $0/month infrastructure.

**Tweet 7:**
Built solo with Claude Code. FastAPI + pgvector + DuckDB + Next.js 16. 204 tests. The hardest part was entity resolution -- the same politician appears as three different names across government databases.

**Tweet 8:**
GitHub: https://github.com/naqeebali-shamsi/Politia
API docs: https://politia-api.onrender.com/docs
Looking for contributors -- data engineers, ML folks, frontend devs. The big unlock is 17K hours of unprocessed parliament audio.
#OpenSource #CivicTech #India #BuildInPublic

---

## Section 6: Posting Strategy

**Order of posting:**

1. **r/SideProject** -- Post first. Most welcoming community, good for early traction and upvotes. Post on a weekday morning US time (Tuesday-Thursday, 9-11am EST). Video demo would significantly boost engagement here -- record a 60-90 second walkthrough if possible.

2. **r/opensource** -- Post same day or next day. Use "Promotional" flair. This audience cares about contribution pathways, not just the product.

3. **r/developersIndia** -- Wait for Sunday. Post in the Showcase Sunday megathread early morning IST (8-9am). This is the most engaged audience for the technical details and the Indian data angle.

4. **r/india** -- Post 2-3 days after r/developersIndia. IMPORTANT: You need a 1:10 self-promotion ratio. Before posting, make at least 10 genuine comments/posts on other r/india threads. Lead with data, not the tool. The title should read like a news headline, not a product launch.

5. **X/Twitter thread** -- Post the same day as r/india or r/developersIndia for cross-pollination. Best times: 9-11am IST or 9-11am EST depending on target audience. Pin the thread.

**Before each post:**

- Hit the live site (https://politia.vercel.app) and the API (https://politia-api.onrender.com/docs) 5-10 minutes before posting. Free tier services cold-start, and you do not want the first visitor to hit a 30-second loading screen.
- Test the semantic search with a query or two to warm the embeddings endpoint.
- Verify the GitHub README is current and the tagged issues are up to date.

**Post-posting:**

- Respond to every comment within the first 2 hours. Reddit algorithm favors active threads.
- If someone asks a technical question, give a real answer -- this is the builder community, they'll know if you're deflecting.
- Don't cross-link between Reddit posts (mods don't like it). Each post should stand alone.
- Track which data points get the most engagement -- that tells you what to lead with next time.

**Additional subreddits to consider later:**

- r/datascience -- lead with the anomaly detection, entity resolution, and DuckDB lakehouse angles
- r/civictech -- small but highly targeted
- Hacker News "Show HN" -- focus on technical architecture and civic impact, HN crowd respects the $0 infrastructure angle
