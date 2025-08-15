# Author: Kaden Daya <kaden.daya@icloud.com>
# Part of the betanet project by Raden Dev Team

import socket
import ssl

class client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.error = None
        self.socket = None
        
        try:
            self.context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            self.context.check_hostname = False
            self.context.verify_mode = ssl.CERT_NONE
            self.context.minimum_version = ssl.TLSVersion.TLSv1_3
            self.context.maximum_version = ssl.TLSVersion.TLSv1_3
            
            self.context.set_alpn_protocols(['h2', 'http/1.1'])
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = self.context.wrap_socket(self.socket, server_hostname=self.host)
        except ssl.SSLError as e:
            self.error = f"SSL context creation error: {e}"
            return
        except Exception as e:
            self.error = f"Client initialization error: {e}"
            return

    def connect(self):
        if self.error:
            return False, self.error
            
        try:
            self.socket.connect((self.host, self.port))
            return True, f"Connected to {self.host}:{self.port}"
        except ConnectionRefusedError:
            return False, f"Connection refused to {self.host}:{self.port} - server may not be running"
        except ssl.SSLError as e:
            return False, f"SSL/TLS error during connection: {e}"
        except socket.error as e:
            return False, f"Socket error during connection: {e}"
        except Exception as e:
            return False, f"Unexpected error during connection: {e}"

    def send(self, data):
        if self.error:
            return False, self.error
            
        try:
            if isinstance(data, str):
                return False, "Data must be bytes"
            self.socket.sendall(len(data).to_bytes(4, 'big') + data)
            return True, "Data sent successfully"
        except BrokenPipeError:
            return False, "Connection broken - cannot send data"
        except ConnectionResetError:
            return False, "Connection reset - cannot send data"
        except ssl.SSLError as e:
            return False, f"SSL/TLS error during send: {e}"
        except socket.error as e:
            return False, f"Socket error during send: {e}"
        except Exception as e:
            return False, f"Unexpected error during send: {e}"

    def receive(self):
        if self.error:
            return False, self.error
        try:
            hdr = bytearray()
            while len(hdr) < 4:
                chunk = self.socket.recv(4 - len(hdr))
                if not chunk:
                    return False, "Connection closed while reading length"
                hdr.extend(chunk)
            length = int.from_bytes(hdr, 'big')

            buf = bytearray()
            while len(buf) < length:
                chunk = self.socket.recv(length - len(buf))
                if not chunk:
                    return False, "Connection closed while reading payload"
                buf.extend(chunk)

            return True, bytes(buf)
        except ConnectionResetError:
            return False, "Connection reset by server"
        except ssl.SSLError as e:
            return False, f"SSL/TLS error during receive: {e}"
        except socket.error as e:
            return False, f"Socket error during receive: {e}"
        except Exception as e:
            return False, f"Unexpected error during receive: {e}"

    def close(self):
        if self.socket:
            try:
                self.socket.close()
                return True, "Client connection closed"
            except Exception as e:
                return False, f"Error closing client: {e}"
        return True, "No connection to close"

class server:
    def __init__(self, host, port, certfile, keyfile):
        self.host = host
        self.port = port
        self.error = None
        self.socket = None
        self.conn = None
        self.addr = None
        
        try:
            self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.context.load_cert_chain(certfile=certfile, keyfile=keyfile)
            self.context.minimum_version = ssl.TLSVersion.TLSv1_3
            self.context.maximum_version = ssl.TLSVersion.TLSv1_3
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = self.context.wrap_socket(self.socket, server_side=True)
            self.socket.bind((self.host, self.port))
        except FileNotFoundError as e:
            self.error = f"Certificate or key file not found: {e}"
            return
        except ssl.SSLError as e:
            self.error = f"SSL context creation error: {e}"
            return
        except PermissionError:
            self.error = f"Permission denied binding to {self.host}:{self.port}"
            return
        except socket.error as e:
            self.error = f"Socket error during server initialization: {e}"
            return
        except Exception as e:
            self.error = f"Server initialization error: {e}"
            return

    def start(self):
        if self.error:
            return False, self.error
            
        try:
            self.socket.listen(1)
            return True, f"Server is listening on {self.host}:{self.port}"
        except socket.error as e:
            return False, f"Socket error starting server: {e}"
        except ssl.SSLError as e:
            return False, f"SSL/TLS error starting server: {e}"
        except Exception as e:
            return False, f"Unexpected error starting server: {e}"

    def stop(self):
        if self.socket:
            try:
                self.socket.close()
                return True, "Server stopped"
            except Exception as e:
                return False, f"Error stopping server: {e}"
        return True, "No server to stop"

    def accept(self):
        if self.error:
            return False, self.error
            
        try:
            self.conn, self.addr = self.socket.accept()
            return True, f"Connected by {self.addr}", [self.conn, self.addr]
        except socket.error as e:
            return False, f"Socket error accepting connection: {e}"
        except ssl.SSLError as e:
            return False, f"SSL/TLS error accepting connection: {e}"
        except Exception as e:
            return False, f"Unexpected error accepting connection: {e}"

    def send(self, data):
        if self.error or not self.conn:
            return False, "No active connection"
        try:
            self.conn.sendall(len(data).to_bytes(4, 'big') + data)
            return True, "Data sent successfully"
        except BrokenPipeError:
            return False, "Connection broken - cannot send data"
        except ConnectionResetError:
            return False, "Connection reset - cannot send data"
        except ssl.SSLError as e:
            return False, f"SSL/TLS error during send: {e}"
        except socket.error as e:
            return False, f"Socket error during send: {e}"
        except Exception as e:
            return False, f"Unexpected error during send: {e}"

    def receive(self):
        if self.error or not self.conn:
            return False, "No active connection"
            
        try:
            hdr = bytearray()
            while len(hdr) < 4:
                chunk = self.conn.recv(4 - len(hdr))
                if not chunk:
                    return False, "Connection closed while reading length"
                hdr.extend(chunk)
            length = int.from_bytes(hdr, 'big')

            # Read payload
            buf = bytearray()
            while len(buf) < length:
                chunk = self.conn.recv(length - len(buf))
                if not chunk:
                    return False, "Connection closed while reading payload"
                buf.extend(chunk)

            return True, bytes(buf)
        except ConnectionResetError:
            return False, "Connection reset by client"
        except ssl.SSLError as e:
            return False, f"SSL/TLS error during receive: {e}"
        except socket.error as e:
            return False, f"Socket error during receive: {e}"
        except Exception as e:
            return False, f"Unexpected error during receive: {e}"

    def close(self):
        if self.conn:
            try:
                self.conn.close()
                self.conn = None
                self.addr = None
                return True, "Client connection closed"
            except Exception as e:
                return False, f"Error closing client connection: {e}"
        return True, "No client connection to close"