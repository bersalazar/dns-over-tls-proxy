import sys
import socket
import ssl
import logging
import threading

# Configuration
host = 'localhost'
port = 53
cloudflare_host = '1.1.1.1'
cloudflare_port = 853
number_of_connections = 5
timeout = 20
cert_location = './cert.crt'


def get_socket():
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def get_bound_socket(host, port):
    sock = get_socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    logger.debug(f'Created a socket bound to {host}:{port}')
    return sock


def get_ssl_wrapped_socket(host, port):
    logger.debug('Creating an SSL wrapped socket')

    # Create the upstream socket
    sock = get_socket()
    sock.settimeout(60)

    # Create an SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    context.load_verify_locations(cert_location)

    # Wrap the socket
    wrapped_socket = context.wrap_socket(sock, server_hostname=host)
    wrapped_socket.connect((host, port))
    return wrapped_socket


def resolve(query):
    logger.info('Resolve DNS over TLS')
    wrapped_socket = get_ssl_wrapped_socket(cloudflare_host, cloudflare_port)
    wrapped_socket.send(query)
    res = wrapped_socket.recv(1024)
    wrapped_socket.close()
    logger.debug(f'Closed the socket connecting to {cloudflare_host}')
    return res


def receive(sock, address):
    query = sock.recv(1024)
    logger.info(f'Received a DNS query from {address}')

    try:
        logger.debug('Attempting to resolve DNS query...')
        response = resolve(query)
        if response:
            logger.info(f'DNS server resolved address {address}')
            sock.send(response)
            logger.debug('Response sent to client over socket connection')
        else:
            logger.debug('Response was empty')
    except Exception:
        logger.error('An error occurred: {e}')
    finally:
        sock.close()
        logger.debug(f'Connection from {address} was closed')


# Main
logging.basicConfig(filename='app.log', level=logging.INFO)
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(sys.stdout))

s = get_bound_socket('', port)
s.listen(number_of_connections)
logger.info(f'Server started and listening on {host}:{port}')

while True:
    connection, address = s.accept()
    logger.debug(f'Got a connection from {address}')
    connection.settimeout(timeout)
    threading.Thread(target=receive, args=(connection, address)).start()
