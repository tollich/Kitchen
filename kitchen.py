import sys
from flask import Flask, request, jsonify
import requests
import random
import time
import concurrent.futures
from threading import Lock, Thread

cooks = []
names = ["Asma Millington", "Mariya Lynn", "Lewie Johnston", "Minnie Huber", "Katharine Finch"]
catch_phrases = ["I'll be back!", "Hasta la vista, baby", "I love the smell of napalm in the morning",
                 "Say hello to my little friend", "42"]

ID_HASH = 0
TIME_UNIT = 20
number_of_cooks = 2
cooking_apparatus_number = 1
stoves_and_ovens = []
mutex = Lock()
mutex1 = Lock()


class Cooks:
    def __init__(self, rank, proficiency, name, catch_phrase):
        self.rank = rank
        self.proficiency = proficiency
        self.name = name
        self.catch_phrase = catch_phrase
        self.dishes_to_prepare = []
        self.can_prepare = []
        self.ready_for_cooking = []
        self.pointer = []
        self.taken_apparatus = []

    def choose_order(self):
        global mutex
        global order_list
        max_priority = 0
        can_take = self.proficiency
        for id in order_list:
            if max_priority < order_list[id]["priority"]:
                max_priority = order_list[id]["priority"]

        for id in order_list:
            if order_list[id]["priority"] == max_priority:
                if len(order_list[id]["items"]) == 0:
                    mutex.acquire()
                    try:
                        self.send_order_back(order_list[id])
                        del order_list[id]
                    finally:
                        mutex.release()
                        break

                for item in order_list[id]["items"]:
                    if foods[item - 1]["complexity"] == self.rank or foods[item - 1]["complexity"] == self.rank - 1:
                        if len(self.dishes_to_prepare) < self.rank:
                            self.dishes_to_prepare.append(foods[item - 1])
                            self.pointer.append((foods[item - 1], id))

                        # order_list[id]["items"].remove(item)
                            can_take -= 1
                            if can_take == 0:
                                break

                        elif len(self.dishes_to_prepare) == self.rank:
                            break

            if can_take == 0 or len(self.dishes_to_prepare) == self.rank:
                break

        if len(self.dishes_to_prepare) != 0:
            self.start_cooking()

    def start_cooking(self):
        _dishes_to_prepare = list(self.dishes_to_prepare)
        for dish in _dishes_to_prepare:
            if dish["cooking-apparatus"] is None:
                self.can_prepare.append((dish, True))
                self.dishes_to_prepare.remove(dish)
            else:
                for apparatus in stoves_and_ovens:
                    if apparatus.name == dish["cooking-apparatus"] and apparatus.isFree:
                        apparatus.isFree = False
                        self.can_prepare.append((dish, True))
                        self.taken_apparatus.append(apparatus)
                        #  apparatus.isFree = True
                        self.dishes_to_prepare.remove(dish)

                    elif apparatus.name == dish["cooking-apparatus"] and not apparatus.isFree:
                        self.can_prepare.append((dish, False))
                        continue

        _can_prepare = list(self.can_prepare)
        mp_time = 0
        for pair in _can_prepare:
            if pair[1]:
                mp_time = mp_time if mp_time >= pair[0]["preparation-time"] else pair[0]["preparation-time"]
                self.ready_for_cooking.append(pair[0])
                self.can_prepare.remove(pair)

        time.sleep(mp_time / TIME_UNIT)
        for a in self.taken_apparatus:
            a.isFree = True
        self.taken_apparatus = []

        _ready_for_cooking = list(self.ready_for_cooking)
        _pointer = list(self.pointer)
        for dish in _ready_for_cooking:
            for pair in _pointer:
                global mutex1
                if pair[0] == dish:
                    mutex1.acquire()
                    try:
                        if pair[1] in order_list and dish["id"] in order_list[pair[1]]["items"]:
                            order_list[pair[1]]["items"].remove(dish["id"])
                    finally:
                        mutex1.release()
                    self.ready_for_cooking.remove(pair[0])
                    self.pointer.remove(pair)
                    break

    def send_order_back(self, order):
        res = requests.post('http://172.17.0.3:80/serve_order', json=order)


class CookingApparatus:
    def __init__(self, name):
        self.isFree = True
        self.name = name


foods = [{"id": 1, "name": "pizza", "preparation-time": 20, "complexity": 2, "cooking-apparatus": "oven"},
         {"id": 2, "name": "salad", "preparation-time": 10, "complexity": 1, "cooking-apparatus": None},
         {"id": 3, "name": "zeama", "preparation-time": 7, "complexity": 1, "cooking-apparatus": "stove"},
         {"id": 4, "name": "Scallop", "preparation-time": 32, "complexity": 3, "cooking-apparatus": None},
         {"id": 5, "name": "Island Duck", "preparation-time": 35, "complexity": 3, "cooking-apparatus": "oven"},
         {"id": 6, "name": "Waffles", "preparation-time": 10, "complexity": 1, "cooking-apparatus": "stove"},
         {"id": 7, "name": "Aubergine", "preparation-time": 20, "complexity": 2, "cooking-apparatus": None},
         {"id": 8, "name": "Lasagna", "preparation-time": 30, "complexity": 2, "cooking-apparatus": "oven"},
         {"id": 9, "name": "Burger", "preparation-time": 15, "complexity": 1, "cooking-apparatus": "oven"},
         {"id": 10, "name": "Gyros", "preparation-time": 15, "complexity": 1, "cooking-apparatus": None}]

seed_value = random.randrange(sys.maxsize)
random.seed(seed_value)

gordon = Cooks(3, 3, "Gordon Ramsay", "My gran could do better! And she’s dead!")
cooks.append(gordon)
rank = 3

"""
For custom cooks
cooker = Cooks(rank, proficiency, random.choice(names), random.choice(catch_phrases))
cooks.append(cooker)
"""

for i in range(1, number_of_cooks):
    rank -= 1
    proficiency = random.randint(1, 3)
    name = random.choice(names)
    catch_phrase = random.choice(catch_phrases)
    t = Cooks(rank, proficiency, name, catch_phrase)
    cooks.append(t)

# Creating stoves and ovens
for i in range(cooking_apparatus_number):
    s = CookingApparatus("stove")
    o = CookingApparatus("oven")
    stoves_and_ovens.append(s)
    stoves_and_ovens.append(o)

app = Flask(__name__)

global input_json
input_json = dict()


def start(cook):
    if order_list is not None:
        cook.choose_order()
        return "ok"
    return "Order list empty"


def change_priorities():
    now = time.time()
    for ident in order_list:
        if order_list[ident]["priority"] == 4 and now - order_list[ident]["time"] > 2 / TIME_UNIT:
            order_list[ident]["priority"] += 1
        elif order_list[ident]["priority"] == 3 and now - order_list[ident]["time"] > 5 / TIME_UNIT:
            order_list[ident]["priority"] += 1
        elif order_list[ident]["priority"] == 2 and now - order_list[ident]["time"] > 9 / TIME_UNIT:
            order_list[ident]["priority"] += 1
        elif order_list[ident]["priority"] == 1 and now - order_list[ident]["time"] > 13 / TIME_UNIT:
            order_list[ident]["priority"] += 1


order_list = dict()


@app.route('/get_order', methods=["POST", "GET"])
def get_posted_order():
    if request.method == "POST":
        input_json = request.get_json(force=True)
        global order_list
        global ID_HASH
        order_list[ID_HASH] = input_json
        order_list[ID_HASH]["time"] = time.time()
        ID_HASH += 1
        return jsonify(input_json)
    else:
        return jsonify(order_list)


@app.route('/start_kitchen')
def start_kitchen():
    while True:
        threads = []
        for i in range(len(cooks)):
            t = Thread(target=start, args=[cooks[i]])
            threads.append(t)
            t.start()

        for thread in threads:
            thread.join()

        change_priorities()
    return jsonify(order_list)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
