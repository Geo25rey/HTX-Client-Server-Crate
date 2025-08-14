import socket
import ssl

HOST = '127.0.0.1'
PORT = 443

context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
context.minimum_version = ssl.TLSVersion.TLSv1_3
context.maximum_version = ssl.TLSVersion.TLSv1_3

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s = context.wrap_socket(s, server_hostname=HOST)
        s.connect((HOST, PORT))
        s.sendall(b'Hello Server!')
        data = s.recv(1024)
        print(f"Received data: {data.decode('utf-8')}")

if __name__ == '__main__':
    main()