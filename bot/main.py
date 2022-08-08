import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData
import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3

meta = MetaData()
engine = create_engine('sqlite:///bot.db', echo=True)
path = os.getcwd()
flag = False
man = False
woman = False
name = False
genderquestion = False


dataa = {}
for root, dirs, files in os.walk("."):
    for filename in files:
        if filename == 'bot.dp':
            flag = True

if not flag:
    bot_table = Table(
       'bot', meta,
       Column('id', Integer, primary_key = True),
       Column('name', String),
       Column('gender', String),
       Column('genderquestion', String))
    meta.create_all(engine)

logging.basicConfig(level=logging.INFO)
API_TOKEN = '5511122711:AAGy1p6VtU-k80q6q1y_MUlhB00mLol0yTw'
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
conn = engine.connect()


inline_btn_1 = InlineKeyboardButton('Имя', callback_data='button1')
inline_btn_3 = InlineKeyboardButton('Возраст', callback_data='button3')
inline_btn_4 = InlineKeyboardButton('Хобби', callback_data='button4')
inline_btn_5 = InlineKeyboardButton('Да', callback_data='button5')
inline_btn_6 = InlineKeyboardButton('Нет', callback_data='button6')

inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1)
inline_kb1.add(inline_btn_3)

inline_kb2 = InlineKeyboardMarkup().add(inline_btn_1)
inline_kb2.add(inline_btn_4)

inline_kb3 = InlineKeyboardMarkup().add(inline_btn_5)
inline_kb3.add(inline_btn_6)


class Form(StatesGroup):
    name = State()
    gender = State()
    genderquestion = State()


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    global man, woman, dataa
    idf = types.User.get_current()['id']
    sql = f"""
        SELECT * FROM bot 
            WHERE id = {idf}
        """

    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        res = cursor.fetchall()
    if res:
        await message.answer('Вы уже вносили данные о себе теперь вы можете только отредактировать их или удалить')
        s = list(res[0])
        dataa['id'] = s[0]
        dataa['name'] = s[1]
        dataa['gender'] = s[2]
        dataa['genderquestion'] = s[3]
        if dataa['gender'] == 'мужчина':
            man = True
        else:
            woman = True

    else:
        man = False
        woman = False
        dataa = {}
        await Form.name.set()
        await message.answer("Привет, как тебя зовут")




@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await Form.next()
    await message.answer("Вы мужчина или женщина?")


@dp.message_handler(lambda message: message.text.lower() not in ["мужчина", "женщина"], state=Form.gender)
async def process_gender_invalid(message: types.Message):
    return await message.reply("Это не гендер")


@dp.message_handler(state=Form.gender)
async def process_gender(message: types.Message, state: FSMContext):
    global man, woman
    async with state.proxy() as data:
        data['gender'] = message.text.lower()
        if data['gender'] == 'мужчина':
            await bot.send_message(message.chat.id, 'Сколько вам лет?')
            man = True
        else:
            await bot.send_message(message.chat.id, 'У женщин неприлично спрашивать про возраст, '
                                                    'поэтому расскажите про ваши хобби' )
    await Form.next()


@dp.message_handler(state=Form.genderquestion)
async def process_name(message: types.Message, state: FSMContext):
    global dataa
    async with state.proxy() as data:
        data['genderquestion'] = message.text
    await bot.send_message(message.chat.id, 'Ваши даннные сохранены, если желаете отредактировать'
                                            ' их или удалить воспользуйтесь соответсвующими командами (/edit, /delete')
    for e in data:
        dataa[e] = data[e]
    dataa['id'] = types.User.get_current()['id']
    ins = bot_table.insert().values(name=dataa['name'], id=dataa['id'], gender=dataa['gender'], genderquestion=dataa['genderquestion'])
    conn.execute(ins)
    await state.finish()


@dp.message_handler(commands='edit')
async def cmd_start(msg: types.Message):
    idf = types.User.get_current()['id']
    sql = f"""
                    SELECT * FROM bot 
                        WHERE id = {idf}
                    """
    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        res = cursor.fetchall()
        s = list(res[0])

    if s[2] == 'мужчина':
        await msg.answer('Что вы хотите изменить? Пол менять нельзя)', reply_markup=inline_kb1)
    if s[2] == 'женщина':
        await msg.answer('Что вы хотите изменить? Пол менять нельзя)', reply_markup=inline_kb2)


@dp.message_handler(commands='delete')
async def cmd_start(msg: types.Message):
    idf = types.User.get_current()['id']
    sql = f"""
            SELECT * FROM bot 
                WHERE id = {idf}
            """

    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        res = cursor.fetchall()
    if res:
        await msg.answer('Вы уверены, что хотите удалить данные о себе? Отменить это действие будет невозможно', reply_markup=inline_kb3)
    else:
        await msg.answer('О вас еще нет данных')

@dp.callback_query_handler(lambda c: c.data == 'button1')
async def process_callback_button1(callback_query: types.CallbackQuery):
    global dataa, name
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    name = True
    idf = types.User.get_current()['id']
    sql = f"""
            SELECT * FROM bot 
                WHERE id = {idf}
            """
    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        res = cursor.fetchall()
        s = list(res[0])
    await bot.send_message(callback_query.from_user.id, f"Ваше текущее имя {s[1]}, на что вы хотите его поменять?")


@dp.callback_query_handler(lambda c: c.data == 'button3')
async def process_callback_button1(callback_query: types.CallbackQuery):
    global genderquestion
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    genderquestion = True
    idf = types.User.get_current()['id']
    sql = f"""
                SELECT * FROM bot 
                    WHERE id = {idf}
                """
    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        res = cursor.fetchall()
        s = list(res[0])
    await bot.send_message(callback_query.from_user.id, f"Ваш текущий возраст {s[3]}, на что вы хотите его поменять?")


@dp.callback_query_handler(lambda c: c.data == 'button4')
async def process_callback_button1(callback_query: types.CallbackQuery):
    global genderquestion
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    genderquestion = True
    idf = types.User.get_current()['id']
    sql = f"""
                    SELECT * FROM bot 
                        WHERE id = {idf}
                    """
    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        res = cursor.fetchall()
        s = list(res[0])
    await bot.send_message(callback_query.from_user.id, f"Ваше текущее хобби {s[3]}, на что вы хотите его поменять?")

@dp.callback_query_handler(lambda c: c.data == 'button5')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    idf = types.User.get_current()['id']
    sql = f"""
            SELECT * FROM bot 
                WHERE id = {idf}
            """

    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        res = cursor.fetchall()
    if res:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM bot WHERE id = {idf}")
        conn.commit()
        await bot.send_message(callback_query.from_user.id, 'Данные о вас удалены')
    else:
        await bot.send_message(callback_query.from_user.id, 'Вы еще не вносили данные о себе')

@dp.callback_query_handler(lambda c: c.data == 'button6')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id, 'Мы рады, что вы решили остаться')

@dp.message_handler(content_types='text')
async def mas(message: types.Message):
    global name, genderquestion
    if name:
        name = False
        connection = sqlite3.connect('bot.db')
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute('UPDATE bot SET name=? WHERE id=?',(message.text,types.User.get_current()['id']))
        connection.commit()
        await message.answer('Данные обновлены')

    if genderquestion:
        genderquestion = False
        connection = sqlite3.connect('bot.db')
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute('UPDATE bot SET name=? WHERE id=?',(message.text, types.User.get_current()['id']))
        connection.commit()
        await message.answer('Данные обновлены')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)