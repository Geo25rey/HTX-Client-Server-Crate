import socket
import ssl

HOST = '127.0.0.1'
PORT = 443

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
context.minimum_version = ssl.TLSVersion.TLSv1_3
context.maximum_version = ssl.TLSVersion.TLSv1_3

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s = context.wrap_socket(s, server_side=True)
        s.listen(1)
        print(f"Server is listening on {HOST}:{PORT}")

        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                print(f"Received data: {data.decode('utf-8')}")
                conn.sendall('Hello Client!'.encode('utf-8'))
                print("Sent data: Hello Client!")
                break
        print("Connection closed")
if __name__ == '__main__':
    main()