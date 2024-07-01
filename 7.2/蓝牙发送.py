
import bluetooth

def send_35(message):#这是35车才用的代码，35车作为发送端
    server_addr = "E4:5F:01:90:EA:51"
    port = 1

    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((server_addr, port))

    try:
        sock.send(message)
    finally:
        sock.close()

# 使用示例
send_35("这是要发送的信息")


def send_36(message):#这是36车才用的代码，36车作为发送端
    server_addr = "E4:5F:01:8C:EF:B2"
    port = 1

    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((server_addr, port))

    try:
        sock.send(message)
    finally:
        sock.close()

# 使用示例
send_36("这是要发送的信息")



def listen():
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    port = 1
    server_sock.bind(("", port))
    server_sock.listen(1)

    print("等待蓝牙连接...")
    client_sock, address = server_sock.accept()
    print("接受到来自 {} 的连接".format(address))

    try:
        while True:
            data = client_sock.recv(1024)
            if not data:
                break
            received_message = data.decode("utf-8")
            print("接收到数据: {}".format(received_message))
            if received_message.strip() == "go":
                print("收到 'go' 信号，结束接收。")
                break
    finally:
        client_sock.close()
        server_sock.close()
        print("连接已关闭")

# 调用函数开始接收蓝牙信号
listen()

# 函数执行完毕后，可以继续执行后续程序
print("继续执行后续程序...")