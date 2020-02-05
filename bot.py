import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
import threading
import pandas as pd
import requests
import lxml.html as lh
import re
import json
import pymongo
from pymongo import MongoClient

headers = {'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
           'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) snap Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36,gzip(gfe)'}
base_url = 'https://bincol.ru/rasp/grupp.php'
teacher_url = 'https://bincol.ru/rasp/prep.php'

# client = MongoClient('localhost', 27017)
client = MongoClient("mongodb://admin:admin@cluster0-shard-00-00-zlpai.mongodb.net:27017,cluster0-shard-00-01-zlpai.mongodb.net:27017,cluster0-shard-00-02-zlpai.mongodb.net:27017/pymongo_test?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin&retryWrites=true&w=majority")



def get_button(label, color, payload=''):
    return {
        'action': {
            'type': 'text',
            'payload': json.dumps(payload),
            'label': label
        },
        'color': color
    }

day_lessons = {
'one_time': False,
    'buttons': [
        [
            get_button(label='пн', color='default'),
            get_button(label='вт', color='default'),
            get_button(label='ср', color='default'),
        ],
        [
            get_button(label='чт', color='default'),
            get_button(label='пт', color='default'),
            get_button(label='сб', color='default')
        ],
        [
            get_button(label='на неделю', color='default')
        ]
    ]
}
day_lessons = json.dumps(day_lessons, ensure_ascii=False).encode('utf-8')
day_lessons = str(day_lessons.decode('utf-8'))

# def check_lessons():


def check(group_name):
    session = requests.Session()
    request = requests.get(base_url, headers=headers)
    tree = lh.document_fromstring(request.content)
    if request.status_code == 200:
        gr_name = tree.xpath('//p/a/text()')
        i = 0
        try:
            while gr_name[i] != group_name:
                i = i + 1
        except:
            return False
        else:
            return True
    else:
        print('ERROR')

def check_teacher(teacher_name):
    session = requests.Session()
    request = requests.get(teacher_url, headers=headers)
    tree = lh.document_fromstring(request.content)
    if request.status_code == 200:
        th_name = tree.xpath('//option/text()')
        i = 1
        try:
            while th_name[i].upper().replace(' ', '') != teacher_name:
                # print(gr_name[i])
                i = i + 1
                # если введенное слово не соответствует массиву названий групп, то выдает ошибку:
        except:
            return False
        else:
            return True
    else:
        print('ERROR')


def parse (group_name, user_id, random_id):
    session = requests.Session()
    # request = session.get(base_url, headers=headers)
    request = requests.get(base_url, headers=headers)
    tree = lh.document_fromstring(request.content)
    if request.status_code == 200:
        gr_name = tree.xpath('//p/a/text()')
        gr_link = tree.xpath('//p/a/@href')
        i = 0
        try:
            while gr_name[i] != group_name:
                # print(gr_name[i])
                i = i + 1
                #если введенное слово не соответствует массиву названий групп, то выдает ошибку:
        except: write_msg(event.object.peer_id, 'Такой группы нет', get_random_id())
        else:
            search_url = "https://bincol.ru/rasp/" + gr_link[i]

            week_lessons = pd.read_html(search_url)
            j = 0
            message = ''
            sr = ''
            send_full_lessons(week_lessons,user_id,random_id, message)
        # print(gr_name)
        # print(gr_link)
    else:
        print('ERROR')


def teacher_parse(teacher_name, user_id):
    session = requests.Session()
    request = requests.get(teacher_url, headers=headers)
    tree = lh.document_fromstring(request.content)
    if request.status_code == 200:
        th_name = tree.xpath('//option/text()')
        th_link = tree.xpath('//option/@value')
        i = 1
        try:
            while th_name[i].upper().replace(' ', '') != teacher_name:
                # print(gr_name[i])
                i = i + 1
                #если введенное слово не соответствует массиву названий групп, то выдает ошибку:
        except: write_msg(event.object.peer_id, 'Такого преподавателя нет', get_random_id())
        else:
            search_url = "https://bincol.ru/rasp/prep.php?id=" + th_link[i-1]
            week_lessons = pd.read_html(search_url)
            j = 0
            message = ''
            sr = ''
            send_full_lessons(week_lessons,user_id,get_random_id(), message)
            # print(search_url)
        # print(gr_link)
    else:
        print('ERROR')


def send_full_lessons(week_lessons,user_id,random_id, message ):
    for j in range(6):
        qw = pd.DataFrame(week_lessons[j + 1], dtype=object)
        day = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
        qw = qw.fillna(0)
        try:
            qw[3] = qw[3].astype('int')
        except:
            pass
        qw = qw.to_records(index=False).tolist()
        i = 0

        message = message + day[j] + '\n'
        j = j + 1

        for i in range(len(qw)):
            st = qw[i]
            sr = ' '.join(str(x) for x in st)
            sr = re.sub(r"0 0", " ", sr)
            message = message + '\n' + sr
            i = i + 1
        message = message + '\n' + '\n'
    print(message)
    write_msg(user_id, message, random_id)


# pcs41_parse(base_url, header s)

switch_case = {
    'пн': 0,
    'вт': 1,
    'ср': 2,
    'чт': 3,
    'пт': 4,
    'сб': 5,
    'на неделю': 6
}
def where_day(index, user_id):
    db = client.pymongo_test
    users_db = db.users
    collection = db.lessons
    cursor = users_db.find({"user_id": user_id}, {"user_id": 1, "_id": 0}).count()
    if cursor > 0:
        tmp = users_db.find({"user_id": user_id}, {"group_name": 1, "user_id": 1, "_id": 0})
        group_name = tmp.next()["group_name"]
        one_group = collection.find({"group_name": group_name }, {"group_name": 1, "lessons": 1, "_id": 0})
        full_lessons_db = list(one_group.next()["lessons"])
        if index < 6:
            message = full_lessons_db[index]
            write_msg(user_id, message , get_random_id())
        else:
            i = 0
            message = ""
            for i in range(6):
                message = message + full_lessons_db[i]
                i = i + 1
            write_msg(user_id, message, get_random_id())
    else:
        write_msg(user_id, "Вы еще не зарегестрировались", get_random_id())


token = "6c7056c8f01aa6cab4faa9bac46a6aeb7521cbef2b9bb94e0a6e660731832b000afe04901e79613fc9e86"

def check_group(user_id, group_name):
    session = requests.Session()
    request = requests.get(base_url, headers=headers)
    tree = lh.document_fromstring(request.content)
    if request.status_code == 200:
        gr_name = tree.xpath('//p/a/text()')
        gr_link = tree.xpath('//p/a/@href')
        i = 0
        try:
            while gr_name[i] != group_name:
                i = i + 1
                # если введенное слово не соответствует массиву названий групп, то выдает ошибку:
        except:

            write_msg(user_id, 'Такой группы нет', get_random_id())

        else:

            link = "https://bincol.ru/rasp/" + gr_link[i]
            registration(user_id, group_name,link)

def check_teacher_2(user_id, teacher_name):
    session = requests.Session()
    request = requests.get(teacher_url, headers=headers)
    tree = lh.document_fromstring(request.content)
    if request.status_code == 200:
        th_name = tree.xpath('//option/text()')
        th_link = tree.xpath('//option/@value')
        i = 1
        try:
            while th_name[i].upper().replace(' ', '') != teacher_name:
                # print(gr_name[i])
                i = i + 1
                # если введенное слово не соответствует массиву названий групп, то выдает ошибку:
        except:
            write_msg(event.object.peer_id, 'Такого преподавателя нет', get_random_id())
        else:

            link = "https://bincol.ru/rasp/prep.php?id=" + th_link[i - 1]
            registration(user_id, teacher_name, link)
    else:
        print('ERROR')



def registration(user_id, group_name,link ):
    db = client.pymongo_test
    collection = db.users
    cursor = collection.find({"user_id": user_id}, {"user_id": 1, "_id": 0}).count()
    if cursor > 0:
        tmp = collection.find({"user_id": user_id}, {"group_name": 1, "user_id": 1, "_id": 0})
        tmp_name = tmp.next()["group_name"]
        write_msg(user_id, 'Вы уже зарегестрированы в группе ' + tmp_name, get_random_id())
    else:
        collection.insert(
            {"group_name": group_name, "user_id": user_id })
        add_groups(group_name, link)
        # write_msg(user_id, 'Вы зарегестрировались в группе '+ group_name , get_random_id())
        write_bot(user_id, 'Вы зарегестрировались в группе '+ group_name, get_random_id(), day_lessons)

def add_groups(group_name, link):
    db = client.pymongo_test
    collection = db.groups
    cursor = collection.find({"group_name": group_name}, {"group_name": 1, "_id": 0}).count()
    if cursor > 0:
        pass
    else:
        collection.insert(
            {"group_name": group_name, "link": link})
        fill_lesons(group_name, link)


def fill_lesons(group_name, link):
    db = client.pymongo_test
    collection = db.lessons
    cursor = collection.find({"group_name": group_name}, {"group_name": 1, "_id": 0}).count()
    if cursor > 0:
        pass
    else:
        collection.insert(
            {"group_name": group_name})
        lessons_db = pd.read_html(link)
        j = 0
        message = ''
        sr = ''
        d = 0
        for j in range(6):
            qw = pd.DataFrame(lessons_db[j+1], dtype=object)
            day = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
            qw = qw.fillna(0)
            try:
                qw[3] = qw[3].astype('int')
            except:
                pass
            qw = qw.to_records(index=False).tolist()
            i = 0
            message = ''

            message = message + day[j] + '\n'
            j = j + 1

            for i in range(len(qw)):
                st = qw[i]
                sr = ' '.join(str(x) for x in st)
                sr = re.sub(r"0 0", " ", sr)
                message = message + '\n' + sr
                i = i + 1
            message = message + '\n' + '\n'
            collection.update(
                {"group_name": group_name}, {"$push": {"lessons": message}})



def rereg(user_id, group_name):
    db = client.pymongo_test
    collection = db.users
    groups = db.groups
    lessons = db.lessons
    tmp = collection.find({"user_id": user_id}, {"group_name": 1, "user_id":1, "_id": 0})
    tmp_name = tmp.next()["group_name"]
    session = requests.Session()
    request = requests.get(base_url, headers=headers)
    tree = lh.document_fromstring(request.content)
    i = 0
    if request.status_code == 200:
        gr_name = tree.xpath('//p/a/text()')
        try:
            while gr_name[i] != group_name:
                i = i + 1
                # если введенное слово не соответствует массиву названий групп, то выдает ошибку:
        except:
            write_msg(user_id, 'Такой группы нет', get_random_id())


        else:

            try:
                collection.remove({"user_id": user_id})
                if collection.find({"group_name": tmp_name}).count() < 1:
                    groups.remove({"group_name": tmp_name})
                    lessons.remove({"group_name": tmp_name})
                    check_group(user_id, group_name)
                else:
                    pass
            except:
                write_msg(user_id, 'Вы еще не зарегестрировались', get_random_id())

def th_rereg(user_id, teacher_name):
    db = client.pymongo_test
    collection = db.users
    groups = db.groups
    lessons = db.lessons
    tmp = collection.find({"user_id": user_id}, {"group_name": 1, "user_id": 1, "_id": 0})
    tmp_name = tmp.next()["group_name"]
    session = requests.Session()
    request = requests.get(teacher_url, headers=headers)
    tree = lh.document_fromstring(request.content)
    i = 1
    if request.status_code == 200:
        th_name = tree.xpath('//option/text()')
        try:
            while th_name[i].upper().replace(' ', '') != teacher_name:
                i = i + 1
                # если введенное слово не соответствует массиву названий групп, то выдает ошибку:
        except:

            write_msg(user_id, 'Такого преподавателя нет', get_random_id())
        else:
            try:
                collection.remove({"user_id": user_id})
                if collection.find({"group_name": tmp_name}).count() < 1:
                    groups.remove({"group_name": tmp_name})
                    lessons.remove({"group_name": tmp_name})
                    check_teacher_2(user_id, teacher_name)
                else:
                    pass
            except:
                write_msg(user_id, 'Вы еще не зарегестрировались', get_random_id())

def recheck():
    db = client.pymongo_test
    collection = db.lessons
    linki = db.groups
    users_db = db.users
    groups = []
    for gr in collection.find({}, {"group_name": 1, "_id": 0}):
        groups.append(gr["group_name"])
    i = 0
    for i in range(len(groups)):

        one_group = collection.find({"group_name": groups[i]}, {"group_name": 1, "lessons": 1, "_id": 0})
        full_lessons_db = list(one_group.next()["lessons"])
        print("Проверяется группа" + groups[i])

        linkq = linki.find({"group_name": groups[i]}, {"link": 1, "_id": 0})
        link = linkq.next()["link"]

        lessons_db = pd.read_html(link)
        j = 0
        message = ''
        full_lessons_parse = []
        sr = ''
        d = 0
        for j in range(6):
            qw = pd.DataFrame(lessons_db[j + 1], dtype=object)
            day = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
            qw = qw.fillna(0)
            try:
                qw[3] = qw[3].astype('int')
            except:
                pass
            qw = qw.to_records(index=False).tolist()
            i = 0
            message = ''

            message = message + day[j] + '\n'
            j = j + 1

            for t in range(len(qw)):
                st = qw[t]
                sr = ' '.join(str(x) for x in st)
                sr = re.sub(r"0 0", " ", sr)
                message = message + '\n' + sr
                t = t + 1
            message = message + '\n' + '\n'
            full_lessons_parse.append(message)
        j = 0
        for j in range(6):
            if full_lessons_db[j] != full_lessons_parse[j] :
                users = []
                for us in users_db.find({"group_name": groups[i]}, {"user_id": 1, "_id": 0}):
                    users.append(us["user_id"])
                l = 0
                for l in range(len(users)):
                    write_msg(users[l], "Ваше расписание изменилось: \n\n"+full_lessons_parse[j], get_random_id())
                    collection.update(
                        {"group_name": groups[i]}, {"$set": {"lessons": full_lessons_parse}})
                    l = l + 1
                j = j + 1
            else:
                pass
        i = i + 1
    threading.Timer(600, recheck).start()

def write_msg(user_id, message, random_id):
    vk_session.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': random_id})

def write_bot(user_id, message, random_id, keyboard):
    vk_session.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': random_id, 'keyboard': keyboard})


t = threading.Thread(target=recheck)
t.start()

vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, 189331291)

for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        if event.from_user:
            mes = event.object.text.lower()
            if mes.find('/help')>= 0 or mes.find('начать')  >= 0:
                write_msg(event.object.peer_id, ' Если вы ученик:\n\n Регистрация: введите /reg и название своей группы \n(/reg 41пкс)\n\n '
                                                ' Чтобы зарегестрироваться под другой группой введите /rereg название группы\n\n'
                                                ' Если вы учитель:\n\n Регистрация: введите /threg и свою фамилию с инициалами \n(/threg Иванов И.И.)\n\n '
                                                ' Чтобы зарегестрироваться под другим преподавателем введите /threreg и свою фамилию с инициалами\n'
                                                '----------------------------------'
                                                'Зарегестрированному пользователю присылаются изменения в его расписании\n\n'
                                                ' Чтобы посмотреть расписание любой группы введите ее название\n\n'
                                                ' Чтобы посмотреть расписание любоого преподавателя введите его фамилию с инициалами\n\n', get_random_id())
            elif mes.find('/rereg') >= 0:
                group_name = event.object.text.upper().replace('/REREG', '').replace(' ', '')
                print(group_name)
                rereg(event.object.peer_id, group_name)
            elif mes.find('/reg') >= 0:
                group_name = event.object.text.upper().replace('/REG', '').replace(' ', '')
                print(group_name+ "рег")
                check_group(event.object.peer_id, group_name)
                # print(group_name)
                # parse(base_url, headers,group_name, event.object.peer_id, get_random_id())
            elif mes.find('/threreg') >= 0:
                teacher_name = event.object.text.upper().replace('/THREREG', '').replace(' ', '')
                th_rereg(event.object.peer_id, teacher_name)
            elif mes.find('/threg') >= 0:
                teacher_name = event.object.text.upper().replace('/THREG', '').replace(' ', '')
                check_teacher_2(event.object.peer_id, teacher_name)
            elif mes in switch_case:
                index = switch_case[mes]
                where_day(index, event.object.peer_id)

            elif check(group_name = event.object.text.upper().replace(' ', '')) is True:
                group_name = event.object.text.upper().replace(' ', '')
                print(group_name)
                parse(group_name, event.object.peer_id, get_random_id())
            elif check_teacher(teacher_name = event.object.text.upper().replace('УЧИТЕЛЬ', '').replace(' ', '')) is True:
                teacher_name = event.object.text.upper().replace('УЧИТЕЛЬ', '').replace(' ', '')
                teacher_parse(teacher_name, event.object.peer_id)

            else:
                write_msg(event.object.peer_id, 'Возможно вы некорректно ввели название группы или команду.\n Для получения информации напишите /help', get_random_id())


