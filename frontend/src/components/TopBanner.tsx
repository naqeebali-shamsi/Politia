'use client';

import { useState, useEffect } from 'react';

const STORAGE_KEY = 'politia-top-banner-dismissed';

export default function TopBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const dismissed = localStorage.getItem(STORAGE_KEY);
    if (!dismissed) {
      setVisible(true);
    }
  }, []);

  const dismiss = () => {
    setVisible(false);
    localStorage.setItem(STORAGE_KEY, '1');
  };

  if (!visible) return null;

  return (
    <div className="top-banner">
      <div className="top-banner-inner">
        <span className="top-banner-text">
          Open source civic tech &mdash;{' '}
          <a
            href="https://github.com/naqeebali-shamsi/Politia"
            target="_blank"
            rel="noopener noreferrer"
          >
            contribute on GitHub
          </a>
        </span>
        <button
          className="top-banner-close"
          onClick={dismiss}
          aria-label="Dismiss banner"
        >
          &times;
        </button>
      </div>
    </div>
  );
}
