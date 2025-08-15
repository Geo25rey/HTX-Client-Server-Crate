# TEST FILE
# just use this to test the server
# Authors: Kaden Daya <kaden.daya@icloud.com>

from noiseXK import NoiseServer, gen_x25519_keypair

keypair = gen_x25519_keypair()
print(f"""
Server Public Key: {keypair[1].hex()}
Server Private Key: {keypair[0].hex()}
""")

server = NoiseServer('127.0.0.1', 443, keypair[1], keypair[0])
server.perform_handshake()

server.send(input("Enter message: ").encode())
print(server.receive())