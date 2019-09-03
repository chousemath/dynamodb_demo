import boto3
from random import randrange
from time import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect

app = Flask(__name__, static_url_path='/static')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Order')
sizes = [
        'short',
        'tall',
        'grande',
        'venti',
        'trenta',
        ]

@app.route('/')
def home_page():
    return render_template('home.html')

@app.route('/orders/complete/<string:order_number>')
def complete_order(order_number: str):
    print(order_number)
    table.update_item(
            Key={
                'order_number': order_number,
            },
            UpdateExpression='SET order_status = :val1, completed_at = :val2',
            ExpressionAttributeValues={
                ':val1': 1,
                ':val2': int(time()),
            },
    )
    return redirect('/orders')

@app.route('/orders/incomplete/<string:order_number>')
def incomplete_order(order_number: str):
    print(order_number)
    table.update_item(
            Key={
                'order_number': order_number,
            },
            UpdateExpression='SET order_status = :val1',
            ExpressionAttributeValues={
                ':val1': 0,
            },
    )
    return redirect('/orders')

@app.route('/orders/delete/<string:order_number>')
def delete_order(order_number: str):
    print(order_number)
    table.delete_item(Key={
        'order_number': order_number,
    })
    return redirect('/orders')

@app.route('/orders', methods=['POST', 'GET'])
def create_order():
    if request.method == 'POST':
        data = request.form
        try:
            quantity = int(data['order_quantity'])
            size = int(data['product_size'])
            price = int(data['price'])
            if quantity == 1:
                table.put_item(Item={
                    'product_name': data['product_name'],
                    'product_size': size,
                    'price': price,
                    'customer_nickname': data['customer_nickname'],
                    'order_number': f'{randrange(1_000_000, 9_999_999)}-{int(time())}',
                    'order_status': 0,
                })
            else:
                with table.batch_writer() as batch:
                    for i in range(quantity):
                        batch.put_item(Item={
                            'product_name': data['product_name'],
                            'product_size': size,
                            'price': price,
                            'customer_nickname': data['customer_nickname'],
                            'order_number': f'{randrange(1_000_000, 9_999_999)}-{int(time())}',
                            'order_status': 0,
                        })
            return render_template('home.html')
        except Exception as e:
            print(e)
            return render_template('home.html')
    else:
        response = table.scan()
        data = response['Items']
        while response.get('LastEvaluatedKey'):
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])
        for x in data:
            x['product_size'] = sizes[int(x['product_size'] - 1)]
            if 'completed_at' in x:
                x['completed_at'] = datetime.fromtimestamp(x['completed_at']).strftime("%m/%d/%Y, %H:%M:%S")
        return render_template(
                'orders.html', 
                orders_incomplete=[x for x in data if x['order_status'] == 0],
                orders_complete=[x for x in data if x['order_status'] == 1]
                )

@app.route('/orders<string:order_number>')
def get_order(order_number: str):
    pass
    
if __name__ == '__main__':
    app.run(port=5000) 

# The `partition key` (`primary key`) should be unique
# Using the same partition key for a new item will overwrite the old item
