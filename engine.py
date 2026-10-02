"""Offline game rules; no Telegram or third-party dependency."""
import json
import random
import re
import sqlite3
import unicodedata
from pathlib import Path

SPECIALTIES = {'medicine': 'Medicine', 'surgery': 'Surgery', 'obgyn': 'Obstetrics & Gynaecology', 'pediatrics': 'Pediatrics'}
LEVELS = ('easy', 'medium', 'hard')
POINTS = (4, 3, 2, 1)
CLUE_SECONDS = 25

def normalize(value):
    value = unicodedata.normalize('NFKD', value.lower())
    value = ''.join(c for c in value if not unicodedata.combining(c))
    value = value.replace("'s", '').replace('’s', '')
    return re.sub(r'[^a-z0-9]', '', value)

def edit_distance(a, b):
    row = list(range(len(b) + 1))
    previous = None
    for i, ca in enumerate(a, 1):
        nxt = [i]
        for j, cb in enumerate(b, 1):
            nxt.append(min(nxt[-1] + 1, row[j] + 1, row[j-1] + (ca != cb)))
            if previous is not None and j > 1 and a[i-1] == b[j-2] and a[i-2] == b[j-1]:
                nxt[j] = min(nxt[j], previous[j-2] + 1)
        previous = row
        row = nxt
    return row[-1]

class Bank:
    def __init__(self, path):
        self.cases = json.loads(Path(path).read_text(encoding='utf-8'))
        self.by_id = {c['id']: c for c in self.cases}
        self.alias_to_diagnoses = {}
        for case in self.cases:
            for alias in case['aliases']:
                self.alias_to_diagnoses.setdefault(normalize(alias), set()).add(case['diagnosis_key'])

    def accepted(self, text, case):
        # A diagnosis, not a sentence or a list of guesses. No substring matching.
        if not text or len(text) > 120 or not re.search('[a-zA-Z]', text):
            return False
        guess = normalize(text.strip())
        expected = {normalize(a) for a in case['aliases']}
        if guess in expected:
            return True
        # Never turn an exact alternative diagnosis into a "typo" of the answer.
        if guess in self.alias_to_diagnoses:
            return False
        # One-character tolerance only for long names. Abbreviations stay exact.
        if len(guess) < 9:
            return False
        candidates = set()
        for alias in self.alias_to_diagnoses:
            if len(alias) >= 9 and abs(len(alias)-len(guess)) <= 1 and edit_distance(guess, alias) <= 1:
                candidates.add(alias)
        return bool(candidates) and candidates <= expected

    def clues(self, case, level):
        f = case['facts']
        if level == 'hard':
            return [f[0], f[1], ' '.join(f[2:4]), ' '.join(f[4:6])]
        if level == 'medium':
            return [' '.join(f[:2]), f[2], f[3], ' '.join(f[4:6])]
        if level == 'easy':
            return [' '.join(f[:3]), f[3], f[4], f[5]]
        raise ValueError('Invalid difficulty')

    def pick(self, specialty, rounds, history, section=None):
        pool = [c for c in self.cases if c['specialty'] == specialty and (not section or c['section'] == section)]
        # No same diagnosis twice within one game, even if variants are added later.
        chosen, used = [], set()
        unseen = [c for c in pool if c['diagnosis_key'] not in history]
        old = [c for c in pool if c['diagnosis_key'] in history]
        random.shuffle(unseen)
        random.shuffle(old)
        for case in unseen + old:
            if case['diagnosis_key'] in used:
                continue
            chosen.append(case['id'])
            used.add(case['diagnosis_key'])
            if len(chosen) == rounds:
                break
        return chosen

class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS settings(scope TEXT PRIMARY KEY, clue_seconds INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(scope TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS seen(scope TEXT, specialty TEXT, diagnosis TEXT,
            PRIMARY KEY(scope, specialty, diagnosis));
        CREATE TABLE IF NOT EXISTS scores(scope TEXT, user_id INTEGER, name TEXT, points INTEGER DEFAULT 0, wins INTEGER DEFAULT 0,
            PRIMARY KEY(scope, user_id));
        ''')
        self.db.commit()

    def clue_time(self, scope, default=25):
        row=self.db.execute('SELECT clue_seconds FROM settings WHERE scope=?',(scope,)).fetchone()
        return row[0] if row else default

    def set_clue_time(self, scope, seconds):
        if not isinstance(seconds,int) or isinstance(seconds,bool) or not 5 <= seconds <= 600:
            raise ValueError('Time must be an integer between 5 and 600 seconds')
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',(scope,seconds))

    def save(self, scope, game):
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO sessions VALUES (?,?)', (scope, json.dumps(game, ensure_ascii=False)))

    def delete(self, scope):
        with self.db:
            self.db.execute('DELETE FROM sessions WHERE scope=?', (scope,))

    def sessions(self):
        return {k: json.loads(v) for k, v in self.db.execute('SELECT scope,payload FROM sessions')}

    def history(self, scope, specialty):
        return {r[0] for r in self.db.execute('SELECT diagnosis FROM seen WHERE scope=? AND specialty=?', (scope, specialty))}

    def mark_seen(self, scope, specialty, diagnosis, available):
        # Reset a cycle only when the entire specialty has been seen.
        if available and available <= self.history(scope, specialty):
            with self.db:
                self.db.execute('DELETE FROM seen WHERE scope=? AND specialty=?', (scope, specialty))
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO seen VALUES (?,?,?)', (scope, specialty, diagnosis))

    def award(self, scope, user_id, name, points):
        with self.db:
            self.db.execute('''INSERT INTO scores VALUES (?,?,?,?,1)
                ON CONFLICT(scope,user_id) DO UPDATE SET name=excluded.name,
                points=scores.points+excluded.points,wins=scores.wins+1''', (scope, user_id, name, points))

    def settle(self, scope, game, winner=None):
        # Session progress and the lifetime score are one atomic commit.
        with self.db:
            if winner:
                self.db.execute('''INSERT INTO scores VALUES (?,?,?,?,1)
                    ON CONFLICT(scope,user_id) DO UPDATE SET name=excluded.name,
                    points=scores.points+excluded.points,wins=scores.wins+1''',
                    (scope, winner['uid'], winner['name'], winner['points']))
            self.db.execute('INSERT OR REPLACE INTO sessions VALUES (?,?)', (scope,json.dumps(game,ensure_ascii=False)))

    def board(self, scope):
        return list(self.db.execute('SELECT name,points,wins FROM scores WHERE scope=? ORDER BY points DESC,wins DESC,user_id ASC LIMIT 15', (scope,)))

def scope_key(chat_id, thread_id=None):
    # The General forum topic may be represented by None or 1.
    return f'{chat_id}:{0 if thread_id in (None, 1) else thread_id}'
