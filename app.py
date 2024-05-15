from flask import Flask, render_template, request, redirect, url_for
import requests
import os

app = Flask(__name__)

class MenuItem:
    def __init__(self, name, price, image):
        self.name = name
        self.price = price
        self.image = image

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

menu_items = [
    MenuItem("계란말이", 4000, "egg.jpg"),
    MenuItem("황도", 4500, "hwangdo.jpg"),
    MenuItem("제육볶음", 5500, "jeyouk.jpg"),
    MenuItem("냉동 만두", 4000, "mandoo.jpg"),
    MenuItem("오뎅탕", 4500, "odaeng.jpg"),
    MenuItem("소세지 야채볶음", 5500, "ssoya.jpg")
]

order = Order()

@app.route('/')
def index():
    return render_template('index.html', menu_items=menu_items, total=order.get_total())

@app.route('/order', methods=['POST'])
def order_menu():
    item_index = int(request.form.get('item_index'))
    quantity = int(request.form.get('quantity'))
    table_number = request.form.get('table_number')
    order.table_number = table_number
    order.add_item(OrderItem(menu_items[item_index], quantity))
    return redirect(url_for('index'))

@app.route('/cart', methods=['GET'])
def view_cart():
    return render_template('cart.html', order=order)

@app.route('/update_table_number', methods=['POST'])
def update_table_number():
    table_number = request.form.get('table_number')
    order.table_number = table_number
    return redirect(url_for('view_cart'))

@app.route('/remove_item', methods=['POST'])
def remove_item():
    item_name = request.form.get('item_name')
    order.remove_item(item_name)
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['POST'])
def checkout():
    table_number = request.form.get('table_number')
    if not table_number:
        return redirect(url_for('view_cart'))
    order.table_number = table_number
    total = order.get_total()
    send_order_to_server(order.items, total)
    order.items.clear()
    return render_template('checkout.html', total=total)

@app.route('/orders', methods=['GET'])
def get_orders():
    orders = fetch_orders_from_server()
    return render_template('orders.html', orders=orders)

def send_order_to_server(items, total):
    api_url = os.getenv("API_URL", "http://localhost:5001/api/orders")
    headers = {'Content-Type': 'application/json'}
    data = {
        "table_number": order.table_number,
        "items": [{"name": item.item.name, "price": item.item.price, "quantity": item.quantity} for item in items],
        "total": total
    }
    response = requests.post(api_url, json=data, headers=headers)
    print("Status Code:", response.status_code)
    print("Response:", response.json())

def fetch_orders_from_server():
    api_url = os.getenv("API_URL", "http://localhost:5001/api/orders")
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json().get('orders', [])
    return []

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)), debug=False)
