from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# 주문 목록을 저장할 리스트
orders = []

@app.route('/api/orders', methods=['POST'])
def create_order():
    order_data = request.json
    orders.append(order_data)
    return jsonify({'status': 'success', 'order': order_data}), 201

@app.route('/api/orders', methods=['GET'])
def get_orders():
    if request.args.get('format') == 'json':
        return jsonify({'status': 'success', 'orders': orders}), 200
    return render_template('orders.html', orders=orders)


if __name__ == '__main__':
    app.run(port=5001, debug=True)