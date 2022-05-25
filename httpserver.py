

import os
from bottle import TEMPLATE_PATH, route, run, template, redirect, request, response, abort, static_file
import threading
import json

import log
import phonestate
import sounds
import play

# This is unfinished, but should work if you uncomment the import line in magicphone.py and add some useful web stuff
# The templates and static files are at ./httpserver/

TEMPLATE_PATH.append('./httpserver/')

@route('/')
def index():

    return template('root')


@route('/<filename:re:.*\.js>')
def send_js(filename):
    return static_file(filename, root='./httpserver/', mimetype='application/javascript')
@route('/<filename:re:.*\.ico>')
def send_ico(filename):
    return static_file(filename, root='./httpserver/', mimetype='image/x-icon')
@route('/<filename:re:.*\.css>')
def send_css(filename):
    return static_file(filename, root='./httpserver/', mimetype='text/css')


# run(host='0.0.0.0', port=80, debug=True)
# run the server in a thread, otherwise it blocks here and prevents everything else from happening
threading.Thread(target=run, daemon=True, kwargs=dict(host='0.0.0.0', port=80)).start()
