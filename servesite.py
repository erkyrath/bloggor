#!/usr/bin/env python

import os.path
import argparse
import contextlib
import http.server
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

parser = argparse.ArgumentParser()

parser.add_argument('-b', '--bind', metavar='ADDRESS',
                    help='bind to this address '
                    '(default: all interfaces)')
parser.add_argument('-d', '--directory', default='site',
                    help='serve this directory '
                    '(default: current directory)')
parser.add_argument('-p', '--protocol', metavar='VERSION',
                    default='HTTP/1.0',
                    help='conform to this HTTP version '
                    '(default: %(default)s)')
parser.add_argument('port', default=8001, type=int, nargs='?',
                    help='bind to this port '
                    '(default: %(default)s)')

args = parser.parse_args()


class CleanHTTPRequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        res = SimpleHTTPRequestHandler.translate_path(self, path)
        if not os.path.exists(res) and not path.endswith('/'):
            if os.path.exists(res+'.html'):
                res += '.html'
        return res

# ensure dual-stack is not disabled; ref #38907
class DualStackServer(ThreadingHTTPServer):

        def server_bind(self):
            # suppress exception when protocol is IPv4
            with contextlib.suppress(Exception):
                self.socket.setsockopt(
                    socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            return super().server_bind()

        def finish_request(self, request, client_address):
            self.RequestHandlerClass(request, client_address, self,
                                     directory=args.directory)

print("http://localhost:%d/" % (args.port,))

http.server.test(
    HandlerClass=CleanHTTPRequestHandler,
    ServerClass=DualStackServer,
    port=args.port,
    bind=args.bind,
    protocol=args.protocol,
)
