import socket
import threading
import sys

def forward(source, destination):
    string = ' '
    while string:
        string = source.recv(4096)
        if string:
            destination.sendall(string)
        else:
            try:
                source.shutdown(socket.SHUT_RD)
                destination.shutdown(socket.SHUT_WR)
            except OSError:
                pass

def handle(client_socket, target_host, target_port):
    try:
        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_socket.connect((target_host, target_port))
        
        t1 = threading.Thread(target=forward, args=(client_socket, remote_socket))
        t2 = threading.Thread(target=forward, args=(remote_socket, client_socket))
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass

def main():
    local_port = 3000
    remote_host = '127.0.0.1'
    remote_port = 3001
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind(('0.0.0.0', local_port))
    except Exception as e:
        print(f"Bind failed: {e}")
        return

    server.listen(5)
    print(f"Proxy listening on {local_port} -> {remote_host}:{remote_port}")
    
    while True:
        client, addr = server.accept()
        # print(f"Accepted connection from {addr[0]}:{addr[1]}")
        proxy_thread = threading.Thread(target=handle, args=(client, remote_host, remote_port))
        proxy_thread.daemon = True
        proxy_thread.start()

if __name__ == '__main__':
    main()
