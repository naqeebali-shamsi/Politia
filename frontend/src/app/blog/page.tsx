import type { Metadata } from 'next';
import Link from 'next/link';
import { articles } from '@/lib/blog-data';
import styles from './blog.module.css';

export const metadata: Metadata = {
  title: 'Blog - Politia',
  description:
    'Architecture deep-dives, data insights, and the open source roadmap behind India\'s MP accountability platform.',
};

const categoryIcons: Record<string, string> = {
  Architecture: 'Arch',
  'Data Journey': 'Data',
  'Open Source': 'OSS',
};

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export default function BlogIndexPage() {
  return (
    <div className={styles.blogIndex}>
      <header className={styles.blogIndexHeader}>
        <h1 className={styles.blogIndexTitle}>Blog</h1>
        <p className={styles.blogIndexSubtitle}>
          Architecture decisions, data investigations, and the roadmap for
          building India's most comprehensive political accountability platform.
        </p>
      </header>

      <div className={styles.articlesGrid}>
        {articles.map((article) => (
          <Link
            key={article.slug}
            href={`/blog/${article.slug}`}
            className={styles.articleCardLink}
          >
            <article className={styles.articleCard}>
              <div className={styles.articleCardImage}>
                <span className={styles.articleCardImageIcon}>
                  {categoryIcons[article.category] || 'P'}
                </span>
              </div>
              <div className={styles.articleCardBody}>
                <span className={styles.articleCardCategory}>
                  {article.category}
                </span>
                <h2 className={styles.articleCardTitle}>{article.title}</h2>
                <p className={styles.articleCardExcerpt}>{article.excerpt}</p>
                <div className={styles.articleCardMeta}>
                  <span>{formatDate(article.date)}</span>
                  <span>{article.readTime}</span>
                </div>
              </div>
            </article>
          </Link>
        ))}
      </div>
    </div>
  );
}
