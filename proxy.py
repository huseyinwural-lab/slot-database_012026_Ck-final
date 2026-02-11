import socket
import threading

def handle(buffer, direction, src_address, src_port, dst_address, dst_port):
    '''
    description: forward data between connections
    '''
    while True:
        try:
            data = buffer.recv(4096)
            if not data: break
            direction.sendall(data)
        except Exception as e:
            break
    direction.close()
    buffer.close()

def route(source, src_address, src_port, dst_address, dst_port):
    '''
    description: route data between connections
    '''
    destination = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    destination.connect((dst_address, dst_port))
    threading.Thread(target=handle, args=(source, destination, src_address, src_port, dst_address, dst_port)).start()
    threading.Thread(target=handle, args=(destination, source, dst_address, dst_port, src_address, src_port)).start()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 3000))
    server.listen(5)
    print("Proxying 3000 -> 3001")
    while True:
        source, address = server.accept()
        threading.Thread(target=route, args=(source, address[0], address[1], '127.0.0.1', 3001)).start()

if __name__ == '__main__':
    main()
