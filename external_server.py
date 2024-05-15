from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/orders', methods=['POST'])
def receive_order():
    data = request.get_json()
    
    # 주문 데이터 처리 (여기서는 단순히 출력)
    items = data.get('items', [])
    total = data.get('total', 0)
    
    print("Received order:")
    for item in items:
        print(f"Item: {item['name']}, Price: {item['price']}")
    print(f"Total: {total}")
    
    # 응답 생성
    response = {
        "status": "success",
        "message": "Order received",
        "received_items": items,
        "received_total": total
    }
    
    return jsonify({"status": "success"}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5001)  # 포트 번호는 필요에 따라 변경