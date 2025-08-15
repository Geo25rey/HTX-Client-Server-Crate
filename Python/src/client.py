# TEST FILE
# just use this to test the client
# Authors: Kaden Daya <kaden.daya@icloud.com>

from noiseXK import NoiseClient

server_key = 'e128b23273f25fe97ea6e7440179c27046baddcd9b6bbac5160ae27c826ee464'
print("Server Public Key: ", server_key)

client = NoiseClient('127.0.0.1', 443, bytes.fromhex(server_key)) # * Just copy and paste pub key from server output for testing

client.connect()

client.send(input("Enter message: ").encode())
print(client.receive())