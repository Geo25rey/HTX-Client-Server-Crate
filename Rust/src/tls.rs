// Author: Kaden Daya <kaden.daya@icloud.com>
// Part of the betanet project by Raden Dev Team

use std::fs::File;
use std::io::{BufReader, Read, Write};
use std::net::{TcpStream, TcpListener};
use std::sync::Arc;

use rustls::{ServerConfig, ServerConnection, Stream, ClientConfig, ClientConnection, RootCertStore};
use rustls::pki_types::{PrivateKeyDer, CertificateDer, ServerName};
use rustls_pemfile::{certs, pkcs8_private_keys};

pub struct Client {
    host: String,
    port: u16,
    socket: Option<TcpStream>,
    tls_conn: Option<ClientConnection>,
    last_response: Option<String>,
}

pub struct Server {
    host: String,
    port: u16,
    cert_file: String,
    key_file: String,
    listener: Option<TcpListener>,
}

impl Client {
    pub fn new(host: String, port: u16) -> Self {
        Client {
            host, port, socket: None, tls_conn: None, last_response: None
        }
    }
    
    pub fn connect(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let addr = format!("{}:{}", self.host, self.port);
        let stream = TcpStream::connect(&addr)?;
        stream.set_nodelay(true)?;
        self.socket = Some(stream);
        Ok(())
    }

    pub fn setup_tls(&mut self, cert_path: &str) -> Result<(), Box<dyn std::error::Error>> {
        // Load root certificates
        let f = File::open(cert_path)?;
        let mut reader = BufReader::new(f);
        let parsed: Vec<CertificateDer<'static>> = certs(&mut reader).collect::<Result<_, _>>()?;

        let mut roots = RootCertStore::empty();
        for cert in parsed {
            roots.add(cert)?;
        }

        let config = Arc::new(
            ClientConfig::builder()
                .with_root_certificates(roots)
                .with_no_client_auth(),
        );

        let server_name = ServerName::try_from("localhost")?;
        let tls_conn = ClientConnection::new(config, server_name)?;
        self.tls_conn = Some(tls_conn);

        Ok(())
    }

    pub fn send(&mut self, data: &[u8]) -> Result<(), Box<dyn std::error::Error>> {
        if let (Some(ref mut tls_conn), Some(ref mut socket)) = (&mut self.tls_conn, &mut self.socket) {
            let mut tls_stream = Stream::new(tls_conn, socket);
            tls_stream.write_all(data)?;
            tls_stream.flush()?;
            Ok(())
        } else if let Some(ref mut socket) = self.socket {
            socket.write_all(data)?;
            socket.flush()?;
            Ok(())
        } else {
            Err("No connection established".into())
        }
    }

    pub fn receive(&mut self, buffer: &mut [u8]) -> Result<usize, Box<dyn std::error::Error>> {
        if let (Some(ref mut tls_conn), Some(ref mut socket)) = (&mut self.tls_conn, &mut self.socket) {
            let mut tls_stream = Stream::new(tls_conn, socket);
            let bytes_read = tls_stream.read(buffer)?;
            if bytes_read > 0 {
                let response = String::from_utf8_lossy(&buffer[..bytes_read]);
                self.last_response = Some(response.to_string());
            }
            Ok(bytes_read)
        } else if let Some(ref mut socket) = self.socket {
            let bytes_read = socket.read(buffer)?;
            if bytes_read > 0 {
                let response = String::from_utf8_lossy(&buffer[..bytes_read]);
                self.last_response = Some(response.to_string());
            }
            Ok(bytes_read)
        } else {
            Err("No connection established".into())
        }
    }

    pub fn get_last_response(&self) -> Option<&String> {
        self.last_response.as_ref()
    }

    pub fn close(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        if let Some(tls_conn) = self.tls_conn.take() {
            drop(tls_conn);
        }
        if let Some(socket) = self.socket.take() {
            drop(socket);
        }
        Ok(())
    }
}

impl Server {
    pub fn new(host: String, port: u16, cert_file: String, key_file: String) -> Self {
        Server {
            host, port, cert_file, key_file, listener: None
        }
    }

    pub fn load_certificates(&self) -> Result<ServerConfig, Box<dyn std::error::Error>> {
        let cert_file = File::open(&self.cert_file)?;
        let mut cert_reader = BufReader::new(cert_file);
        let cert_chain: Vec<_> = certs(&mut cert_reader).collect::<Result<_, _>>()?;
        
        let key_file = File::open(&self.key_file)?;
        let mut key_reader = BufReader::new(key_file);
        let mut keys: Vec<_> = pkcs8_private_keys(&mut key_reader).collect::<Result<_, _>>()?;
        
        if keys.is_empty() {
            return Err("No private keys found".into());
        }
        
        let config = ServerConfig::builder()
            .with_no_client_auth()
            .with_single_cert(cert_chain, PrivateKeyDer::Pkcs8(keys.remove(0)))?;
        
        Ok(config)
    }

    pub fn handle_client(mut stream: TcpStream, config: Arc<ServerConfig>) -> Result<String, Box<dyn std::error::Error>> {
        let mut tls_conn = ServerConnection::new(config)?;
    
        let mut tls_stream = Stream::new(&mut tls_conn, &mut stream);
        
        // Drive the TLS handshake to completion
        tls_stream.flush()?;
        
        let mut buffer = [0; 1024];
        let bytes_read = tls_stream.read(&mut buffer)?;
        
        if bytes_read > 0 {
            let request = String::from_utf8_lossy(&buffer[..bytes_read]);
            Ok(request.to_string())
        } else {
            Ok("No data received".to_string())
        }
    }

    pub fn send_response(&self, stream: &mut TcpStream, config: Arc<ServerConfig>, response: &str) -> Result<(), Box<dyn std::error::Error>> {
        let mut tls_conn = ServerConnection::new(config)?;
        let mut tls_stream = Stream::new(&mut tls_conn, stream);
        
        let response_bytes = response.as_bytes();
        tls_stream.write_all(response_bytes)?;
        tls_stream.flush()?;
        
        Ok(())
    }

    pub fn start(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let config = Arc::new(self.load_certificates()?);
        let listener = TcpListener::bind(format!("{}:{}", self.host, self.port))?;
        self.listener = Some(listener);
        
        if let Some(ref listener) = self.listener {
            for stream in listener.incoming() {
                match stream {
                    Ok(stream) => {
                        let config = config.clone();
                        
                        std::thread::spawn(move || {
                            match Self::handle_client(stream, config) {
                                Ok(request) => {
                                },
                                Err(e) => eprintln!("TLS connection error: {}", e),
                            }
                        });
                    }
                    Err(e) => {
                        eprintln!("Connection error: {}", e);
                    }
                }
            }
        }
        
        Ok(())
    }

    pub fn stop(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        if let Some(listener) = self.listener.take() {
            drop(listener);
        }
        Ok(())
    }

    pub fn accept(&mut self) -> Result<TcpStream, Box<dyn std::error::Error>> {
        if let Some(ref listener) = self.listener {
            match listener.accept() {
                Ok((stream, _addr)) => Ok(stream),
                Err(e) => Err(e.into())
            }
        } else {
            Err("Server not started".into())
        }
    }
}