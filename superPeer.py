import os
import sys
import socket
import threading
import json
import click

SIZE = 1024
FORMAT = "utf-8"
SERVER_DATA_PATH = "./"
TTL = 2

peer_table = {}
neighbor_peers = []
cond = threading.Condition()

def startUDPServer(hostname, port):
    # Setup UDP server for broadcasting message
    udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    udp_server.bind((hostname, port))
    print(f"[LISTENING] Super Peer(UDP) is listening on {hostname}:{port}")

    while True:
        data, addr = udp_server.recvfrom(SIZE)
        print("received message: %s" % data)

def startTCPServer(hostname, port):
    # Setup TCP server for connecting weak peer
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.bind((hostname, port))
    tcp_server.listen()
    print(f"[LISTENING] Super Peer(TCP) is listening on {hostname}:{port}")

    while True:
        conn, addr = tcp_server.accept()
        thread = threading.Thread(target=clientHandler, args=(conn, addr))
        thread.daemon = True
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

def clientHandler(conn, addr):
    global peer_table
    global cond
    full_addr = addr[0] + ":" + str(addr[1])

    print(f"[NEW CONNECTION] {addr} connected.")
    conn.send(json.dumps({"type": "OK", "msg": "Welcome to Super Peer!"}).encode(FORMAT))

    while True:
        data = conn.recv(SIZE).decode(FORMAT)

        if not data:
            # delete record in peer_table when data = None, client has disconnected
            print(f"[UNREGISTER] {full_addr} unrigistered")
            cond.acquire()
            del peer_table[full_addr]
            cond.release()
            break

        json_data = json.loads(data)

        if json_data["action"] == "REGISTER":
            # register file list from peers
            print(f"[REGISTER] {full_addr} registerd")
            cond.acquire()
            peer_table[full_addr] = json_data["filelist"]
            # print(peer_table)
            cond.release()
        
        elif json_data["action"] == "UPDATE":
            # Update file list of peers
            print(f"[UPDATE] {full_addr} file list updated")
            cond.acquire()
            peer_table[full_addr] = json_data["filelist"]
            # print(peer_table)
            cond.release()
        
        elif json_data["action"] == "QUERY":
            # query for a file
            query_file = json_data["file"]
            print(f"[QUERY] {full_addr} query {query_file}")
            res = []
            cond.acquire()
            for peer, filelist in peer_table.items():
                if peer != full_addr and query_file in filelist:
                    res.append(peer)
            cond.release()
            conn.send(json.dumps({"type": "QUERY-RES", "msg": res, "file": query_file}).encode(FORMAT))

    conn.close()

@click.command()
@click.option('--tport',
              '-t',
              default="5000",
              help='Hosting TCP port(for connecting weak peer)')
@click.option('--uport',
              '-u',
              default="10000",
              help='Hosting UDP port(for broadcasting)')
@click.option('--neighbors',
              '-n',
              multiple=True,
              default=[],
              help='Specify neighbor super nodes')
def startSuperPeer(tport, uport, neighbors):
    print("[STARTING] Super Peer is starting")
    global neighbor_peers
    neighbor_peers = neighbors
    hostname = socket.gethostbyname(socket.gethostname())

    # start udp server on another thread
    thread = threading.Thread(target=startUDPServer, args=(hostname, int(uport)))
    thread.daemon = True
    thread.start()

    startTCPServer(hostname, int(tport))
    

if __name__ == "__main__":
    try:
        startSuperPeer()
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Super Peer is down")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)