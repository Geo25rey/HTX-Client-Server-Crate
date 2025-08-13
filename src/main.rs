use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::fs::File;
use std::io::BufReader;
use std::sync::Arc;
use rustls::{ServerConfig, ServerConnection};
use rustls_pemfile::{certs, pkcs8_private_keys};

fn load_certificates() -> Result<ServerConfig, Box<dyn std::error::Error>> {
    let cert_file = File::open("cert.pem")?;
    let mut cert_reader = BufReader::new(cert_file);
    let cert_chain: Vec<_> = certs(&mut cert_reader).collect::<Result<_, _>>()?;
    
    let key_file = File::open("key.pem")?;
    let mut key_reader = BufReader::new(key_file);
    let mut keys: Vec<_> = pkcs8_private_keys(&mut key_reader).collect::<Result<_, _>>()?;
    
    if keys.is_empty() {
        return Err("No private keys found".into());
    }
    
    let config = ServerConfig::builder()
        .with_no_client_auth()
        .with_single_cert(cert_chain, rustls::pki_types::PrivateKeyDer::Pkcs8(keys.remove(0)))?;
    
    Ok(config)
}

fn handle_client(mut stream: TcpStream, config: Arc<ServerConfig>) -> Result<(), Box<dyn std::error::Error>> {
    let mut tls_conn = ServerConnection::new(config)?;
    tls_conn.set_buffer_limit(Some(1024));

    let mut tls_stream = rustls::Stream::new(&mut tls_conn, &mut stream);
    
    let mut buffer = [0; 1024];
    let bytes_read = tls_stream.read(&mut buffer)?;
    
    if bytes_read > 0 {
        let request = String::from_utf8_lossy(&buffer[..bytes_read]);
        println!("Encrypted Request Received: {}", request);
        let response = "Hello, Client!".as_bytes();
        tls_stream.write_all(response)?;
        tls_stream.flush()?;
    }
    
    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let config = Arc::new(load_certificates()?);
    println!("TLS certificates loaded successfully");
    
    let listener = TcpListener::bind("127.0.0.1:443")?;
    println!("TLS Server listening for encrypted connections on port 443");

    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                let config = config.clone();
                std::thread::spawn(move || {
                    if let Err(e) = handle_client(stream, config) {
                        eprintln!("TLS connection error: {}", e);
                    }
                });
            }
            Err(e) => {
                eprintln!("Connection error: {}", e);
            }
        }
    }
    
    Ok(())
}