import os, stat

mem_file_name = 'test.php'
while True:
    try:
        f = open(mem_file_name, "w") # 清空文件
        f.close()
        os.chmod(mem_file_name, 0)  # 设置为 000
    except PermissionError:
        pass