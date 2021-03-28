import os
import sys
import socket
import threading
import json
import click
import time

SIZE = 1024
FORMAT = "utf-8"
SERVER_DATA_PATH = "./"
TTL = 1

# Global Variable
neighbor_peers = []
peer_table = {}
queryhit_table = {}
visited = set()
cond = threading.Condition()

def startUDPServer(hostname, port):
    # Setup UDP server for broadcasting message
    global peer_table
    global cond
    global queryhit_table
    global visited
    udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    udp_server.bind((hostname, port))
    print(f"[LISTENING] Super Peer(UDP) is listening on {hostname}:{port}")

    while True:
        data, addr = udp_server.recvfrom(SIZE)
        json_data = json.loads(data.decode(FORMAT))
        print(f"[BROADRECV] {json_data['type']} - ID: {json_data['msgid']}, TTL: {json_data['TTL']}")
        identity = (json_data['type'], json_data['msgid'])
        if json_data['TTL'] > 0 and identity not in visited:
            # broadcast msg if TTL > 0
            # prevent duplicate message
            visited.add(identity)
            broadcastMsg(json_data)
        
        if json_data['type'] == 'QUERY' and json_data['msgid'] not in queryhit_table:
            # only check for query hit on other super peers not the one initial the query message
            # the super peer that initial the query message will store the msgid in `queryhit_table`
            res = []
            cond.acquire()
            for peer, filelist in peer_table.items():
                if json_data['file'] in filelist:
                    res.append(peer)
            cond.release()

            if len(res) > 0:
                broadcastMsg({"type": "QUERYHIT", "msgid": json_data['msgid'], "filelist": res, "TTL": TTL})
        
        elif json_data['type'] == 'QUERYHIT':
            if json_data['msgid'] in queryhit_table:
                # store the result in QUERYHIT message
                queryhit_table[json_data['msgid']].update(json_data['filelist'])


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

def broadcastMsg(msg):
    global neighbor_peers
    msg['TTL'] -= 1
    broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    encode = json.dumps(msg).encode(FORMAT)
    
    for n in neighbor_peers:
        addr, port = n.split(":")
        broadcaster.sendto(encode, (addr, int(port)))

def clientHandler(conn, addr):
    global peer_table
    global cond
    global queryhit_table
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

            # broadcast query message to neighbor super peers
            global_id = str(addr[1]) + "-" + str(time.time()) # use client port + timestamp as message id
            queryhit_table[global_id] = set([]) # create a new entry in query hit table
            msg = {
                "type": 'QUERY',
                "msgid": global_id,
                "file": query_file,
                "TTL": TTL
            }
            broadcastMsg(msg)

            # waiting for query hit
            snapshot = queryhit_table[global_id]
            while True:
                time.sleep(0.01)
                if queryhit_table[global_id] == snapshot:
                    break # break if there's no change in last second
                snapshot = queryhit_table[global_id]

            res = list(queryhit_table[global_id])
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
@click.option('--ttl',
              default=1,
              help='Broadcast TTL')
def startSuperPeer(tport, uport, neighbors, ttl):
    print("[STARTING] Super Peer is starting")
    global neighbor_peers
    global TTL
    neighbor_peers = neighbors
    TTL = ttl
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