import socket
import ssl

class client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        self.context.check_hostname = False
        self.context.verify_mode = ssl.CERT_NONE
        self.context.minimum_version = ssl.TLSVersion.TLSv1_3
        self.context.maximum_version = ssl.TLSVersion.TLSv1_3
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = self.context.wrap_socket(self.socket, server_hostname=self.host)

    def connect(self):
        self.socket.connect((self.host, self.port))
        print(f"Connected to {self.host}:{self.port}")

    def send(self, data):
        self.socket.sendall(data.encode('utf-8'))

    def receive(self):
        while True:
            data = self.socket.recv(1024)
            if not data:
                break
            return data

class server:
    def __init__(self, host, port, certfile, keyfile):
        self.host = host
        self.port = port
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        self.context.minimum_version = ssl.TLSVersion.TLSv1_3
        self.context.maximum_version = ssl.TLSVersion.TLSv1_3
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = self.context.wrap_socket(self.socket, server_side=True)
        self.socket.bind((self.host, self.port))

    def start(self):
        self.socket.listen(1)
        print(f"Server is listening on {self.host}:{self.port}")

    def stop(self):
        self.socket.close()
        print(f"Server is stopped")
    

    def accept(self):
        self.conn, self.addr = self.socket.accept()
        print(f"Connected by {self.addr}")

    def send(self, data):
        self.conn.sendall(data.encode('utf-8'))

    def receive(self):
        while True:
            data = self.conn.recv(1024)
            if not data:
                break
            return data

if __name__ == '__main__':
    # Server Testing
    server = server('127.0.0.1', 443, "cert.pem", "key.pem")
    server.start()
    server.accept()
    server.send('Hello Client!')
    data = server.receive()
    print(f"Received data: {data.decode('utf-8')}")
    server.stop()

    # Client Testing
    client = client('127.0.0.1', 443)
    client.connect()
    client.send('Hello Server!')
    data = client.receive()
    print(f"Received data: {data.decode('utf-8')}")