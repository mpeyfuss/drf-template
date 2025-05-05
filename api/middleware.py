from rest_framework.renderers import JSONRenderer

from api.views import health


class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/health":
            # Why: https://stackoverflow.com/a/71572324
            response = health(request)
            response.accepted_renderer = JSONRenderer()
            response.accepted_media_type = "application/json"
            response.renderer_context = {}
            response.render()
            return response

        return self.get_response(request)
