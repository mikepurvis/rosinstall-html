#!/usr/bin/env python

from flask import Flask, request, url_for
from render import do_render
import argparse
from datetime import datetime
app = Flask(__name__)

parser = argparse.ArgumentParser(description='Server to create an HTML table of one or more rosinstall files.')
parser.add_argument('--auth', metavar='USER:PASS', type=str,
                    help='Credentials for authorized HTTP requests.')
parser.add_argument('--host', metavar='IP', type=str, default="0.0.0.0",
                    help='IP address to listen on.')
parser.add_argument('--port', metavar='PORT', type=int, default=5000,
                    help='Port to listen on.')
parser.add_argument('--max_cache', metavar='SECS', type=int, default=24*3600,
                    help='Maximum seconds before regenerating.')
args = parser.parse_args()

cache = {}

@app.route("/")
def show():
  if request.url in cache:
    cache_time, output = cache[request.url]
    age = (datetime.now() - cache_time).total_seconds()
    print "Cache age %d seconds for %s" % (age, request.url)
    if age < args.max_cache:
      print "Returning cached output."
      return output
    else:
      print "Regenerating output."
  
  print "Generating new response."
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

  base = request.args.get('base', request.base_url) 
  
  output = do_render(configs, auth, template, base)

  cache[request.url] = (datetime.now(), output)

  return output

if __name__ == "__main__":
  app.debug = True
  app.run(host=args.host, port=args.port)
