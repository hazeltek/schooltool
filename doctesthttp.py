#!/usr/bin/env python2.3
"""
Run a functional doctest with real HTTP calls.
"""

import sys
import unittest
import httplib
import rfc822
import re
import urllib
import readline
import Cookie
from StringIO import StringIO

sys.path.insert(0, 'Zope3/src')

from zope.testing import doctest


class HTTPCaller(object):
    """Execute an HTTP request directly."""

    host = 'localhost'
    port = 8080

    def __init__(self):
        self.cookies = Cookie.SimpleCookie()

    def __call__(self, request_string, handle_errors=True):
        response = make_http_request(self.host, self.port, request_string,
                                     self.cookies)
        for header in response.response.msg.headers:
            h, v = split_header(header)
            if h.lower() == 'set-cookie':
                self.cookies.load(v)
        return response


headerre = re.compile(r'(\S+): (.+)$')
def split_header(header):
    return headerre.match(header).group(1, 2)


def make_http_request(host, port, request_string, cookies):
    """Make a HTTP request and return the response as a string."""
    # Discard leading white space to make call layout simpler
    request_string = request_string.lstrip()

    # split off and parse the command line
    l = request_string.find('\n')
    command_line = request_string[:l].rstrip()
    request_string = request_string[l+1:]
    method, path, protocol = command_line.split()
    path = urllib.unquote(path)

    instream = StringIO(request_string)
    headers = []
    for header in rfc822.Message(instream).headers:
        h, v = split_header(header)
        if h.lower() == 'content-length':
            continue
        if h.lower() == 'authorization' and v.startswith('Basic '):
            v = 'Basic ' + v[len('Basic '):].encode('base64').strip()
        headers.append((h, v))
    for header in cookies.output(header="Cookie:").splitlines():
        h, v = split_header(header)
        headers.append((h, v))
    body = instream.read().rstrip()
    if body:
        headers.append(('Content-Length', str(len(body))))

    connection = httplib.HTTPConnection(host, port)
    connection.putrequest(method, path, skip_host=1)
    connection.putheader('Host', 'localhost')
    for h, v in headers:
        connection.putheader(h, v)
    connection.endheaders()
    if body:
        connection.send(body)
    response = connection.getresponse()
    body = response.read()
    return ResponseWrapper(response, body)


class ResponseWrapper(object):

    omit_headers = ('x-content-type-warning', 'x-powered-by', 'date', 'server',
                    'set-cookie')

    def __init__(self, response, body):
        self.response = response
        self.body = body

    def getStatus(self):
        return self.response.status

    def getBody(self):
        return self.body

    def getHeader(self, name, default=None):
        return self.response.getheader(name, default)

    def __str__(self):
        version = {9: 'HTTP/0.9', 10: 'HTTP/1.0', 11: 'HTTP/1.1'}[self.response.version]
        status = '%s %s %s' % (version, self.response.status, self.response.reason)
        headers = []
        for header in self.response.msg.headers:
            h, v = split_header(header)
            if h.lower() in self.omit_headers:
                continue
            h = '-'.join([s.capitalize() for s in h.split('-')])
            headers.append('%s: %s' % (h, v.rstrip()))
        headers.sort()
        head = '\n'.join([status] + headers) + '\n'
        if self.body:
            return head + '\n' + self.body
        else:
            return head


def FunctionalDocFileSuite(*paths, **kw):
    globs = kw.setdefault('globs', {})
    globs['http'] = HTTPCaller()
    if 'optionflags' not in kw:
        kw['optionflags'] = (doctest.ELLIPSIS
                             | doctest.REPORT_NDIFF
                             | doctest.NORMALIZE_WHITESPACE)
    return doctest.DocFileSuite(*paths, **kw)


def main(argv=sys.argv):
    try:
        args = argv[1:]
        had_args = bool(args)
        print "Try src/schoolbell/app/browser/ftests/app.txt"
        while True:
            if args:
                filename = args.pop(0)
            elif had_args:
                break
            else:
                filename = raw_input("fdoctest file name> ")
            if not filename or filename == "help":
                print "Please enter a file name, or 'pdb' to start a pdb session"
                print "Hit ^C or ^D to quit."
                continue
            if filename == 'pdb':
                import pdb; pdb.set_trace()
            else:
                try:
                    suite = FunctionalDocFileSuite(filename,
                                optionflags=(doctest.ELLIPSIS |
                                             doctest.REPORT_NDIFF |
                                             doctest.REPORT_ONLY_FIRST_FAILURE |
                                             doctest.NORMALIZE_WHITESPACE))
                    unittest.TextTestRunner().run(suite)
                except Exception, e:
                    import traceback
                    traceback.print_exc()
    except (KeyboardInterrupt, EOFError):
        print "Bye!"

if __name__ == '__main__':
    main()
