#!/usr/bin/env python

"""
//  -------------------------------------------------------------
//  author        Giga
//  project       qeeqbox/raven
//  email         gigaqeeq@gmail.com
//  description   asyncio, websockets and http
//  licensee      AGPL-3.0
//  -------------------------------------------------------------
//  contributors list qeeqbox/raven/graphs/contributors
//  ----
"""


from http import HTTPStatus
from mimetypes import guess_type
from urllib.parse import urljoin, urlparse
from os import path, getcwd
from contextlib import suppress
from asyncio import sleep as asleep
from asyncio import run as arun
from asyncio import gather
from websockets import serve
from json import dumps
from sys import argv
from random import randint, uniform, choice

IP = '0.0.0.0'
WEBSOCKET_PORT = 5678
HTTP_PORT = 8080
WEBSOCKETS = set()
dummy_countries=["us","cn","br","fr","gb","mx","in","ca","au","jp","dr","ru"]
dummy_coordinates=["30.57, 118.75", "36.53, 139.52","55.17, 35.02","36.17, 128.72","40.16, 127.22",
                  "-34.17, 150.72","20.92, 77.72","32.16, 76.20","23.72, 120.82","30.92, 14.89",
                  "23.66, 54.09","25.66, 47.09","35.66, 52.29","35.78, 69.69","20.97, 106.04",
                  "-24.69, 28.54","29.80, 30.53","31.80, 34.98","33.80, 36.98","39.30, 34.38",
                  "49.30, 30.38","54.30, 27.38","64.30, 27.37","52.30, 19.38","49.60, 16.08",
                  "48.10, 14.08","40.10, 16.43","52.10, 12.43","51.42, -1.20","58.52, 16.20",
                  "48.10, 1.0","40.10, -4.98","33.13, 43.65","15.12, 45.25","4.12, 46.64",
                  "15.12, 30.64","-3.12, 16.64","23.12, -80.79","26.12, -81.09","33.12, -83.09",
                  "38.12, -77.09","40.12, -74.67","47.12, -73.42","44.12, -79.42","44.12, -89.42",
                  "30.12, -90.42","30.12, -95.42","40.12, -110.42","39.22, -123.42","46.22, -123.02",
                  "20.22, -101.02","17.22, -90.02","9.22, -67.02","-25.22, -48.86","-40.22, -65.86"]
test_coordinates=["30.57, 118.75","-40.22, -65.86"]
 
def dummy_ip():
    return (".".join("{}".format(choice([i for i in range(0,255) if i not in [10,127,172,192]])) for x in range(4)))

def dummy_request_ip(loop, function=""):
  # note that this just makes a bunch of fake IPs and querys them. makes slightly more believable data.
  # don't use it unless you want to run up the API limit!
    ret = []
    for index in range(loop):
      ip1 = dummy_ip()
      ip2 = dummy_ip()
      ret.append(attack_request(ip1, ip2, function))
    return dumps(ret)

def dummy_request_geocoordinates(loop, function=""):
    ret = []
    for index in range(loop):
      geocoordinates = dummy_coordinates
      ip1 = choice(geocoordinates)
      while True:
        ip2 = choice(geocoordinates)
        if ip1 != ip2:
          break
      ret.append(attack_request(ip1, ip2, function))
    return dumps(ret)

def dummy_request(loop, function=""):
    ret = []
    for index in range(loop):
        parameters = {
    "function":function,
      "object": {
        "from": "{},{}".format(uniform(-90, 90), uniform(-180,180)),
        "to": "{},{}".format(uniform(-90, 90), uniform(-180,180))
      },
      "color": {
        "line": {
          "from": "#{:06x}".format(randint(255, 16777216)),
          "to": "#{:06x}".format(randint(255, 16777216))
        }
      },
      "timeout": 2000,
      "options": [
        "line",
        "multi-output",
        "country-by-coordinate"
      ]
    }

        ret.append(parameters)
    return dumps(ret)

# locations must be in the format "x.xx, y.yy". (specificity varies)
def attack_request(from_loc: str, to_loc: str, function=""):
    parameters = {
    "function":function,
      "object": {
        "from": from_loc,
        "to": to_loc
      },
      "color": {
        "line": {
          "from": "#{:06x}".format(randint(255, 16777216)),
          "to": "#{:06x}".format(randint(255, 16777216))
        }
      },
      "timeout": 2000,
      "options": [
        "line",
        "multi-output",
        "country-by-coordinate"
      ]
    }
    return parameters

def check_path(_path):
    with suppress(Exception):
        _path = path.relpath(_path, start=getcwd())
        _path = path.abspath(_path)
        if not any(detect in _path for detect in ['\\..','/..','..']):
            if _path.startswith(getcwd()):
                if path.isfile(_path):
                    return True
    return False

async def http_task(path, headers):
    response_content = ''
    response_status = HTTPStatus.NOT_FOUND
    response_headers = [('Connection', 'close')]
    if 'User-Agent' in headers and 'Host' in headers:
        print("Host: {} User-Agent: {}".format(headers['Host'],headers['User-Agent']))
    if 'Accept' in headers:
        with suppress(Exception):
            if path == '/':
                path = getcwd()+'/index.html'
            else:
                path = getcwd()+urljoin(path, urlparse(path).path)
            if check_path(path):
                mime_type = guess_type(path)[0]
                if mime_type in ['text/html','application/javascript','text/css']:
                    if mime_type in headers['Accept'] or '*/*' in headers['Accept']:
                        response_content = open(path, 'rb').read()      # <---- switch to aiofile 
                        response_headers.append(('Content-Type', mime_type))
                        response_headers.append(('Content-Length', str(len(response_content))))
                        response_status = HTTPStatus.OK
                    else:
                        print("Mismatch {} type {} with {}".format(path,mime_type, headers['Accept']))
                else:
                    print("File is not supported {} type {}".format(path,mime_type))
            else:
                print("File is not supported or does not exist {}".format(path))
    else:
        print("Needs [Accept] from server")
    return response_status, response_headers, response_content


async def websoket_task(websocket, path):
    WEBSOCKETS.add(websocket)
    try:
        while True:
            data_to_send = None
            try:
                if argv[1] == "table":
                    data_to_send = dummy_request_geocoordinates(5, "table")
            except:
                pass
            if not data_to_send:
                data_to_send = dummy_request_geocoordinates(5, "marker")
            await gather(*[ws.send(data_to_send) for ws in WEBSOCKETS],return_exceptions=False)
            await asleep(randint(1,1))
    except Exception as e:
        pass
    finally:
        WEBSOCKETS.remove(websocket)

async def main():
    await serve(websoket_task, IP, WEBSOCKET_PORT)
    await serve(lambda x: None, IP, HTTP_PORT, process_request=http_task)
    try:
        while True:
            await asleep(0.2)
    except KeyboardInterrupt:
        exit()

arun(main())
