import aiohttp
import asyncio
import async_timeout


def splitIp(victims, whiteList=[]):
    '''支持 1.1.1-100.1-100 和 1.1.1-233.1-2, 1.1.1.1 这种表达方式'''
    result = set()
    if len(victims.split(',')) != 1:
        for i in victims.split(','):
            result = result.union(splitIp(i.strip(), whiteList))
        return result

    parts = victims.split(".")
    assert len(parts) == 4
    for part in parts: # 以 . 分割成 4 部分
        tmp = set()
        if part.find('-') == -1: # 观察是否为 ip 段
            if len(result) != 0: # 是否是第一部分, 如果是第一部分, 直接加入到列表中
                for ip in result:
                    tmp.add(f"{ip}.{part}")
            else:
                tmp.add(part)
        else:
            if len(result) != 0:
                for ip in result:
                    f, b = part.split('-')[0], part.split('-')[1]
                    tmp = tmp.union([f"{ip}.{j}" for j in range(int(f), int(b) + 1)])
            else:
                f, b = part.split('-')[0], part.split('-')[1]
                tmp = tmp.union([str(j) for j in range(int(f), int(b) + 1)])
        result = tmp

    for i in whiteList:
        result.remove(i)
    return result


class attackChain():
    chain = []
    

    def fixRoute(self, route):
        if route[0] != "/":
            route = "/" + route
        return route

    
    def addGET(self, route, reqResult=True, cookies={}, headers={}, timeout=10, schema="http://"):
        self.chain.append({
            "method": "GET",
            "route": self.fixRoute(route),
            "reqResult": reqResult,
            "schema": schema,
            "cookies": cookies,
            "headers": headers,
            "timeout": timeout,
        })
        
    
    def addPOST(self, route, data={}, reqResult=True, cookies={}, headers={}, timeout=10, schema="http://",):
        '''file use
        ```
        data = {'file': open('/etc/passwd', 'rb')}
        ```  
        or 
        ```
        {'file': ('filename.xls', open('report.xls', 'rb'), 'application/vnd.ms-excel'}
        ```  
        json use
        ```
        data = json.dumps(data)
        ```'''
        self.chain.append({
            "method": "POST",
            "route": self.fixRoute(route),
            "data": data,
            "reqResult": reqResult,
            "schema": schema,
            "cookies": cookies,
            "headers": headers,
            "timeout": timeout,
        })
    

    async def perform(self, host):
        jar = aiohttp.CookieJar(unsafe=True)
        sess = aiohttp.ClientSession(cookie_jar=jar)
        result = []
        for i in self.chain:
            try:
                async with async_timeout.timeout(i["timeout"]):
                    sess._cookie_jar.update_cookies(i["cookies"])
                    if i["method"] == "POST":
                        res = await sess.post(f"{i['schema']}{host}{i['route']}", data=i['data'], headers=i["headers"])
                    elif i["method"] == "GET":
                        res = await sess.get(f"{i['schema']}{host}{i['route']}", headers=i["headers"])
                    else:
                        raise Exception("Unsupported method")
                    if i["reqResult"]:
                        result.append(await res.text())
            except asyncio.TimeoutError:
                result.append(f"Time out in action {i}")            
        await sess.close()
        return {"host": host, "result": result}


    def attack(self, victims):
        '''各个 host 之间是并发的, chian 里面的请求是按顺序执行  
        eg.
        ```
        chain = attackChain()  
        chain.addGET("/?key=value", True, cookies={"key":"value"}, headers={"User-Agent": "curl"})
        chain.addPOST("/?key=value", {"key": "value"}, True, cookies={"key":"value"}, headers={"User-Agent": "curl"})
        chain.attack(splitIp("127.0.0.1-100"))
        ```
        将会对所有 `victims` 按顺序执行 GET, POST
        '''
        if type(victims) != type([]):
            raise Exception("victims need a list object")
        loop = asyncio.get_event_loop()
        tasks = []
        results = []
        for i in victims:
            t = asyncio.ensure_future(self.perform(i))
            tasks.append(t)
            loop.run_until_complete(asyncio.wait(tasks))
        for i in tasks:
            results.append(i.result())
        return results
