import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { articles, getArticleBySlug, getRelatedArticles } from '@/lib/blog-data';
import styles from '../blog.module.css';

type Props = {
  params: Promise<{ slug: string }>;
};

export async function generateStaticParams() {
  return articles.map((article) => ({ slug: article.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const article = getArticleBySlug(slug);
  if (!article) return { title: 'Not Found - Politia' };
  return {
    title: `${article.title} - Politia Blog`,
    description: article.excerpt,
  };
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export default async function BlogPostPage({ params }: Props) {
  const { slug } = await params;
  const article = getArticleBySlug(slug);

  if (!article) {
    notFound();
  }

  const related = getRelatedArticles(slug);
  const shareUrl = `https://politia.in/blog/${slug}`;
  const shareText = encodeURIComponent(article.title);

  return (
    <div className={styles.postPage}>
      {/* Breadcrumb */}
      <nav className={styles.postBreadcrumb} aria-label="Breadcrumb">
        <Link href="/">Home</Link>
        <span className={styles.breadcrumbSep}>/</span>
        <Link href="/blog">Blog</Link>
        <span className={styles.breadcrumbSep}>/</span>
        <span>{article.title}</span>
      </nav>

      {/* Hero */}
      <header className={styles.postHero}>
        <span className={styles.postCategory}>{article.category}</span>
        <h1 className={styles.postTitle}>{article.title}</h1>
        <div className={styles.postMeta}>
          <div className={styles.postAuthor}>
            <div className={styles.authorAvatar}>
              {article.author.name
                .split(' ')
                .map((w) => w[0])
                .join('')
                .slice(0, 2)}
            </div>
            <div className={styles.authorInfo}>
              <span className={styles.authorName}>{article.author.name}</span>
              <span className={styles.authorRole}>{article.author.role}</span>
            </div>
          </div>
          <span className={styles.postDate}>{formatDate(article.date)}</span>
          <span className={styles.postReadTime}>{article.readTime}</span>
        </div>
      </header>

      {/* Two-column layout */}
      <div className={styles.postLayout}>
        {/* Main content */}
        <article
          className={styles.postContent}
          dangerouslySetInnerHTML={{ __html: article.content }}
        />

        {/* Sidebar */}
        <aside className={styles.postSidebar}>
          {/* Metadata */}
          <div className={styles.metadataCard}>
            <div className={styles.metadataCardTitle}>Overview</div>
            {article.metadata.map((item) => (
              <div key={item.label} className={styles.metadataItem}>
                <span className={styles.metadataLabel}>{item.label}</span>
                <span className={styles.metadataValue}>{item.value}</span>
              </div>
            ))}
          </div>

          {/* Social share */}
          <div className={styles.shareCard}>
            <div className={styles.shareTitle}>Share</div>
            <div className={styles.shareButtons}>
              <a
                href={`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.shareBtn}
                aria-label="Share on LinkedIn"
                title="LinkedIn"
              >
                in
              </a>
              <a
                href={`https://twitter.com/intent/tweet?text=${shareText}&url=${encodeURIComponent(shareUrl)}`}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.shareBtn}
                aria-label="Share on X"
                title="X (Twitter)"
              >
                X
              </a>
              <a
                href={`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.shareBtn}
                aria-label="Share on Facebook"
                title="Facebook"
              >
                f
              </a>
            </div>
          </div>

          {/* Table of Contents */}
          <div className={styles.tocCard}>
            <div className={styles.tocTitle}>On this page</div>
            <ul className={styles.tocList}>
              {article.toc.map((item) => (
                <li key={item.id} className={styles.tocItem}>
                  <a href={`#${item.id}`} className={styles.tocLink}>
                    {item.title}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </aside>
      </div>

      {/* Related articles */}
      <section className={styles.relatedSection}>
        <h2 className={styles.relatedTitle}>More from the blog</h2>
        <div className={styles.relatedGrid}>
          {related.map((rel) => (
            <Link
              key={rel.slug}
              href={`/blog/${rel.slug}`}
              className={styles.relatedCardLink}
            >
              <div className={styles.relatedCard}>
                <span className={styles.relatedCardCategory}>
                  {rel.category}
                </span>
                <h3 className={styles.relatedCardTitle}>{rel.title}</h3>
                <p className={styles.relatedCardExcerpt}>{rel.excerpt}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
