import json
from os.path import realpath, join, dirname

BASE_PATH = dirname(realpath(__file__))

def x(s):
    return join(BASE_PATH, s)

hyperlocal_sites = json.load(open(x('hyperlocal_sites.json')))

