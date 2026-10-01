"""Offline game rules and SQLite persistence. No Telegram dependency."""
import json
import random
import re
import sqlite3
import unicodedata
from pathlib import Path

POINTS = (40, 30, 20, 10)


def normalize(text):
    text = unicodedata.normalize('NFKD', text.casefold())
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.translate(str.maketrans({'أ':'ا','إ':'ا','آ':'ا','ى':'ي','ة':'ه','ؤ':'و','ئ':'ي','ـ':''}))
    return re.sub(r'[^a-z0-9\u0621-\u064a]', '', text)


class Bank:
    def __init__(self, directory):
        self.items = {}
        self.aliases = {}
        for mode in ('players', 'clubs'):
            rows = json.loads((Path(directory) / f'{mode}.json').read_text(encoding='utf-8'))
            assert rows and len({r['id'] for r in rows}) == len(rows), 'Duplicate IDs'
            for r in rows:
                assert len(r['clues']) == 4 and all(isinstance(c, str) and c.strip() for c in r['clues'])
                assert r['answer'] and r['aliases']
                for clue in r.get('extra_clues', []):
                    assert 1 <= clue['difficulty'] <= 4 and clue['text'].strip()
                    assert clue.get('source_url') and clue.get('event_year')
            self.items[mode] = {r['id']: r for r in rows}
            index = {}
            for r in rows:
                for a in r['aliases'] + [r['answer']]:
                    n = normalize(a)
                    if len(n) >= 3:
                        index.setdefault(n, set()).add(r['id'])
            self.aliases[mode] = index

    def matches(self, mode, item, text):
        # Exact normalized aliases only: don't accept an arbitrary substring.
        matches = self.aliases[mode].get(normalize(text), set())
        return matches == {item['id']}

    def choose_clues(self, item):
        """Keep 4 difficulty tiers, mix old + new, without overwriting old data."""
        selected = list(item['clues'])
        pools = {}
        for clue in item.get('extra_clues', []):
            pools.setdefault(clue['difficulty'] - 1, []).append(clue['text'])
        if pools:
            rng = random.SystemRandom()
            # Always use >=1 new clue when available and retain >=1 old clue.
            slots = rng.sample(list(pools), rng.randint(1, min(3, len(pools))))
            for slot in slots:
                selected[slot] = rng.choice(pools[slot])
        return selected


def split_scope(scope):
    """Legacy chat IDs remain compatible; new games use (chat_id, topic_id)."""
    return scope if isinstance(scope, tuple) else (scope, 0)


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute('PRAGMA journal_mode=WAL')
        self._migrate()

    def _migrate(self):
        # Atomic one-time migration: old group history belongs to General (topic 0).
        self.db.execute('BEGIN IMMEDIATE')
        try:
            for table in ('used', 'scores', 'active'):
                columns = {x[1] for x in self.db.execute(f'PRAGMA table_info({table})')}
                if columns and 'topic' not in columns:
                    self.db.execute(f'ALTER TABLE {table} RENAME TO {table}_legacy')
            self.db.execute('''CREATE TABLE IF NOT EXISTS used(
                chat INTEGER, topic INTEGER, mode TEXT, item TEXT,
                PRIMARY KEY(chat,topic,mode,item))''')
            self.db.execute('''CREATE TABLE IF NOT EXISTS scores(
                chat INTEGER, topic INTEGER, user INTEGER, name TEXT, points INTEGER,
                PRIMARY KEY(chat,topic,user))''')
            self.db.execute('''CREATE TABLE IF NOT EXISTS active(
                chat INTEGER, topic INTEGER, PRIMARY KEY(chat,topic))''')
            for table, fields in [('used','chat,mode,item'),('scores','chat,user,name,points'),('active','chat')]:
                exists = self.db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (table+'_legacy',)).fetchone()
                if exists:
                    other = fields.split(',')[1:]
                    expression = 'chat,0' + (','+','.join(other) if other else '')
                    self.db.execute(f'INSERT INTO {table} SELECT {expression} FROM {table}_legacy')
                    self.db.execute(f'DROP TABLE {table}_legacy')
            self.db.execute('PRAGMA user_version=2')
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def remaining(self, chat, mode, bank):
        used = {x[0] for x in self.db.execute('SELECT item FROM used WHERE chat=? AND topic=? AND mode=?', (*split_scope(chat), mode))}
        return [x for x in bank.items[mode] if x not in used]

    def draw(self, chat, mode, bank, recent_share=0.5):
        available = self.remaining(chat, mode, bank)
        if not available:
            return None
        # Give the verified supplement a fair chance to appear, not ~1/700.
        recent = [key for key in available if bank.items[mode][key].get('extra_clues')]
        rng = random.SystemRandom()
        pool = recent if recent and rng.random() < recent_share else available
        key = rng.choice(pool)
        with self.db:
            self.db.execute('INSERT INTO used VALUES(?,?,?,?)', (*split_scope(chat), mode, key))
        return bank.items[mode][key]

    def score(self, chat, user, name, points):
        with self.db:
            self.db.execute('''INSERT INTO scores VALUES(?,?,?,?,?)
                ON CONFLICT(chat,topic,user) DO UPDATE SET
                name=excluded.name,points=scores.points+excluded.points''', (*split_scope(chat),user,name,points))

    def leaders(self, chat):
        return list(self.db.execute('SELECT name,points FROM scores WHERE chat=? AND topic=? ORDER BY points DESC,user ASC LIMIT 10', split_scope(chat)))

    def reset_used(self, chat, mode):
        with self.db:
            self.db.execute('DELETE FROM used WHERE chat=? AND topic=? AND mode=?', (*split_scope(chat),mode))

    def mark_active(self, chat, active):
        with self.db:
            if active:
                self.db.execute('INSERT OR IGNORE INTO active VALUES(?,?)', split_scope(chat))
            else:
                self.db.execute('DELETE FROM active WHERE chat=? AND topic=?', split_scope(chat))

    def interrupted(self):
        return list(self.db.execute('SELECT chat,topic FROM active'))

    def backup(self, destination):
        # SQLite backup includes committed WAL data, unlike copying just .sqlite3.
        target = sqlite3.connect(destination)
        self.db.backup(target)
        target.close()

    def close(self):
        self.db.close()
