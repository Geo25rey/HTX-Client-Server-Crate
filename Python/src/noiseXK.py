# Authors: Kaden Daya <kaden.daya@icloud.com>
# Part of the betanet project by Raven dev team

import struct
from typing import Optional, Tuple
from tls import client, server
from noise.connection import NoiseConnection, Keypair
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.serialization import (
    Encoding, PrivateFormat, NoEncryption, PublicFormat
)
from itertools import cycle

def gen_x25519_keypair() -> Tuple[bytes, bytes]:
    sk = x25519.X25519PrivateKey.generate()
    pk = sk.public_key()
    return (
        sk.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()),
        pk.public_bytes(Encoding.Raw, PublicFormat.Raw)
    )

class NoiseClient:
    def __init__(self, host, port, responder_pub):
        self.client = client(host, port)
        print(self.client.connect()[1])
        self.proto = NoiseConnection.from_name(b'Noise_XK_25519_ChaChaPoly_SHA256')
        self.proto.set_as_initiator()
        self.c_priv, self.c_pub = gen_x25519_keypair()
        self.proto.set_keypair_from_private_bytes(Keypair.STATIC, self.c_priv)
        self.proto.set_keypair_from_public_bytes(Keypair.REMOTE_STATIC, responder_pub)
    
    def connect(self):
        self.proto.start_handshake()
        message = self.proto.write_message()
        print(self.client.send(message)[1])

        received = self.client.receive()

        if isinstance(received[1], str):
            data = received[1].encode()
        else:
            data = received[1]

        self.proto.read_message(data)

        if not self.proto.handshake_finished:
            final_message = self.proto.write_message()
            print(f"Client sending final handshake message: {len(final_message)} bytes")
            self.client.send(final_message)

        if self.proto.handshake_finished:
            print("Handshake successful")
        else:
            print("Handshake failed")
        
    def send(self, message):
        encrypted_message = self.proto.encrypt(message)
        self.client.send(encrypted_message)
    
    def receive(self):
        ciphertext = self.client.receive()[1]
        plaintext = self.proto.decrypt(ciphertext)
        return plaintext

class NoiseServer:
    def __init__(self, host, port, s_pub, s_priv):
        self.server = server(host, port, 'cert.pem', 'key.pem')
        self.server.start()
        
        self.conn, self.addr = self.server.accept()[2]

        self.noise = NoiseConnection.from_name(b'Noise_XK_25519_ChaChaPoly_SHA256')
        self.noise.set_as_responder()
        self.noise.set_keypair_from_private_bytes(Keypair.STATIC, s_priv)

    def perform_handshake(self):
        data = self.server.receive()[1]
        print(f"Server received: {len(data)} bytes")
    
        self.noise.start_handshake()
        print(f"Server handshake state after start: {self.noise.handshake_finished}")
    
        self.noise.read_message(data)
        print(f"Server handshake state after reading client: {self.noise.handshake_finished}")
    
        if not self.noise.handshake_finished:
            response = self.noise.write_message()
            print(f"Server sending response: {len(response)} bytes")
            self.server.send(response)
            print(f"Server handshake state after sending: {self.noise.handshake_finished}")
            
            # ADD THIS: Read the client's final handshake message
            final_data = self.server.receive()[1]
            print(f"Server received final message: {len(final_data)} bytes")
            self.noise.read_message(final_data)
            print(f"Server handshake state after reading final: {self.noise.handshake_finished}")

        if self.noise.handshake_finished:
            print("Server handshake complete")
        else:
            print("Server handshake failed")

    def send(self, message):
        self.server.send(self.noise.encrypt(message))

    def receive(self):
        while True:
            data = self.server.receive()[1]
            if not data:
                pass
            else:
                received = self.noise.decrypt(data)
                return received