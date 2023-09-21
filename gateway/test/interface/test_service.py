import json

from mock import call

from gateway.exceptions import OrderNotFound, ProductNotFound

class TestDeleteProduct(object):
    def test_can_delete_product(self, gateway_service, web_session):
        # Mock the delete RPC call in gateway_service
        gateway_service.products_rpc.delete.return_value = {}

        # Call the delete endpoint
        response = web_session.delete('/products/the_odyssey')

        # Assert the response and verify the RPC call
        assert response.status_code == 204
        assert response.content == b''
        assert gateway_service.products_rpc.delete.call_args_list == [
            call("the_odyssey")
        ]

class TestGetProduct(object):
    def test_can_get_product(self, gateway_service, web_session):
        gateway_service.products_rpc.get.return_value = {
            "in_stock": 10,
            "maximum_speed": 5,
            "id": "the_odyssey",
            "passenger_capacity": 101,
            "title": "The Odyssey"
        }
        response = web_session.get('/products/the_odyssey')
        assert response.status_code == 200
        assert gateway_service.products_rpc.get.call_args_list == [
            call("the_odyssey")
        ]
        assert response.json() == {
            "in_stock": 10,
            "maximum_speed": 5,
            "id": "the_odyssey",
            "passenger_capacity": 101,
            "title": "The Odyssey"
        }

    def test_product_not_found(self, gateway_service, web_session):
        gateway_service.products_rpc.get.side_effect = (
            ProductNotFound('missing'))

        # call the gateway service to get order #1
        response = web_session.get('/products/foo')
        assert response.status_code == 404
        payload = response.json()
        assert payload['error'] == 'PRODUCT_NOT_FOUND'
        assert payload['message'] == 'missing'


class TestCreateProduct(object):
    def test_can_create_product(self, gateway_service, web_session):
        response = web_session.post(
            '/products',
            json.dumps({
                "in_stock": 10,
                "maximum_speed": 5,
                "id": "the_odyssey",
                "passenger_capacity": 101,
                "title": "The Odyssey"
            })
        )
        assert response.status_code == 200
        assert response.json() == {'id': 'the_odyssey'}
        assert gateway_service.products_rpc.create.call_args_list == [call({
                "in_stock": 10,
                "maximum_speed": 5,
                "id": "the_odyssey",
                "passenger_capacity": 101,
                "title": "The Odyssey"
            })]

    def test_create_product_fails_with_invalid_json(
        self, gateway_service, web_session
    ):
        response = web_session.post(
            '/products', 'NOT-JSON'
        )
        assert response.status_code == 400
        assert response.json()['error'] == 'BAD_REQUEST'

    def test_create_product_fails_with_invalid_data(
        self, gateway_service, web_session
    ):
        response = web_session.post(
            '/products',
            json.dumps({"id": 1})
        )
        assert response.status_code == 400
        assert response.json()['error'] == 'VALIDATION_ERROR'

class TestListOrders(object):
    def test_can_list_orders(self, gateway_service, web_session):
        # Setup mock orders-service response
        gateway_service.orders_rpc.list_orders.return_value = [
            {
                'id': 1,
                'order_details': [
                    {
                        'id': 1,
                        'quantity': 2,
                        'product_id': 'the_odyssey',
                        'price': '200.00'
                    }
                ]
            },
            {
                'id': 2,
                'order_details': [
                    {
                        'id': 3,
                        'quantity': 3,
                        'product_id': 'the_odyssey',
                        'price': '300.00'
                    }
                ]
            }
        ]

        gateway_service.products_rpc.get.return_value = {
            "in_stock": 10,
            "maximum_speed": 5,
            "id": "the_odyssey",
            "passenger_capacity": 101,
            "title": "The Odyssey"
            }

        # Call the gateway service to list orders
        response = web_session.get('/orders')
        assert response.status_code == 200

        # Check if the product will come as part of the order
        for order in response.json():
            # Assumes one order detail per order.
            order_details = order['order_details'][0]
            assert len(order_details['product']) > 0

        # Check dependencies called as expected
        assert [call()] == gateway_service.orders_rpc.list_orders.call_args_list
        assert [call("the_odyssey"), call("the_odyssey")] == gateway_service.products_rpc.get.call_args_list

    def test_list_orders_empty(self, gateway_service, web_session):
        # Setup mock orders-service response for an empty list
        gateway_service.orders_rpc.list_orders.return_value = []

        # Call the gateway service to list orders
        response = web_session.get('/orders')
        assert response.status_code == 200
        assert response.json() == []

        # Check dependencies called as expected
        assert [call()] == gateway_service.orders_rpc.list_orders.call_args_list

class TestGetOrder(object):

    def test_can_get_order(self, gateway_service, web_session):
        # setup mock orders-service response:
        gateway_service.orders_rpc.get_order.return_value = {
            'order_details': [
                {
                    'quantity': 1,
                    'price': '100000.99',
                    'product_id': 'the_odyssey',
                    'id': 8197
                }
            ],
            'id': 8197
        }

        gateway_service.products_rpc.get.return_value = {
            'title': 'The Odyssey',
            'passenger_capacity': 101,
            'in_stock': 9,
            'maximum_speed': 5,
            'id': 'the_odyssey'
        }

        # call the gateway service to get order #8197
        response = web_session.get('/orders/8197')
        assert response.status_code == 200
        # This again, assumes on order details per order.
        product_dict = response.json()['order_details'][0]['product']
        assert isinstance(product_dict, dict) and len(product_dict) > 0

    def test_order_not_found(self, gateway_service, web_session):
        gateway_service.orders_rpc.get_order.side_effect = (
            OrderNotFound('missing'))

        # call the gateway service to get order #1
        response = web_session.get('/orders/1')
        assert response.status_code == 404
        payload = response.json()
        assert payload['error'] == 'ORDER_NOT_FOUND'
        assert payload['message'] == 'missing'


class TestCreateOrder(object):

    def test_can_create_order(self, gateway_service, web_session):
        # setup mock products-service response:
        gateway_service.products_rpc.get.return_value = {
            'id': 'the_odyssey',
            'in_stock': 10,
            'maximum_speed': 5,
            'passenger_capacity': 101,
            'title': 'The Odyssey'
        }

        # setup mock create response
        gateway_service.orders_rpc.create_order.return_value = {
            'id': 11,
            'order_details': []
        }

        # call the gateway service to create the order
        response = web_session.post(
            '/orders',
            json.dumps({
                'order_details': [
                    {
                        'product_id': 'the_odyssey',
                        'price': '41.00',
                        'quantity': 3
                    }
                ]
            })
        )
        assert response.status_code == 200
        assert response.json() == {'id': 11}
        assert gateway_service.products_rpc.get.call_args_list == [call('the_odyssey')]
        assert gateway_service.orders_rpc.create_order.call_args_list == [
            call([
                {'product_id': 'the_odyssey', 'quantity': 3, 'price': '41.00'}
            ])
        ]

    def test_create_order_fails_with_invalid_json(
        self, gateway_service, web_session
    ):
        # call the gateway service to create the order
        response = web_session.post(
            '/orders', 'NOT-JSON'
        )
        assert response.status_code == 400
        assert response.json()['error'] == 'BAD_REQUEST'

    def test_create_order_fails_with_invalid_data(
        self, gateway_service, web_session
    ):
        # call the gateway service to create the order
        response = web_session.post(
            '/orders',
            json.dumps({
                'order_details': [
                    {
                        'product_id': 'the_odyssey',
                        'price': '41.00',
                    }
                ]
            })
        )
        assert response.status_code == 400
        assert response.json()['error'] == 'VALIDATION_ERROR'

    def test_create_order_fails_with_unknown_product(
        self, gateway_service, web_session
    ):

        # call the gateway service to create the order
        response = web_session.post(
            '/orders',
            json.dumps({
                'order_details': [
                    {
                        'product_id': 'unknown',
                        'price': '41',
                        'quantity': 1
                    }
                ]
            })
        )
        # The code 500 happens in this case because it tries
        # to get the product when the create order is invoked.
        # This is not an ideal response code for this case.
        assert response.status_code == 500
        assert response.json()['error'] == 'UNEXPECTED_ERROR'
