#!/usr/bin/env python3
"""Telegram diagnosis game. Standard library only, Python 3.11+."""
import asyncio
import json
import logging
import os
import secrets
import time
import urllib.error
import urllib.request
from pathlib import Path
from engine import Bank, Store, SPECIALTIES, LEVELS, POINTS, CLUE_SECONDS, scope_key

ROOT = Path(__file__).resolve().parent
LOG = logging.getLogger('diagnosis_game')

def load_env():
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                name, value = line.split('=', 1)
                os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))

class TelegramError(Exception):
    def __init__(self, code, description, retry_after=0):
        super().__init__(description)
        self.code, self.description, self.retry_after = code, description, retry_after

class Telegram:
    def __init__(self, token):
        self.base = f'https://api.telegram.org/bot{token}/'

    async def call(self, method, **payload):
        def request():
            req = urllib.request.Request(self.base+method, data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'})
            try:
                with urllib.request.urlopen(req, timeout=45) as response:
                    result = json.load(response)
            except urllib.error.HTTPError as exc:
                try:
                    result = json.loads(exc.read().decode())
                except Exception:
                    raise TelegramError(exc.code, 'Telegram HTTP request failed') from None
            except (urllib.error.URLError, TimeoutError, OSError):
                # Do not expose token-bearing request URLs in logs.
                raise TelegramError(0, 'Network request failed') from None
            if not result.get('ok'):
                raise TelegramError(result.get('error_code',0), result.get('description','Telegram rejected request'), result.get('parameters',{}).get('retry_after',0))
            return result['result']
        try:
            return await asyncio.to_thread(request)
        except TelegramError as error:
            if error.code == 429 and error.retry_after:
                await asyncio.sleep(min(error.retry_after, 60))
                return await asyncio.to_thread(request)
            raise

    async def send(self, game, text, keyboard=None):
        payload = {'chat_id': game['chat_id'], 'text': text}
        if game.get('thread_id') not in (None, 1):
            payload['message_thread_id'] = game['thread_id']
        if keyboard is not None:
            payload['reply_markup'] = {'inline_keyboard': keyboard}
        return await self.call('sendMessage', **payload)

class GameBot:
    def __init__(self, api, bank, store, clock=time.time, clue_seconds=CLUE_SECONDS):
        self.api, self.bank, self.store, self.clock = api, bank, store, clock
        if not isinstance(clue_seconds, int) or isinstance(clue_seconds, bool) or clue_seconds <= 0:
            raise ValueError("CLUE_SECONDS must be a positive integer in seconds")
        self.clue_seconds = clue_seconds
        self.games = store.sessions()
        self.menus = {}
        self.settings_menus = {}
        self.lock = asyncio.Lock()
        self.username = ''

    def save(self, scope):
        self.store.save(scope, self.games[scope])

    async def admin_or_host(self, user_id, game):
        if user_id == game['host_id']:
            return True
        if game['chat_id'] > 0:
            return False
        member = await self.api.call('getChatMember', chat_id=game['chat_id'], user_id=user_id)
        return member.get('status') in ('creator','administrator')

    def context(self, message, user):
        return {'chat_id': message['chat']['id'], 'thread_id': message.get('message_thread_id'), 'host_id':user['id']}

    def seconds(self, scope):
        return self.store.clue_time(scope,self.clue_seconds)

    async def may_change_time(self, context, user):
        scope=scope_key(context['chat_id'],context.get('thread_id'))
        game=self.games.get(scope)
        if game:
            return await self.admin_or_host(user['id'],game)
        if context['chat_id'] > 0:
            return True
        member=await self.api.call('getChatMember',chat_id=context['chat_id'],user_id=user['id'])
        return member.get('status') in ('creator','administrator')

    async def settings(self, message, user):
        context=self.context(message,user)
        scope=scope_key(context['chat_id'],context.get('thread_id'))
        nonce=secrets.token_hex(4)
        self.settings_menus[scope]={'nonce':nonce,'created':self.clock()}
        keyboard=[[{'text':f'{n} ثانية','callback_data':f'time:{nonce}:{n}'} for n in row]
                  for row in ((20,25,30),(40,45,60),(90,120,180))]
        keyboard.append([{'text':'وقت مخصص','callback_data':f'time:{nonce}:custom'}])
        await self.api.send(context,f'⚙️ إعدادات الوقت لهذا الكروب/القسم\nالوقت الحالي: {self.seconds(scope)} ثانية لكل تلميح.\nاختار الوقت، أو اكتب /time 75 (من 5 إلى 600 ثانية).\nالتعديل لأدمن الكروب أو صاحب اللعبة الجارية؛ يطبق من التلميح القادم.',keyboard)

    async def change_time(self, message, user, value):
        context=self.context(message,user)
        scope=scope_key(context['chat_id'],context.get('thread_id'))
        if not await self.may_change_time(context,user):
            await self.api.send(context,'تعديل الوقت لأدمن الكروب أو صاحب اللعبة الجارية.')
            return
        if not value.isdigit() or not 5 <= int(value) <= 600:
            await self.api.send(context,'اكتب /time 40 مثلًا. الوقت من 5 إلى 600 ثانية.')
            return
        self.store.set_clue_time(scope,int(value))
        await self.api.send(context,f'✅ تم حفظ الوقت: {int(value)} ثانية لكل تلميح بهذا القسم.\nيطبق من التلميح القادم وعلى الألعاب الجديدة. مهلة التلميح الظاهر حاليًا تبقى كما هي.')

    async def menu(self, message, user):
        context = self.context(message, user)
        scope = scope_key(context['chat_id'], context['thread_id'])
        if scope in self.games:
            await self.api.send(context, 'لعبة شغالة بهذا القسم. /score للنقاط، /stop لإنهائها بواسطة صاحب اللعبة أو الأدمن.')
            return
        nonce = secrets.token_hex(4)
        self.menus[scope] = {**context, 'nonce':nonce, 'stage':'specialty', 'created':self.clock()}
        keyboard = [[{'text':name,'callback_data':f'dx:{nonce}:s:{key}'}] for key,name in SPECIALTIES.items()]
        await self.api.send(context, f'🩺 Guess the Diagnosis\nاختار الاختصاص. الكيسات والجواب بالإنكليزي.\n٤ تلميحات، لكل تلميح {self.seconds(scope)} ثانية.', keyboard)

    async def callback(self, query):
        message, user = query.get('message'), query['from']
        if not message:
            return
        scope = scope_key(message['chat']['id'], message.get('message_thread_id'))
        parts = query.get('data','').split(':')
        if parts and parts[0]=='time':
            current=self.settings_menus.get(scope)
            if len(parts)!=3 or not current or parts[1]!=current['nonce'] or self.clock()-current['created']>900:
                await self.api.call('answerCallbackQuery',callback_query_id=query['id'],text='القائمة قديمة. افتح /settings')
                return
            context=self.context(message,user)
            if not await self.may_change_time(context,user):
                await self.api.call('answerCallbackQuery',callback_query_id=query['id'],text='للأدمن أو صاحب اللعبة الجارية فقط.')
                return
            await self.api.call('answerCallbackQuery',callback_query_id=query['id'])
            if parts[2]=='custom':
                await self.api.send(context,'اكتب /time وبعده الوقت بالثواني، مثل /time 75. المسموح 5 إلى 600.')
            else:
                await self.change_time(message,user,parts[2])
            return
        menu = self.menus.get(scope)
        if len(parts) != 4 or parts[0] != 'dx' or not menu or parts[1] != menu['nonce'] or self.clock()-menu['created'] > 900:
            await self.api.call('answerCallbackQuery', callback_query_id=query['id'], text='القائمة قديمة. افتح /newgame')
            return
        if user['id'] != menu['host_id']:
            await self.api.call('answerCallbackQuery', callback_query_id=query['id'], text='صاحب اللعبة يختار الإعدادات.')
            return
        action, value = parts[2:]
        expected_stage = {'s':'specialty', 'd':'difficulty', 'r':'rounds'}
        if expected_stage.get(action) != menu['stage'] or scope in self.games:
            await self.api.call('answerCallbackQuery', callback_query_id=query['id'], text='هذا الاختيار صار قديم.')
            return
        await self.api.call('answerCallbackQuery', callback_query_id=query['id'])
        if action == 's' and value in SPECIALTIES:
            menu.update(specialty=value, stage='difficulty')
            keyboard = [[{'text':level.title(), 'callback_data':f'dx:{menu["nonce"]}:d:{level}'} for level in LEVELS]]
            await self.api.send(menu, f'{SPECIALTIES[value]}\nاختار مستوى الكيس:', keyboard)
        elif action == 'd' and value in LEVELS:
            menu.update(difficulty=value, stage='rounds')
            keyboard = [[{'text':str(n), 'callback_data':f'dx:{menu["nonce"]}:r:{n}'} for n in (5,10,15)], [{'text':'20', 'callback_data':f'dx:{menu["nonce"]}:r:20'}, {'text':'عدد آخر', 'callback_data':f'dx:{menu["nonce"]}:r:custom'}]]
            await self.api.send(menu, 'اختار عدد الجولات، أو اختار عدد آخر واكتب العدد من 1 إلى 50.', keyboard)
        elif action == 'r':
            if value == 'custom':
                menu['stage'] = 'custom'
                await self.api.send(menu, 'اكتب عدد الجولات من 1 إلى 50. إذا Privacy Mode شغال استعمل /rounds 12')
            elif value.isdigit() and 1 <= int(value) <= 50:
                await self.begin(scope, int(value))

    async def begin(self, scope, rounds):
        menu = self.menus[scope]
        ids = self.bank.pick(menu['specialty'], rounds, self.store.history(scope, menu['specialty']))
        if not ids:
            await self.api.send(menu, 'ماكو كيسات لهذا الاختصاص.')
            return
        game = {k:menu[k] for k in ('chat_id','thread_id','host_id','specialty','difficulty')}
        game.update(case_ids=ids, index=0, clue=0, phase='next', deadline=self.clock(), scores={}, accepting=False, opened=0)
        self.games[scope] = game
        self.save(scope)
        del self.menus[scope]
        await self.api.send(game, f'🎮 {SPECIALTIES[game["specialty"]]} — {game["difficulty"].title()}\nالجولات: {len(ids)}\nالنقاط: 4 ← 3 ← 2 ← 1\nاكتب تشخيص واحد بالإنكليزي. الجميع يگدر يشارك بدون join.\n/guess diagnosis بديل للجواب العادي.')
        await self.advance(scope)

    async def send_clue(self, scope):
        game = self.games[scope]
        case = self.bank.by_id[game['case_ids'][game['index']]]
        clue = game['clue']
        text = self.bank.clues(case, game['difficulty'])[clue]
        message = f'🩺 Case {game["index"]+1}/{len(game["case_ids"])} | {game["difficulty"].title()}\n🔎 Clue {clue+1}/4 | {POINTS[clue]} points | {self.seconds(scope)} seconds\n\n{text}\n\nWhat is the diagnosis?'
        # Do not reveal the subsection: it can itself give away the answer.
        game['accepting'] = False
        self.save(scope)
        await self.api.send(game, message)
        game['opened'] = self.clock()
        game['deadline'] = game['opened'] + self.seconds(scope)
        game['accepting'] = True
        game['phase'] = 'clue'
        self.save(scope)

    async def advance(self, scope):
        game = self.games[scope]
        if game['index'] >= len(game['case_ids']):
            await self.finish(scope)
            return
        case = self.bank.by_id[game['case_ids'][game['index']]]
        available = {c['diagnosis_key'] for c in self.bank.cases if c['specialty'] == game['specialty']}
        self.store.mark_seen(scope, game['specialty'], case['diagnosis_key'], available)
        game['clue'] = 0
        await self.send_clue(scope)

    async def reveal(self, scope, winner=None):
        game = self.games[scope]
        if game['phase'] != 'clue':
            return
        case = self.bank.by_id[game['case_ids'][game['index']]]
        game['accepting'] = False
        game['phase'] = 'next'
        game['index'] += 1
        game['deadline'] = self.clock()+5
        self.store.settle(scope,game,winner)
        intro = f'✅ {winner["name"]} +{winner["points"]} points' if winner else '⏰ انتهى الكيس بدون جواب صحيح.'
        topics = case.get('blueprint_topics') or [case['section']]
        topic = f'{case["section"]} — {topics[0]}'
        await self.api.send(game, f'{intro}\nDiagnosis: {case["diagnosis"]}\nKey finding: {case["facts"][-1]}\nBlueprint topic: {topic}')

    async def answer(self, message, user, text):
        scope = scope_key(message['chat']['id'], message.get('message_thread_id'))
        game = self.games.get(scope)
        if not game or game['phase'] != 'clue' or not game['accepting']:
            return
        now = self.clock()
        # Reject already-expired, queued pre-round, or older-hint answers.
        timestamp = message.get('date', int(now))
        if now >= game['deadline'] or timestamp < int(game['opened']):
            return
        case = self.bank.by_id[game['case_ids'][game['index']]]
        if not self.bank.accepted(text, case):
            return
        points = POINTS[game['clue']]
        name = user.get('first_name','Player')[:80]
        uid = str(user['id'])
        row = game['scores'].setdefault(uid, {'name':name,'points':0,'wins':0})
        row.update(name=name, points=row['points']+points, wins=row['wins']+1)
        await self.reveal(scope, {'uid':user['id'],'name':name,'points':points})

    async def finish(self, scope):
        game = self.games[scope]
        rows = sorted(game['scores'].values(), key=lambda r:(-r['points'],-r['wins'],r['name']))
        lines = [f'🏁 انتهت اللعبة — {len(game["case_ids"])} جولات']
        lines += [f'{i}. {r["name"]}: {r["points"]} points ({r["wins"]} wins)' for i,r in enumerate(rows[:15],1)]
        if not rows:
            lines.append('ماكو أجوبة صحيحة بهذا الكيم.')
        lines.append('/newgame للعبة جديدة، /leaderboard للنقاط المحفوظة بهذا القسم.')
        await self.api.send(game, '\n'.join(lines))
        self.store.delete(scope)
        del self.games[scope]

    async def tick(self):
        async with self.lock:
            for scope in list(self.games):
                game = self.games[scope]
                if self.clock() < game['deadline']:
                    continue
                try:
                    if game['phase'] == 'next':
                        await self.advance(scope)
                    elif game['clue'] < 3:
                        game['clue'] += 1
                        await self.send_clue(scope)
                    else:
                        await self.reveal(scope)
                except TelegramError as exc:
                    LOG.warning('Game delivery failed with code %s', exc.code)
                    # A failed delivery stops this game instead of silently skipping a clue.
                    self.store.delete(scope)
                    self.games.pop(scope,None)

    async def command(self, message, user, name, arg):
        ctx = self.context(message,user)
        scope = scope_key(ctx['chat_id'],ctx['thread_id'])
        if name in ('start','newgame','play'):
            await self.menu(message,user)
        elif name in ('settings','اعدادات'):
            await self.settings(message,user)
        elif name == 'time':
            await self.change_time(message,user,arg)
        elif name == 'help':
            await self.api.send(ctx, f'🩺 /newgame تبدأ لعبة\n/settings إعدادات الوقت\n/time 40 وقت مخصص بالثواني\n/guess diagnosis جواب إذا الخصوصية مفعلة\n/rounds 12 عدد مخصص\n/score نقاط الكيم\n/leaderboard النقاط المحفوظة\n/skip يتجاوز الكيس (صاحب اللعبة أو الأدمن)\n/stop يوقف اللعبة (صاحب اللعبة أو الأدمن)\n/bank إحصائية البنك\nالكيسات والجواب بالإنكليزي. ٤ تلميحات × {self.seconds(scope)} ثانية.\nبالكروب عطّل Privacy Mode من BotFather لاستقبال الأجوبة العادية. الأوامر تبقى تشتغل.\nالبنك تعليمي، مو أسئلة وزارية رسمية.')
        elif name == 'guess':
            await self.answer(message,user,arg)
        elif name == 'rounds':
            menu = self.menus.get(scope)
            if menu and menu['host_id'] == user['id'] and menu['stage'] == 'custom':
                if arg.isdigit() and 1<=int(arg)<=50:
                    await self.begin(scope,int(arg))
                else:
                    await self.api.send(ctx,'اكتب عدد من 1 إلى 50.')
        elif name in ('stop','skip'):
            game = self.games.get(scope)
            if not game:
                return
            if not await self.admin_or_host(user['id'],game):
                await self.api.send(ctx,'هذا الأمر لصاحب اللعبة أو أدمن الكروب.')
                return
            if name == 'skip':
                await self.reveal(scope)
            else:
                self.store.delete(scope)
                del self.games[scope]
                await self.api.send(ctx,'تم إيقاف اللعبة. النقاط المكتسبة محفوظة. /newgame')
        elif name == 'score':
            game = self.games.get(scope)
            rows = sorted((game or {}).get('scores',{}).values(),key=lambda r:-r['points'])
            await self.api.send(ctx,'🏆 نقاط الكيم\n'+'\n'.join(f'{r["name"]}: {r["points"]}' for r in rows[:15]) if rows else 'ماكو نقاط بالكيم الحالي.')
        elif name == 'leaderboard':
            rows = self.store.board(scope)
            await self.api.send(ctx,'🏆 النقاط المحفوظة بهذا القسم\n'+'\n'.join(f'{i}. {name}: {points} points ({wins} wins)' for i,(name,points,wins) in enumerate(rows,1)) if rows else 'بعد ماكو نقاط محفوظة.')
        elif name == 'bank':
            lines = ['📚 Base cases / difficulty presentations']
            for key,label in SPECIALTIES.items():
                count = sum(c['specialty']==key for c in self.bank.cases)
                lines.append(f'{label}: {count} / {count*3}')
            await self.api.send(ctx,'\n'.join(lines))

    async def handle(self, update):
        async with self.lock:
            if 'callback_query' in update:
                await self.callback(update['callback_query'])
                return
            # Edited answers are deliberately ignored.
            message = update.get('message')
            if not message or 'text' not in message or not message.get('from') or message['from'].get('is_bot'):
                return
            user, text = message['from'], message['text'].strip()
            if text.startswith('/'):
                command, _, arg = text.partition(' ')
                target = command.split('@',1)
                if len(target)>1 and target[1].lower()!=self.username.lower():
                    return
                await self.command(message,user,target[0][1:].lower(),arg.strip())
            else:
                scope = scope_key(message['chat']['id'],message.get('message_thread_id'))
                menu = self.menus.get(scope)
                if menu and menu['stage']=='custom' and menu['host_id']==user['id']:
                    if text.isdigit() and 1<=int(text)<=50:
                        await self.begin(scope,int(text))
                    return
                await self.answer(message,user,text)

    async def recover(self):
        for scope,game in list(self.games.items()):
            try:
                if any(cid not in self.bank.by_id for cid in game['case_ids']):
                    raise ValueError('The bank changed during an active game')
                await self.api.send(game,'🔄 البوت رجع بعد إعادة التشغيل. راح يكمل من الكيس الحالي، والنقاط محفوظة.')
                if game['phase']=='clue':
                    await self.send_clue(scope)
                else:
                    game['deadline']=self.clock()+5
                    self.save(scope)
            except (TelegramError,ValueError):
                LOG.warning('Could not restore an active game; scores retained')
                self.store.delete(scope)
                self.games.pop(scope,None)

async def run():
    load_env()
    token = os.getenv('BOT_TOKEN','').strip()
    if not token or token=='PUT_YOUR_TOKEN_HERE':
        raise SystemExit('Set BOT_TOKEN in environment or .env first. Do not publish your token.')
    api = Telegram(token)
    bank = Bank(ROOT/'data'/'cases.json')
    store = Store(os.getenv('DB_PATH',str(ROOT/'state'/'game.sqlite3')))
    try:
        clue_seconds = int(os.getenv("CLUE_SECONDS", str(CLUE_SECONDS)))
        if clue_seconds <= 0:
            raise ValueError
    except ValueError:
        raise SystemExit("CLUE_SECONDS must be a positive integer in seconds, e.g. 40.") from None
    bot = GameBot(api,bank,store,clue_seconds=clue_seconds)
    identity = await api.call('getMe')
    bot.username = identity['username']
    # Polling needs an unoccupied webhook. Preserve pending updates; stale answer timestamps are rejected.
    await api.call('deleteWebhook',drop_pending_updates=False)
    commands = [{'command':c,'description':d} for c,d in [('settings','إعدادات تعديل وقت التلميحات'),('time','تحديد الوقت مثل /time 40'),('newgame','Start a diagnosis game'),('help','Game instructions'),('guess','Submit a diagnosis'),('score','Current game scores'),('leaderboard','Saved scores'),('stop','Stop the game'),('skip','Skip current case'),('bank','Case bank statistics')]]
    await api.call('setMyCommands',commands=commands)
    await bot.recover()
    offset = None
    async def scheduler():
        while True:
            await bot.tick()
            await asyncio.sleep(0.25)
    task = asyncio.create_task(scheduler())
    LOG.info('Bot ready; %s base cases. Keep one polling instance.',len(bank.cases))
    try:
        while True:
            try:
                updates = await api.call('getUpdates',offset=offset,timeout=30,allowed_updates=['message','callback_query'])
                for update in updates:
                    try:
                        await bot.handle(update)
                    except TelegramError as exc:
                        LOG.warning('Update delivery failed with code %s',exc.code)
                    except Exception:
                        LOG.error('Unexpected update processing failure; update was not replayed')
                    offset = update['update_id']+1
            except TelegramError as exc:
                if exc.code in (401,409):
                    raise SystemExit('Invalid BOT_TOKEN or another polling instance is running.') from None
                LOG.warning('Polling unavailable; retrying (code %s)',exc.code)
                await asyncio.sleep(3)
    finally:
        task.cancel()
        await asyncio.gather(task,return_exceptions=True)
        store.db.close()

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,format='%(levelname)s %(message)s')
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass
