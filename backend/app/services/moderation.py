import logging
import threading

import ahocorasick

from ..extensions import db
from ..models import SensitiveWord

logger = logging.getLogger(__name__)

_automaton_lock = threading.Lock()
_automaton: ahocorasick.Automaton | None = None


def _build_automaton() -> ahocorasick.Automaton:
    auto = ahocorasick.Automaton()
    words = (
        db.session.query(SensitiveWord.word)
        .filter(SensitiveWord.is_active.is_(True))
        .all()
    )
    for (word,) in words:
        auto.add_word(word, word)
    auto.make_automaton()
    return auto


def get_automaton() -> ahocorasick.Automaton:
    global _automaton
    with _automaton_lock:
        if _automaton is None:
            _automaton = _build_automaton()
        return _automaton


def reload_automaton():
    global _automaton
    with _automaton_lock:
        _automaton = _build_automaton()
    logger.info("Moderation automaton reloaded")


def scan(text: str) -> list[str]:
    auto = get_automaton()
    if auto is None or len(auto) == 0:
        return []
    found = set()
    for _, matched in auto.iter(text):
        found.add(matched)
    return sorted(found)
