use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};

fn handle_client(mut stream: TcpStream) {
    let mut buffer = [0; 1024];
    stream.read(&mut buffer).expect("Failed to read from the client!");

    let request = String::from_utf8_lossy(&buffer[..]);
    println!("Request Received: {}", request);
    let response = "Hello, Client!".as_bytes();
    stream.write(response).expect("Failed to write to the client!");
}

fn main() {
    let listener = TcpListener::bind("127.0.0.1:443").
    expect("Failed to bind to address");
    println!("Listening for connections on port 443");

    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                std::thread::spawn(|| {
                    handle_client(stream);
                });
            }
            Err(e) => {
                println!("Error: {}", e);
            }
        }
    }
}