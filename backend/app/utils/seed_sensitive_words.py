"""Seed the sensitive_words table with a baseline list.

Run: python -m app.utils.seed_sensitive_words
"""

from ..extensions import db
from ..models import SensitiveWord

BASELINE_WORDS: list[dict] = [
    # Populate with actual sensitive words as needed.
    # Categories: political, porn, violence, spam, other
    # Levels: low, medium, high
]

def seed_sensitive_words():
    existing = {row.word for row in db.session.query(SensitiveWord.word).all()}
    added = 0
    for entry in BASELINE_WORDS:
        word = entry.get("word", "").strip()
        if not word or word in existing:
            continue
        db.session.add(SensitiveWord(
            word=word,
            category=entry.get("category", "other"),
            level=entry.get("level", "medium"),
        ))
        added += 1
    db.session.commit()
    return added


if __name__ == "__main__":
    from .. import create_app

    app = create_app()
    with app.app_context():
        count = seed_sensitive_words()
        print(f"Seeded {count} sensitive words")
