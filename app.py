from flask import Flask, session, render_template, request, redirect, url_for, flash
from flask_session import Session
import requests
import os
import logging
from logging.handlers import RotatingFileHandler

# 로깅 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
logger.addHandler(handler)

# ... existing imports ...

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

class MenuItem:
    def __init__(self, name, price, image, inventory):
        self.name = name
        self.price = price
        self.image = image
        self.inventory = inventory

    def is_sold_out(self):
        return self.inventory <= 0

class OrderItem:
    def __init__(self, item, quantity):
        self.item = item
        self.quantity = quantity

    def get_total_price(self):
        return self.item.price * self.quantity

class Order:
    def __init__(self):
        self.items = []
        self.table_number = None

    def add_item(self, order_item):
        for existing_item in self.items:
            if existing_item.item.name == order_item.item.name:
                existing_item.quantity += order_item.quantity
                return
        self.items.append(order_item)

    def remove_item(self, item_name):
        self.items = [item for item in self.items if item.item.name != item_name]

    def get_total(self):
        return sum(item.get_total_price() for item in self.items)

# 단품 메뉴 리스트
single_items = [
    MenuItem("슈뢰딩거의 고..에란말이", 6000, "egg.jpg", 25),
    MenuItem("오일러.. 볶은 제육볶음", 9000, "jeyouk.jpg", 20),
    MenuItem("하버의 독일 소세지 야채볶음", 7000, "ssoya.jpg", 40),
    MenuItem("보일 랑말랑한 어묵탕", 8000, "odaeng.jpg", 5),
    MenuItem("장영실의 최애 떡갈비", 7000, "dduk.jpg", 26),
    MenuItem("뉴턴의 사과 아닌 황도", 4000, "hwangdo.jpg", 48),
    MenuItem("우리 몸에서 70%를 차지하고, 끓는점 373.14K, 녹는점 273.14K, 밀도는 4'C에서 가장 큰, 무색 무취의 액체", 500, "water.jpg", 150)
]

# 세트 메뉴 리스트
set_menus = [
    MenuItem("어제쏘 세트 (제육 + 쏘야 + 어묵탕)", 23000, "set1.jpg", 10),
    MenuItem("퀴리부부 세트 (떡갈비 + 어묵탕)", 14000, "set2.jpg", 10)
]

@app.route('/')
def index():
    order = session.get('order', Order())
    return render_template('index.html', single_items=single_items, set_menus=set_menus, total=order.get_total())

@app.route('/order', methods=['POST'])
def order_menu():
    order = session.get('order', Order())
    item_index = int(request.form.get('item_index'))
    item_type = request.form.get('item_type')
    quantity = int(request.form.get('quantity'))
    table_number = request.form.get('table_number')
    order.table_number = table_number

    if item_type == 'single':
        menu_item = single_items[item_index]
    else:
        menu_item = set_menus[item_index]

    if menu_item.inventory < quantity:
        flash(f"Sorry, we only have {menu_item.inventory} of {menu_item.name} left.")
        return redirect(url_for('index'))

    menu_item.inventory -= quantity
    order.add_item(OrderItem(menu_item, quantity))
    session['order'] = order
    return redirect(url_for('index'))

@app.route('/cart', methods=['GET'])
def view_cart():
    order = session.get('order', Order())
    return render_template('cart.html', order=order)

@app.route('/update_table_number', methods=['POST'])
def update_table_number():
    order = session.get('order', Order())
    table_number = request.form.get('table_number')
    order.table_number = table_number
    session['order'] = order
    return redirect(url_for('view_cart'))

@app.route('/remove_item', methods=['POST'])
def remove_item():
    order = session.get('order', Order())
    item_name = request.form.get('item_name')
    for item in single_items + set_menus:
        if item.name == item_name:
            item.inventory += next((order_item.quantity for order_item in order.items if order_item.item.name == item_name), 0)
            break
    order.remove_item(item_name)
    session['order'] = order
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['POST'])
def checkout():
    order = session.get('order', Order())
    table_number = request.form.get('table_number')
    if not table_number:
        return redirect(url_for('view_cart'))
    order.table_number = table_number
    total = order.get_total()
    send_order_to_server(order.items, total)
    session.pop('order', None)  # 주문 완료 후 세션에서 주문 정보 삭제
    return render_template('checkout.html', total=total)

@app.route('/orders', methods=['GET'])
def get_orders():
    orders = fetch_orders_from_server()
    return render_template('orders.html', orders=orders)

def send_order_to_server(items, total):
    api_url = os.getenv("API_URL", "https://port-0-server-1ru12mlw71p1z1.sel5.cloudtype.app/api/orders")
    headers = {'Content-Type': 'application/json'}
    data = {
        "table_number": session.get('order', Order()).table_number,
        "items": [{"name": item.item.name, "price": item.item.price, "quantity": item.quantity} for item in items],
        "total": total
    }
    response = requests.post(api_url, json=data, headers=headers)
    logger.info(f"Status Code: {response.status_code}, Response: {response.json()}")

def fetch_orders_from_server():
    api_url = os.getenv("API_URL", "https://port-0-server-1ru12mlw71p1z1.sel5.cloudtype.app/api/orders")
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json().get('orders', [])
    return []

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)), debug=False)
