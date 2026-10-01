# Version 2.0 — 2026-10-01

- Added 121 sourced Arabic event and transfer clues for 2024–2026, including 56 for 2026.
- Preserved all 700 players, 110 clubs, aliases, IDs and 3240 original clues.
- Mixes old and new clues by difficulty; prefers unused supplemented questions with configurable probability.
- Separate games, scores, used questions, setup menus and reset confirmations for every group topic.
- Routes scheduled questions and restart notices to the originating topic, without General fallback.
- Automatically migrates old SQLite records to General, preserving history and scores.
- 13 local tests passed, including topic isolation, reply routing, clue mixing and migration.
- Live Telegram connection requires the operator's token and was not tested in this delivery.
