import socket

HOST = '127.0.0.1'
PORT = 443

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(b'Hello Server!')
        data = s.recv(1024)
        print(f"Received data: {data.decode('utf-8')}")

if __name__ == '__main__':
    main()