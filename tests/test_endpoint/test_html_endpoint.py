from unittest import TestCase
from unittest.mock import Mock

from gatekeeper import Request, HtmlRequest, HtmlEndpoint


class HtmlEndpointTestCase(TestCase):

    def test_request_gets_converted_to_html_request_inside_endpoint(self):
        class HtmlTestEndpoint(HtmlEndpoint):
            endpoint_path = '/'
            def get(self, request, response):
                assert isinstance(request, HtmlRequest)
        endpoint = HtmlTestEndpoint()
        request = Request({'REQUEST_METHOD': 'GET', 'PATH_INFO': '/'})
        endpoint.handle_request(request)

    def test_response_has_correct_content_type(self):
        endpoint = HtmlEndpoint()
        endpoint.get = Mock()
        request = Request({'REQUEST_METHOD': 'GET', 'PATH_INFO': '/'})
        response = endpoint.handle_request(request)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8')

    def test_endpoint_sets_response_in_request(self):
        class HtmlTestEndpoint(HtmlEndpoint):
            path = '/'
            def get(self, request, response):
                assert request.response is response
        endpoint = HtmlTestEndpoint()
        request = Request({'REQUEST_METHOD': 'GET', 'PATH_INFO': '/'})
        endpoint.handle_request(request)
