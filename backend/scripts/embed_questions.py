"""
Batch-embed all question_records titles using paraphrase-multilingual-MiniLM-L12-v2.

Usage:
    python -m scripts.embed_questions

Idempotent: skips rows that already have an embedding.
Commits after each batch so progress is preserved on interrupt.
Estimated time: ~2-4 hours for 296K questions on CPU.
"""

import os
import sys
import signal
import time

# Ensure the backend package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.infrastructure.database.session import get_engine


# Graceful shutdown flag
_shutdown = False


def _handle_signal(signum, frame):
    global _shutdown
    print(f"\nReceived signal {signum} -- finishing current batch then exiting.")
    _shutdown = True


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def main():
    from sentence_transformers import SentenceTransformer

    model_name = "paraphrase-multilingual-MiniLM-L12-v2"
    batch_size = 1000
    encode_batch_size = 256

    print(f"Loading model: {model_name} ...")
    model = SentenceTransformer(model_name)
    print("Model loaded.")

    engine = get_engine()

    # Count total and remaining
    with engine.connect() as conn:
        total = conn.execute(text("SELECT count(*) FROM question_records")).scalar()
        remaining = conn.execute(
            text("SELECT count(*) FROM question_records WHERE embedding IS NULL AND question_title IS NOT NULL")
        ).scalar()
        print(f"Total questions: {total:,}")
        print(f"Remaining to embed: {remaining:,}")

    embedded_count = 0
    start_time = time.time()

    while not _shutdown:
        with engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT id, question_title
                    FROM question_records
                    WHERE embedding IS NULL AND question_title IS NOT NULL
                    ORDER BY id
                    LIMIT :batch_size
                """),
                {"batch_size": batch_size},
            ).fetchall()

        if not rows:
            print("All questions embedded.")
            break

        ids = [r[0] for r in rows]
        titles = [r[1] for r in rows]

        # Encode
        embeddings = model.encode(titles, batch_size=encode_batch_size, show_progress_bar=True)

        # Update in a single transaction
        with engine.connect() as conn:
            for row_id, emb in zip(ids, embeddings):
                emb_str = "[" + ",".join(str(float(x)) for x in emb) + "]"
                conn.execute(
                    text("UPDATE question_records SET embedding = :emb WHERE id = :id"),
                    {"emb": emb_str, "id": row_id},
                )
            conn.commit()

        embedded_count += len(ids)
        elapsed = time.time() - start_time
        rate = embedded_count / elapsed if elapsed > 0 else 0

        if embedded_count % 10000 < batch_size:
            print(
                f"  Progress: {embedded_count:,} embedded "
                f"({elapsed:.0f}s elapsed, {rate:.0f} q/s, "
                f"~{(remaining - embedded_count) / max(rate, 1):.0f}s remaining)"
            )

    elapsed = time.time() - start_time
    print(f"\nDone. Embedded {embedded_count:,} questions in {elapsed:.0f}s.")


if __name__ == "__main__":
    main()
