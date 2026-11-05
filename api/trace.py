"""Vercel Python Function: reuse the validated local trace endpoint."""

from server import Handler


class handler(Handler):
    def do_POST(self):
        self.path = "/api/trace"
        super().do_POST()
