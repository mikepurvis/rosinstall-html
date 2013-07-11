#!/usr/bin/env python

import requests, yaml, re, argparse
from mako.template import Template
from mako.lookup import TemplateLookup
from collections import OrderedDict
from os import path

TMPL_DIR = path.join(path.dirname(path.realpath(__file__)), "tmpl")
lookup = TemplateLookup(directories=[TMPL_DIR])

# Example:
# ./render.py public:https://raw.github.com/clearpathrobotics/kingfisher/master/kingfisher_base.rosinstall --output test.html --base http://localhost/rosinstall/

class RepoUri(object):
  re = re.compile("(.*)")
  has_pic = False

  def __init__(self, uri):
    match = self.re.match(uri)
    if not match:
      raise ValueError()
    self.groups = match.groups
  def src_uri(self, version): return self.uri
  def repo_uri(self): return self.uri 

class GithubUri(RepoUri):
  re = re.compile("(.*)(github\.com)(.*)\.git")
  has_pic = True
  pic_uri = "static/github.png"
  def src_uri(self, version):
    if version:
      return "".join(self.groups()) + "/tree/%s" % version
    else:
      return "".join(self.groups())

class BitbucketUri(RepoUri):
  re = re.compile("(.*)(bitbucket\.org)(.*)\.git")
  has_pic = True
  pic_uri = "static/bitbucket.png"
  def src_uri(self, version):
    if version:
      return "".join(self.groups()) + "/src?at=%s" % version
    else:
      return "".join(self.groups()) + "/src"

def uri_object(uri):
  classes = [BitbucketUri, GithubUri, RepoUri]
  for cls in classes:
    try:
      return cls(uri)
    except ValueError:
      pass
  raise ValueError("No match found for %s" % uri)


class RepoBranch(object):
  def __init__(self, fields):
    self.uri = uri_object(fields['uri'])
    self.version = fields.get('version', None)


def do_render(configs, auth, template_name, base_url):
  entries = OrderedDict()

  for name, url in configs:
    r = requests.get(url, auth=auth)
    if "<html" in r.text:
      print "Error fetching file: %s" % url
      print "Check location and whether authorization is necessary."
      exit(1)

    for entry in yaml.load(r.text):
      scm = entry.keys()[0]
      if scm in ('other', 'setup-file'):
        continue
      fields = entry[scm]

      if 'local-name' in fields:
        entries.setdefault(fields['local-name'], {})[name] = RepoBranch(fields)

  return lookup.get_template(template_name).render(configs=configs, entries=entries, base_url=base_url)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Create an HTML table of one or more rosinstall files.')
  parser.add_argument('rosinstalls', metavar='NAME:ROSINSTALL_URL', type=str, nargs='+',
                      help='name and rosinstall url pairs as input.')
  parser.add_argument('--auth', metavar='USER:PASS', type=str,
                      help='Credentials for authorized HTTP requests.')
  parser.add_argument('--template', metavar='TMPL', type=str, default="standalone.html",
                      help='Template to render table against.')
  parser.add_argument('--base', metavar='URL', type=str, default="",
                      help='Base URL to use for images and links, default is relative.')
  parser.add_argument('--output', metavar='FILE', type=str,
                      help='Where to write output (default is stdout)')
  args = parser.parse_args()

  configs = []
  for pair in args.rosinstalls:
    try:
      name, url = pair.split(":", 1)
      configs.append((name, url))
    except ValueError:
      print "Problem with argument: %s" % pair
      print "Missing colon to separate name from url?"
      exit(1)

  auth = None
  if args.auth:
    auth = tuple(args.auth.split(":"))

  output = do_render(configs, auth, args.template, args.base)

  if args.output:
    with open(args.output, 'w') as f:
      f.write(output)
  else:
    print output
