use std::fs::File;
use std::io::{BufReader, Read, Write};
use std::net::TcpStream;
use std::sync::Arc;

use rustls::{ClientConfig, ClientConnection, RootCertStore, Stream};
use rustls::pki_types::{CertificateDer, ServerName};
use rustls_pemfile::certs;

fn load_root_store_from_cert(path: &str) -> Result<RootCertStore, Box<dyn std::error::Error>> {
    let f = File::open(path)?;
    let mut reader = BufReader::new(f);

    let parsed: Vec<CertificateDer<'static>> = certs(&mut reader).collect::<Result<_, _>>()?;

    let mut roots = RootCertStore::empty();
    for cert in parsed {
        roots.add(cert)?;
    }
    Ok(roots)
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 1) TCP connect
    let mut tcp = TcpStream::connect("127.0.0.1:443")?;
    tcp.set_nodelay(true)?;

    let roots = load_root_store_from_cert("cert.pem")?;
    let config = Arc::new(
        ClientConfig::builder()
            .with_root_certificates(roots)
            .with_no_client_auth(),
    );

    let server_name = ServerName::try_from("localhost")?;
    let mut tls_conn = ClientConnection::new(config, server_name)?;
    tls_conn.set_buffer_limit(Some(1024));

    let mut tls_stream = Stream::new(&mut tls_conn, &mut tcp);

    let msg = b"Hello, Server!";
    tls_stream.write_all(msg)?;
    tls_stream.flush()?;
    println!("Sent: {}", String::from_utf8_lossy(msg));

    let mut buf = [0u8; 1024];
    let n = tls_stream.read(&mut buf)?;
    if n > 0 {
        println!("Received: {}", String::from_utf8_lossy(&buf[..n]));
    } else {
        println!("No response from server");
    }

    Ok(())
}