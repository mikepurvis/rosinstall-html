#!/usr/bin/python
from flask import Flask, request, url_for
from render import do_render
import argparse
app = Flask(__name__)

parser = argparse.ArgumentParser(description='Server to create an HTML table of one or more rosinstall files.')
parser.add_argument('--auth', metavar='USER:PASS', type=str,
                    help='Credentials for authorized HTTP requests.')
parser.add_argument('--host', metavar='IP', type=str, default="0.0.0.0",
                    help='IP address to listen on.')
parser.add_argument('--port', metavar='PORT', type=int, default=5000,
                    help='Port to listen on.')
args = parser.parse_args()


@app.route("/")
def show():
  configs = []
  for pair in request.args.get('rosinstalls', '').split(','):
    try:
      name, url = pair.split(":", 1)
      if not name or not url:
        raise ValueError
      configs.append((name, url))
    except ValueError:
      return "Problem with argument: [%s]" % pair

  auth = request.args.get('auth', args.auth)
  if auth:
    auth = tuple(auth.split(":"))

  template = request.args.get('template', 'standalone.html')

  base = request.args.get('base', url_for('show', _external=True)) 

  #return "Hello World! %s foo" % request.args.get('foo', "baz")
  output = do_render(configs, auth, template, base)
  return output

if __name__ == "__main__":
  #app.debug = True
  app.run(host=args.host, port=args.port)
