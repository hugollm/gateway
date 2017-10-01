import os
from unittest import TestCase

from gatekeeper.requests.request import Request
from gatekeeper.responses.response import Response
from gatekeeper.exceptions import ResponseNotSet
from .factory import mock_env


class RequestTestCase(TestCase):

    def test_request_method(self):
        env = mock_env()
        request = Request(env)
        env['REQUEST_METHOD'] = 'POST'
        request = Request(env)
        self.assertEqual(request.method, 'POST')

    def test_url(self):
        env = mock_env()
        env['wsgi.url_scheme'] = 'https'
        env['HTTP_HOST'] = 'myserver.com:8080'
        env['PATH_INFO'] = '/dashboard/products'
        env['QUERY_STRING'] = 'page=1&order=price'
        request = Request(env)
        self.assertEqual(request.url, 'https://myserver.com:8080/dashboard/products?page=1&order=price')

    def test_base_url(self):
        env = mock_env()
        env['wsgi.url_scheme'] = 'https'
        env['HTTP_HOST'] = 'myserver.com:8080'
        env['PATH_INFO'] = '/dashboard/products'
        env['QUERY_STRING'] = 'page=1&order=price'
        request = Request(env)
        self.assertEqual(request.base_url, 'https://myserver.com:8080')

    def test_scheme(self):
        env = mock_env()
        env['wsgi.url_scheme'] = 'https'
        request = Request(env)
        self.assertEqual(request.scheme, 'https')

    def test_host(self):
        env = mock_env()
        env['HTTP_HOST'] = 'myserver.com:8080'
        request = Request(env)
        self.assertEqual(request.host, 'myserver.com:8080')

    def test_path(self):
        env = mock_env()
        env['PATH_INFO'] = '/dashboard/products'
        request = Request(env)
        self.assertEqual(request.path, '/dashboard/products')

    def test_query_string(self):
        env = mock_env()
        env['QUERY_STRING'] = 'page=1&order=price'
        request = Request(env)
        self.assertEqual(request.query_string, 'page=1&order=price')

    def test_body(self):
        env = mock_env()
        env['wsgi.input'].write(b'<h1>Hello World</h1>')
        env['wsgi.input'].seek(0)
        request = Request(env)
        self.assertEqual(request.body, b'<h1>Hello World</h1>')

    def test_query(self):
        env = mock_env()
        env['QUERY_STRING'] = 'page=1&order=price'
        request = Request(env)
        self.assertEqual(request.query, {'page': '1', 'order': 'price'})

    def test_headers(self):
        env = mock_env()
        env['HTTP_AUTH'] = 'token'
        env['HTTP_X_FORWARDED_FOR'] = '203.0.113.195, 70.41.3.18, 150.172.238.178'
        request = Request(env)
        self.assertEqual(request.headers, {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, sdch',
            'accept-language': 'pt-BR,pt;q=0.8,en-US;q=0.6,en;q=0.4',
            'auth': 'token',
            'connection': 'keep-alive',
            'host': 'localhost:8000',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36',
            'x-forwarded-for': '203.0.113.195, 70.41.3.18, 150.172.238.178',
        })

    def test_cookies(self):
        env = mock_env()
        env['HTTP_COOKIE'] = 'foo=bar; bar=biz'
        request = Request(env)
        self.assertEqual(request.cookies, {'foo': 'bar', 'bar': 'biz'})

    def test_empty_cookies(self):
        env = mock_env()
        request = Request(env)
        self.assertEqual(request.cookies, {})

    def test_cookie_with_special_characters(self):
        env = mock_env()
        env['HTTP_COOKIE'] = 'token="abc/\\073\\054~\\341\\347[\'!\\"\\"]"'
        request = Request(env)
        self.assertEqual(request.cookies, {'token': 'abc/;,~áç[\'!""]'})

    def test_ip(self):
        env = mock_env()
        env['REMOTE_ADDR'] = '127.0.0.1'
        request = Request(env)
        self.assertEqual(request.ip, '127.0.0.1')

    def test_ip_with_x_forwarded_for_header(self):
        env = mock_env()
        env['HTTP_X_FORWARDED_FOR'] = '203.0.113.195, 70.41.3.18, 150.172.238.178'
        request = Request(env)
        self.assertEqual(request.ip, '203.0.113.195')

    def test_referer(self):
        env = mock_env()
        env['HTTP_REFERER'] = 'http://localhost:8000/app/hello'
        request = Request(env)
        self.assertEqual(request.referer, 'http://localhost:8000/app/hello')

    def test_empty_referer(self):
        env = mock_env()
        request = Request(env)
        self.assertIsNone(request.referer)

    def test_user_agent(self):
        env = mock_env()
        request = Request(env)
        self.assertEqual(request.user_agent, 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36')

    def test_empty_user_agent(self):
        env = mock_env()
        env.pop('HTTP_USER_AGENT')
        request = Request(env)
        self.assertEqual(request.user_agent, None)

    def test_messages(self):
        env = mock_env()
        env['HTTP_COOKIE'] = 'MESSAGE:foo=bar; MESSAGE:bar=biz'
        request = Request(env)
        request.set_response(Response())
        self.assertEqual(request.messages, {'foo': 'bar', 'bar': 'biz'})

    def test_accessing_messages_requires_a_response_to_be_set(self):
        env = mock_env()
        request = Request(env)
        with self.assertRaises(ResponseNotSet):
            request.messages

    def test_accessing_messages_unsets_message_cookies(self):
        env = mock_env()
        env['HTTP_COOKIE'] = 'MESSAGE:foo=bar; MESSAGE:bar=biz'
        request = Request(env)
        response = Response()
        request.set_response(response)
        request.messages
        expected_cookie = 'MESSAGE:foo=; Expires=Thu, 01 Jan 1970 00:00:00 GMT'
        self.assertIn(('Set-Cookie', expected_cookie), response._wsgi_headers())
        expected_cookie = 'MESSAGE:bar=; Expires=Thu, 01 Jan 1970 00:00:00 GMT'
        self.assertIn(('Set-Cookie', expected_cookie), response._wsgi_headers())