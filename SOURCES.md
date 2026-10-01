# Sources and data scope

## Historical player records

The 624 biography-based entries are derived from factual identity fields in a
FIFA 22 / SoFIFA-based 2021 snapshot. Only identity and biographical fields are
used; game skill ratings, market values and photos are not included in the delivered bank.
Clubs and kit numbers are explicitly dated to this snapshot in the clues.
Brazilian domestic league records were excluded because FIFA editions can contain
fictional/unlicensed domestic player identities. The initial displayed names were
reviewed and common football names/Arabic aliases were added.

- Dataset mirror used: https://github.com/MakuG/fifa22/blob/main/players_22.csv
- Dataset publisher: https://www.kaggle.com/datasets/stefanoleone992/fifa-22-complete-player-dataset
- Underlying profile provider: https://sofifa.com/

Names and biographical facts are transformed into original Arabic clue sentences.
No claim is made that all 700 player biographies have been independently checked
against 700 official profiles, or that these are October 2026 squad lists.

## Authored historical questions

76 player entries use manually written historical career and achievement clues.
These include retired players active during the requested period and selected
younger stars absent from the 2021 snapshot. Clubs use historical identity facts;
founding dates can refer to predecessors/roots (e.g. Red Bull Salzburg), and
stadiums can be historical rather than current homes. Sources for checking and
improving individual entries include the relevant official club histories and:

- FIFA World Cup history and player articles: https://www.fifa.com/
- UEFA competition/player history: https://www.uefa.com/
- Premier League statistics and records: https://www.premierleague.com/
- FC Barcelona player/club history: https://www.fcbarcelona.com/
- Real Madrid player/club history: https://www.realmadrid.com/

These links describe provenance/reference resources, not a claim that every
handwritten clue was individually retrieved from each of these sites during this build.

## Verified modern supplement (v2)

121 original Arabic clues were added without changing any original clue, alias or ID.
They cover 64 players and 16 clubs: 56 clues concern 2026, 42 concern 2025 and 23 concern 2024.
Official club, FIFA, UEFA and Premier League pages were retrieved on 2026-10-01.
Each extra clue records its event year, source URL, difficulty and checking date.

- `data/modern_clues.csv`: every new clue with its source and year.
- `data/modern_sources.json`: exact primary-source URLs used.
- `add_modern_clues.py`: reproducible, idempotent supplement builder; it uses the packaged facts and does not fetch live updates.

Original 2021 snapshot facts remain explicitly dated. This selective supplement does
not turn all 700 entries into current squad or transfer records. A source's checking
date is separate from the event year. New clue slots are sampled by difficulty while
retaining at least one original clue in each supplemented round.

## Software documentation

- python-telegram-bot Application API (22.8):
  https://docs.python-telegram-bot.org/en/stable/telegram.ext.application.html
- Telegram Bot features and group privacy:
  https://core.telegram.org/bots/features#privacy-mode

- Telegram topic IDs and the General topic:
  https://core.telegram.org/api/forum
- Bot API message routing:
  https://core.telegram.org/bots/api#sendmessage
- python-telegram-bot Message reply routing:
  https://docs.python-telegram-bot.org/en/stable/telegram.message.html

## License

The bot's original code and original Arabic clue wording are provided under the
MIT license in LICENSE. That license does not assert ownership of third-party
data, player identities, club names or trademarks. Consult the linked dataset
publisher for any separate data-use terms. No logos, photos or game assets are packaged.
