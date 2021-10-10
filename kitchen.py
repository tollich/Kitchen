import queue
import time
from flask import Flask, request
import threading
import requests

time_unit = 1
foods_list = queue.Queue()
orders = []
app = Flask(__name__)

restaurant_cooks = [{
    "id": 1,
    "rank": 3,
    "proficiency": 3,
    "name": "Cook1",
}, {
    "id": 2,
    "rank": 2,
    "proficiency": 3,
    "name": "Cook2",
}, {
    "id": 3,
    "rank": 2,
    "proficiency": 3,
    "name": "Cook3",
}]

menu = [{
    "id": 1,
    "name": "pizza",
    "preparation-time": 20,
    "complexity": 2,
    "cooking-apparatus": "oven"
}, {
    "id": 2,
    "name": "salad",
    "preparation-time": 10,
    "complexity": 1,
    "cooking-apparatus": None
}, {
    "id": 4,
    "name": "Scallop Sashimi with Meyer Lemon Confit",
    "preparation-time": 32,
    "complexity": 3,
    "cooking-apparatus": None
}, {
    "id": 5,
    "name": "Island Duck with Mulberry Mustard",
    "preparation-time": 35,
    "complexity": 3,
    "cooking-apparatus": "oven"
}, {
    "id": 6,
    "name": "Waffles",
    "preparation-time": 10,
    "complexity": 1,
    "cooking-apparatus": "stove"
}, {
    "id": 7,
    "name": "Aubergine",
    "preparation-time": 20,
    "complexity": 2,
    "cooking-apparatus": None
}, {
    "id": 8,
    "name": "Lasagna",
    "preparation-time": 30,
    "complexity": 2,
    "cooking-apparatus": "oven"
}, {
    "id": 9,
    "name": "Burger",
    "preparation-time": 15,
    "complexity": 1,
    "cooking-apparatus": "oven"
}, {
    "id": 10,
    "name": "Gyros",
    "preparation-time": 15,
    "complexity": 1,
    "cooking-apparatus": None
}]

@app.route('/order', methods=['POST'])

def cooking(cook, food_items: queue.Queue):
    while True:
        try:
            food_item = food_items.get_nowait()
            food_details = next((f for f in menu if f['id'] == food_item['food_id']), None)
            (idx, order_details) = next(((idx, order) for idx, order in enumerate(orders) if order['order_id'] == food_item['order_id']), (None, None))
            # check if cook can afford to do this type of food
            print(f'{threading.current_thread().name} is cooking {food_details["name"]} for order {order_details["order_id"]}')
            time.sleep(food_details['preparation-time'] * time_unit)
            print(f'{threading.current_thread().name} cook has finished the order {order_details["order_id"]}')
            orders[idx]['cooking_details'].put({'food_id': food_details['id'], 'cook_id': cook['id']})
            print(f'Calculating')
            payload = {
                        **orders[idx],
                        'cooking_details': list(orders[idx]['cooking_details'].queue)
                    }
            requests.post('http://localhost:3000/distribution', json=payload, timeout=0.0000000001)
        except Exception as e:
                pass


def kitchen():
    main_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=3030, debug=False, use_reloader=False), daemon=True)
    main_thread.start()

    for _, cook in enumerate(restaurant_cooks):
        cook_thread = threading.Thread(target=cooking, args=(cook, foods_list,), daemon=True)
        cook_thread.start()

    while True:
        pass


if __name__ == '__main__':
    kitchen()