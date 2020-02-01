#! /usr/bin/env python3
"""Simple Threaded HTTP 1.1 Server"""
# adapted from https://gist.github.com/nitaku/10d0662536f37a087e1b
import logging
import json
import signal
import sys
# import os
# import time
# import threading
# import traceback
import urllib
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import coloredlogs
import redis


HTTP_PORT  = 9000
REDIS_PORT = 6379
ALLOW_FRONTEND_DOMAINS = [
    "http://localhost:" + str(HTTP_PORT),
    "http://localhost:3000",
    "http://ttb-pot8o.github.io/potato-id"
]


class Server(BaseHTTPRequestHandler):
    '''
        Base class for handling HTTP requests -- the core of the server.
    '''

    protocol_version = "HTTP/1.1"

    def enable_dynamic_cors(self):
        '''
            Arguments:  none
            Returns:    None
            Throws:     KeyError if the remote end never sent an Origin header.
            Effects:    Sends to the remote end a dynamically generated ACAO
                        header or none at all.

            A trick needed to allow CORS from multiple, but not just any, other
            domains.

            The Access-Control-Allow-Origin header can only have one domain as
            its value, so we test if the remote origin is allowed instead, and
            send it back as the ACAO value.

            If the remote origin isn't allowed, no ACAO header is sent, and
            we assume the client implementation will enforce the same-origin
            policy in that case (it's okay if this assumption falls through).
        '''
        http_origin = self.headers["origin"]
        print(http_origin)
        if http_origin in ALLOW_FRONTEND_DOMAINS:
            self.send_header("Access-Control-Allow-Origin", http_origin)

    def write_str(self, data):
        '''
            Arguments:  data (a string or other string-like that can be cast to
                        bytes)
            Returns:    None
            Throws:     TypeError if data cannot be encoded to bytes() with
                        UTF8
            Effects:    Modifies self.wfile by writing bytes there.

            Shorthand for writing a string back to the remote end.
        '''
        logger.debug("Response: " + str(data))
        self.wfile.write(bytes(data, "utf-8"))

    def write_json(self, obj):
        '''
            Arguments:  obj (a dict)
            Returns:    None
            Throws:     json.dumps throws TypeError if the provided argument
                        is not serialisable to JSON, and anything thrown by
                        self.write_str
            Effects:    inherited

            Take (probably) a Python dictionary and write it to the remote end
                as JSON.

        '''
        self.write_str(json.dumps(obj, indent=2))

    def write_json_error(self, err, expl=""):
        '''
            Arguments:  err (an object) and expl (an object)
            Returns:    None
            Throws:     inherited
            Effects:    inherited

            Take an error descriptor (a string, or other JSON-serialisable
                object like a number or another dict) and an optional
                explanation, and write them as a JSON object to the remote end.
        '''

        self.write_json( {"error": err, "explanation": expl} )

    def set_headers(self, resp, headers=(), msg=None, close=True, csop=False):
        '''
            Arguments:  resp (an int), headers (a tuple<tuple<string,
                        string>>), msg (a string), close (a bool), csop
                        (a bool)
            Returns:    None
            Throws:     inherited
                        its own exceptions)
            Effects:    Sends headers to the remote end, and calls
                        self.end_headers, meaning that no more headers can be
                        sent.

            Sends the appropriate headers given an HTTP response code.
            Also sends any headers specified in the headers argument.
            If `headers` evaluates to False, a "Content-Type: application/json"
                header is sent. Otherwise, the Content-Type is expected to be
                present in `headers`.
            An alternate message can be specified, so that instead of "200 OK",
                "200 Hello" could be sent instead.
            If close is True, its default value, the header "Connection: Close"
                is sent. Otherwise, if close evaluates to False, "Connection:
                keep-alive" is sent. This is not recommended.
            If csop is True, Access-Control-Allow-Origin is set to *, allowing
                requests from anywhere.

            If called with 200 as the first argument, the following headers are
                sent:

            HTTP/1.1 200 OK
            Server: BaseHTTP/0.6 Python/3.5.3
            Date: Fri, 19 May 2017 12:14:12 GMT
            Content-Type: application/json
            Access-Control-Allow-Origin: <client origin or omitted>
            Access-Control-Allow-Methods: HEAD,GET,POST,OPTIONS
            Accept: application/json
            Connection: Close
        '''
        self.send_response(resp, message=msg)

        if not headers:
            self.send_header("Content-Type", "application/json")

        else:
            for h in headers:
                self.send_header(*h)

        if csop:
            self.send_header("Access-Control-Allow-Origin", "*")
        else:
            self.enable_dynamic_cors()

        self.send_header("Connection", ["keep-alive", "Close"][close] )

        self.send_header(
            "Access-Control-Allow-Methods",
            "HEAD,GET,OPTIONS"
        )
        # self.send_header("Accept", "application/json")

        # force HSTS
        self.send_header("Strict-Transport-Security", "max-age=31536000")

        self.end_headers()

    def do_HEAD(self):
        '''
            Arguments:  none
            Returns:    None
            Throws:     inherited
            Effects:    inherited

            Reply to an HTTP HEAD request, sending the default headers.
        '''
        self.set_headers(200)

    # handle GET, reply unsupported
    def do_GET(self):
        '''
            Arguments:  none
            Returns:    None
            Throws:     inherited
            Effects:    inherited

            Reply to an HTTP GET request, probably with 404 or 405.

            As yet undocumented: SOP Buster is a workaround for the Same Origin
                Policy
        '''
        url  = urllib.parse.urlparse(self.path)
        endpoint = url.path[1:]

        if endpoint == "favicon.ico":
            self.set_headers(200, headers=(["Content-Type", "image/x-icon"],))
            with open("favicon.ico", "rb") as icon:
                self.wfile.write(icon.read())

        elif endpoint == "data":
            self.set_headers(
                200,
                headers=(["Content-Type", "application/json"],)
            )

            with open("data/test.json", "r") as j:
                self.write_str(j.read())

        else:
            self.set_headers(404)
            self.write_json_error(f"GET /{endpoint}: 404 Not Found")

    def do_OPTIONS(self):
        '''
        Arguments:  none
        Returns:    None
        Throws:     inherited
        Effects:    inherited

        Reply to an HTTP OPTIONS request.

        Browsers use the OPTIONS method as a 'preflight check' on
            XMLHttpRequest POST calls, to determine which headers are sent and
            to tell whether making such a request would violate the same-origin
            policy.
        '''
        self.set_headers(
            200,
            headers=(
                (
                    "Access-Control-Allow-Headers",
                    "Content-Type, Access-Control-Allow-Headers, Origin, "
                    + "Content-Length, Date, X-Unix-Epoch, Host, Connection"
                ),
            )
        )


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


def run(
        server_class=ThreadedHTTPServer,
        handler_class=Server,
        http_port=HTTP_PORT,
        redis_port=REDIS_PORT):  # api_helper.LOCAL_PORT

    http_address = ("", http_port)
    httpd = server_class(http_address, handler_class)

    redisd = redis.Redis(host='localhost', port=redis_port, db=0)

    logger.info("Starting HTTP on port {}...".format(http_port))


    httpd.serve_forever()


def main():
    from sys import argv

    logger.info("=== STARTING ===")

    if len(argv) == 2:
        run(http_port=int(argv[1]))
    else:
        run()


def sigterm_handler(signo, stack_frame):
    print()
    logger.critical("it's all over")
    # json_helper.kill_all_threads()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)
    coloredlogs.install(
        level="NOTSET",
        fmt="%(name)s[%(process)d] %(levelname)s %(message)s"
    )
    logger = logging.getLogger("server")
    try:
        main()
    finally:
        logger.critical("=== SHUTTING DOWN ===")
