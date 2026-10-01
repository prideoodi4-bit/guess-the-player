import asyncio
import logging
import os
import secrets
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from telegram import InlineKeyboardButton as Button, InlineKeyboardMarkup as Keyboard, BotCommand
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from core import Bank, Store, POINTS, split_scope

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
bank = Bank(ROOT / 'data')
db_path=Path(os.environ.get('DATABASE_PATH', 'state/game.sqlite3'))
if not db_path.is_absolute():
    db_path=ROOT/db_path
store = Store(db_path)
CLUE_SECONDS = int(os.environ.get('CLUE_SECONDS', '20'))
RECENT_QUESTION_SHARE = float(os.environ.get('RECENT_QUESTION_SHARE', '0.5'))
if CLUE_SECONDS < 1:
    raise ValueError('CLUE_SECONDS must be positive')
if not 0 <= RECENT_QUESTION_SHARE <= 1:
    raise ValueError('RECENT_QUESTION_SHARE must be between 0 and 1')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
# Request URLs can contain the bot token; keep HTTP logging quiet.
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
log = logging.getLogger('football')


@dataclass
class Game:
    owner: int
    mode: str
    nonce: str = field(default_factory=lambda: secrets.token_hex(4))
    phase: str = 'setup'
    rounds: int = 0
    players: dict = field(default_factory=dict)
    scores: dict = field(default_factory=dict)
    item: dict | None = None
    clue: int = -1
    deadline: float = 0
    sent_at: int = 0
    winner: tuple | None = None
    event: asyncio.Event = field(default_factory=asyncio.Event)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    task: asyncio.Task | None = None


games = {}
setups = {}  # (chat_id, topic_id) -> (owner, nonce)


def mode_label(mode):
    return 'اللاعب' if mode == 'players' else 'النادي'


def scope_key(update):
    message = update.effective_message
    topic = getattr(message, 'message_thread_id', None) or 0
    # General is represented by 0, including API updates explicitly using ID 1.
    if topic == 1:
        topic = 0
    return update.effective_chat.id, topic


async def send(bot, scope, text, **kwargs):
    chat_id, topic_id = split_scope(scope)
    # Never retry a closed/deleted topic by sending into General.
    return await bot.send_message(chat_id, text, message_thread_id=topic_id or None, **kwargs)


async def admin_or_owner(update, context, owner=None):
    user = update.effective_user
    if not user:
        return False
    if user.id == owner or update.effective_chat.type == 'private':
        return True
    member = await context.bot.get_chat_member(update.effective_chat.id, user.id)
    return member.status in ('creator', 'administrator')


async def help_command(update, context):
    await update.effective_message.reply_text(
        '⚽ احزر اللاعب / النادي\n'
        '/game — اختار النوع وعدد الجولات\n'
        '/join — انضم للعبة\n/begin — صاحب اللعبة يبدأ\n'
        '/game players 10 أو /game clubs 5 — عدد مباشر\n'
        '/rounds 12 — عدد خاص قبل البداية\n'
        '/score — نقاط هذه اللعبة\n/top — النقاط المحفوظة لهذا القسم\n'
        '/stop — إيقاف اللعبة (صاحبها أو الأدمن)\n'
        '/remaining — عدد الأسئلة غير المستخدمة\n'
        '/reset players أو /reset clubs — إعادة بنك الأسئلة بعد تأكيد الأدمن\n'
        '٤ تلميحات، كل واحد ٢٠ ثانية. النقاط: ٤٠، ٣٠، ٢٠، ١٠.\n'
        'اكتب الاسم بالعربي إذا إله اسم بديل، أو بالإنكليزي. لازم /join قبل الجواب.\n'
        'التلميحات القديمة والحديثة مختلطة حسب الصعوبة، والسنة مكتوبة.\n'
        'ابدأ /game داخل القسم المطلوب؛ كل قسم إله لعبة ونقاط مستقلة.'
    )


async def game_command(update, context):
    chat = scope_key(update)
    if chat in games:
        await update.effective_message.reply_text('أكو لعبة أو إعدادات مفتوحة. كمّلها أو استخدم /stop.')
        return
    if context.args:
        if len(context.args) != 2 or context.args[0] not in bank.items:
            await update.effective_message.reply_text('مثال: /game players 10 أو /game clubs 5')
            return
        try:
            rounds = int(context.args[1])
        except ValueError:
            rounds = 0
        g = Game(update.effective_user.id, context.args[0])
        if not 1 <= rounds <= len(store.remaining(chat,g.mode,bank)):
            await update.effective_message.reply_text('العدد لازم يكون من ١ إلى عدد الأسئلة المتبقية. استخدم /remaining.')
            return
        games[chat] = g
        setups.pop(chat,None)
        await lobby(context.bot,chat,g,rounds)
        return
    nonce = secrets.token_hex(4)
    setups[chat] = (update.effective_user.id,nonce)
    await update.effective_message.reply_text('اختار نوع اللعبة:', reply_markup=Keyboard([[
        Button('⚽ احزر اللاعب', callback_data=f'mode:{nonce}:players'),
        Button('🏟 احزر النادي', callback_data=f'mode:{nonce}:clubs')]]))


async def lobby(bot, chat, g, rounds):
    g.rounds = rounds
    g.phase = 'lobby'
    await send(bot,chat, f'⚽ احزر {mode_label(g.mode)} — {rounds} جولات\n'
        'اضغط انضمام، وبعدها صاحب اللعبة يضغط ابدأ. تگدر تدخل أثناء اللعبة همين.',
        reply_markup=Keyboard([[
            Button('🙋 انضمام', callback_data=f'join:{g.nonce}'),
            Button('▶️ ابدأ', callback_data=f'begin:{g.nonce}')]]))


async def select_rounds(bot,chat,g):
    available = len(store.remaining(chat,g.mode,bank))
    choices = [n for n in (5,10,15,20) if n <= available]
    if not choices and available:
        choices = [available]
    await send(bot,chat, f'عدد الأسئلة المتبقية: {available}\nاختار عدد الجولات أو اكتب /rounds 12',
        reply_markup=Keyboard([[Button(str(n),callback_data=f'rounds:{g.nonce}:{n}') for n in choices]]) if choices else None)


async def callback(update, context):
    q = update.callback_query
    await q.answer()
    chat,user = scope_key(update),update.effective_user
    parts = q.data.split(':')
    action, nonce = parts[:2]
    if action == 'mode':
        setup = setups.get(chat)
        if not setup or setup != (user.id,nonce) or chat in games:
            return
        mode = parts[2]
        if not store.remaining(chat,mode,bank):
            await q.message.reply_text('خلصت الأسئلة. الأدمن يگدر يستخدم /reset لإعادتها.')
            return
        g = Game(user.id,mode)
        games[chat] = g
        setups.pop(chat,None)
        await q.edit_message_reply_markup(reply_markup=None)
        await select_rounds(context.bot,chat,g)
        return
    if action == 'reset':
        # Admin authorization is checked again when confirmation is clicked.
        pending = context.chat_data.get(('reset',chat[1]))
        if not pending or pending != (nonce,parts[2],user.id):
            return
        if chat in games or not await admin_or_owner(update,context):
            return
        store.reset_used(chat,parts[2])
        context.chat_data.pop(('reset',chat[1]),None)
        await q.edit_message_text('تمت إعادة بنك الأسئلة لهذا النوع. النقاط تبقى محفوظة.')
        return
    g = games.get(chat)
    if not g or g.nonce != nonce:
        return
    if action == 'join':
        g.players[user.id] = user.full_name
        await q.message.reply_text(f'انضم {user.full_name} ✅')
    elif action == 'rounds' and g.phase == 'setup' and user.id == g.owner:
        n = int(parts[2])
        if 1 <= n <= len(store.remaining(chat,g.mode,bank)):
            await q.edit_message_reply_markup(reply_markup=None)
            await lobby(context.bot,chat,g,n)
    elif action == 'begin':
        await begin_game(update,context,g)


async def rounds_command(update,context):
    chat = scope_key(update)
    g = games.get(chat)
    if not g or g.phase not in ('setup','lobby') or update.effective_user.id != g.owner:
        return
    try:
        n = int(context.args[0])
    except (IndexError,ValueError):
        n = 0
    if not 1 <= n <= len(store.remaining(chat,g.mode,bank)):
        await update.effective_message.reply_text('اختار عدد موجب ضمن الأسئلة المتبقية. /remaining')
        return
    await lobby(context.bot,chat,g,n)


async def join_command(update,context):
    g = games.get(scope_key(update))
    if not g:
        await update.effective_message.reply_text('افتح لعبة أولاً: /game')
        return
    u = update.effective_user
    g.players[u.id] = u.full_name
    await update.effective_message.reply_text(f'انضم {u.full_name} ✅')


async def begin_command(update,context):
    g = games.get(scope_key(update))
    if g:
        await begin_game(update,context,g)


async def begin_game(update,context,g):
    if g.phase != 'lobby' or not await admin_or_owner(update,context,g.owner):
        return
    if not g.players:
        await update.effective_message.reply_text('لازم ينضم لاعب واحد على الأقل: /join')
        return
    g.phase = 'running'
    chat = scope_key(update)
    store.mark_active(chat,True)
    # Managed here so shutdown can cancel games before waiting for their timers.
    g.task = asyncio.create_task(play(context.application,chat,g),name=f'game-{chat}')


async def play(app,chat,g):
    try:
        for round_number in range(1,g.rounds+1):
            item = store.draw(chat,g.mode,bank,recent_share=RECENT_QUESTION_SHARE)
            if not item:
                await send(app.bot,chat,'خلصت الأسئلة؛ ما راح أعيدها تلقائياً.')
                break
            async with g.lock:
                g.item,g.winner,g.clue = item,None,-1
                g.event.clear()
            for i,clue in enumerate(bank.choose_clues(item)):
                async with g.lock:
                    g.clue = -1  # Close scoring while the next clue is being sent.
                    msg = await send(app.bot,chat,
                        f'🎯 الجولة {round_number}/{g.rounds} — احزر {mode_label(g.mode)}\n'
                        f'💡 التلميح {i+1}/4 — {POINTS[i]} نقطة\n{clue}\n⏱ {CLUE_SECONDS} ثانية')
                    g.clue = i
                    g.sent_at = msg.message_id
                    g.deadline = time.monotonic()+CLUE_SECONDS
                try:
                    await asyncio.wait_for(g.event.wait(),timeout=CLUE_SECONDS)
                except asyncio.TimeoutError:
                    pass
                async with g.lock:
                    g.clue = -1
                    winner = g.winner
                if winner:
                    break
            async with g.lock:
                g.item = None
            if winner:
                name,points = winner
                await send(app.bot,chat,f'✅ {name} حزرها! +{points} نقطة\nالجواب: {item["answer"]}')
            else:
                await send(app.bot,chat,f'⌛ خلص الوقت. الجواب: {item["answer"]}')
            await asyncio.sleep(3)
        await send(app.bot,chat,'🏆 انتهت اللعبة!\n'+session_table(g))
    except asyncio.CancelledError:
        raise
    except Exception as e:
        # Log only type: never expose token-bearing HTTP exception text.
        log.error('Game interrupted: %s',type(e).__name__)
        try:
            await send(app.bot,chat,'توقفت اللعبة بسبب مشكلة اتصال. النقاط والأسئلة المستخدمة محفوظة. /game')
        except Exception:
            pass
    finally:
        store.mark_active(chat,False)
        if games.get(chat) is g:
            games.pop(chat,None)


async def guess(update,context):
    message = update.effective_message
    chat = scope_key(update)
    g = games.get(chat)
    if not g or g.phase != 'running' or not update.effective_user:
        return
    u = update.effective_user
    if u.id not in g.players:
        return
    async with g.lock:
        # Message-id guard rejects guesses sent before this clue in this chat.
        if (g.item is None or g.clue < 0 or g.winner or
                time.monotonic() >= g.deadline or message.message_id <= g.sent_at):
            return
        if not bank.matches(g.mode,g.item,message.text):
            return
        points = POINTS[g.clue]
        store.score(chat,u.id,u.full_name,points)
        g.scores[u.id] = g.scores.get(u.id,0)+points
        g.players[u.id] = u.full_name
        g.winner = (u.full_name,points)
        g.event.set()


def session_table(g):
    rows = sorted(g.scores.items(),key=lambda x:(-x[1],x[0]))[:10]
    return '\n'.join(f'{i}. {g.players[u]} — {p}' for i,(u,p) in enumerate(rows,1)) or 'بعد ماكو نقاط.'


async def score_command(update,context):
    g = games.get(scope_key(update))
    await update.effective_message.reply_text(session_table(g) if g else 'ماكو لعبة مفتوحة. استخدم /top للنقاط المحفوظة.')


async def top_command(update,context):
    rows = store.leaders(scope_key(update))
    text = '\n'.join(f'{i}. {name} — {p}' for i,(name,p) in enumerate(rows,1)) or 'بعد ماكو نقاط.'
    await update.effective_message.reply_text('🏆 ترتيب هذا القسم\n'+text)


async def remaining_command(update,context):
    chat = scope_key(update)
    await update.effective_message.reply_text('\n'.join(
        f'{"لاعبين" if m=="players" else "أندية"}: {len(store.remaining(chat,m,bank))}/{len(bank.items[m])}'
        for m in bank.items))


async def stop_command(update,context):
    chat = scope_key(update)
    g = games.get(chat)
    owner = g.owner if g else (setups.get(chat) or (None,None))[0]
    if not await admin_or_owner(update,context,owner):
        return
    setups.pop(chat,None)
    if g:
        if g.task:
            g.task.cancel()
            try:
                await g.task
            except asyncio.CancelledError:
                pass
        games.pop(chat,None)
        store.mark_active(chat,False)
    await update.effective_message.reply_text('تم إيقاف اللعبة. النقاط والأسئلة المستخدمة محفوظة.')


async def reset_command(update,context):
    chat = scope_key(update)
    if chat in games or chat in setups:
        await update.effective_message.reply_text('أوقف اللعبة أولاً: /stop')
        return
    if not await admin_or_owner(update,context):
        await update.effective_message.reply_text('إعادة الأسئلة للأدمن فقط.')
        return
    if len(context.args)!=1 or context.args[0] not in bank.items:
        await update.effective_message.reply_text('/reset players أو /reset clubs')
        return
    mode,nonce = context.args[0],secrets.token_hex(4)
    context.chat_data[('reset',chat[1])] = (nonce,mode,update.effective_user.id)
    await update.effective_message.reply_text('راح ترجع الأسئلة القديمة متاحة بهذا الكروب. تأكد؟',
        reply_markup=Keyboard([[Button('تأكيد إعادة الأسئلة',callback_data=f'reset:{nonce}:{mode}')]]))


async def backup_command(update,context):
    # Never publish a database containing other groups' identities in a group.
    allowed = {int(x) for x in os.environ.get('OWNER_IDS','').split(',') if x.strip().isdigit()}
    if update.effective_chat.type!='private' or update.effective_user.id not in allowed:
        await update.effective_message.reply_text('النسخة الاحتياطية للمشغّل بالخاص فقط. ضيف رقمك إلى OWNER_IDS.')
        return
    with tempfile.TemporaryDirectory() as d:
        path = Path(d)/'game-backup.sqlite3'
        store.backup(path)
        with path.open('rb') as f:
            await update.effective_message.reply_document(f,filename='game-backup.sqlite3',caption='النقاط والأسئلة المستخدمة لكل الكروبات.')


async def post_init(app):
    await app.bot.set_my_commands([BotCommand(n,d) for n,d in [
        ('game','لعبة جديدة'),('join','انضمام'),('begin','ابدأ اللعبة'),
        ('rounds','عدد خاص للجولات'),('score','نقاط اللعبة'),('top','ترتيب الكروب'),
        ('remaining','الأسئلة المتبقية'),('stop','إيقاف'),('help','التعليمات'),('backup','نسخة احتياطية للمشغّل')]])
    for chat in store.interrupted():
        try:
            await send(app.bot,chat,'أعيد تشغيل البوت؛ اللعبة السابقة توقفت. النقاط والأسئلة المستخدمة محفوظة. ابدأ بـ /game')
        except Exception:
            log.warning('Could not notify interrupted chat')
        store.mark_active(chat,False)


async def post_stop(app):
    for g in list(games.values()):
        if g.task:
            g.task.cancel()
    await asyncio.gather(*(g.task for g in list(games.values()) if g.task),return_exceptions=True)


async def error_handler(update,context):
    log.error('Update failed: %s',type(context.error).__name__)


def main():
    token = os.environ.get('BOT_TOKEN','')
    if not token or token=='PUT_YOUR_BOT_TOKEN_HERE':
        raise SystemExit('حط BOT_TOKEN بملف .env أو بمتغيرات الاستضافة أولاً.')
    app = (Application.builder().token(token).concurrent_updates(False)
        .post_init(post_init).post_stop(post_stop).build())
    for command,fn in [('start',help_command),('help',help_command),('game',game_command),
        ('join',join_command),('begin',begin_command),('rounds',rounds_command),
        ('score',score_command),('top',top_command),('remaining',remaining_command),
        ('stop',stop_command),('reset',reset_command),('backup',backup_command)]:
        app.add_handler(CommandHandler(command,fn))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE,guess))
    app.add_error_handler(error_handler)
    app.run_polling(drop_pending_updates=True)


if __name__=='__main__':
    main()
