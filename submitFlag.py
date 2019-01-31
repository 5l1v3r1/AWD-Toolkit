import base64
import json
import re

import requests


def loadRecord(filename, startTime):
    f = open(filename).read()
    flags = []
    for l in f:
        l = json.loads(l)
    if int(l["ts"]) > int(startTime):
        flags.append(l["data"])
    return flags


def loadLines(filename):
    f = open(filename).read()
    f = f.strip("\n")
    f = f.split("\n")
    return f


def regMatchs(regex, strings):
    '''eg. `regMatchs(r"#RANDOM--->([\S\s]*?)<---STRING#", s)`'''
    regex = re.compile(regex)
    result = regex.findall(strings)
    return result


def loadDump(filename, regex):
    dump = open(filename).read()
    dump = json.loads(dump)
    flags = []
    for record in dump:
        history = record["history"]
        flag = regMatchs(regex, history)
        flags.extend(flag)
    return flags


def submit(flags):
    sess = requests.session()
    sess.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36"
    # sess.headers["X-Requested-With"] = "XMLHttpRequest"
    cookies = open('cookies.json').read()
    cookies = json.loads(cookies)
    for cookie in cookies:
        sess.cookies[cookie["name"]] = cookie["value"]
    
    for f in flags:
        res = sess.post("http://127.0.0.1/", data={"flag": f})
    print(res.text)


print(loadDump("dump-1548928339.7051184.json", "#RANDOM#->([\S\s]*?)<-#RANDOM#"))