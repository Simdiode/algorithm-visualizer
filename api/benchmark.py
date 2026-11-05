"""Vercel Python Function: benchmark the same Python algorithm implementations."""

from server import Handler


class handler(Handler):
    def do_POST(self):
        self.path = "/api/benchmark"
        super().do_POST()
