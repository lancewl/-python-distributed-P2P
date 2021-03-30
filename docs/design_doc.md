# Design Doc

## Super Peer

For the super peer, I seperate the logic into two part, connection with weak peers and connection with other super peers.

### Weak Peers Connection

For the connection with weak peers, I use pretty the same method as I implemented the indexing server in pa2. I use `socket` which is a built-in module in `Python 3` to create connections between it and the weak peers. At first, it will start listening on a specific port(can be set by passing argument). Whenever, a peer connect to the super peer, it will create a thread by using `threading` module in `Python 3` to handle the connection with the peer so that the super peer can handle multiple peer connections in the same time.

After the connection has been made between the super peer and the weak peer, they will start to send and receive message in `json` format. The super peer will fisrt waiting for the weak peer to send the information of their file list to make a initial register. After receving the file list from the weak peer, the super peer will update the `peer_table` which stores the information of every peers that are currently connected to the P2P system. Then the super peer will start to waiting the weak peer to send any requests such as `UPDATE`, `QUERY`. If it receive an `QUERY` request, it will lookup the `peer_table` and return all ip address that contain the target file.

To maintain a table for storing the information of every peers that are currently connected to the P2P system. I declare a global variable `peer_table` which is a `dictionary` in `Python` so that every connections in different threads can share the table with others. I also add a condtion lock to any operations that trying to access or modify the `peer_table` to make sure it works properly under multi-threading structure.

### Message Broadcasting between Super Nodes

To broadcast messages between super nodes, instead of creating a lot of `TCP` connections between super nodes, I use `UDP` to send out the messages. By using `UDP`, we can simply send out the messgae to the target destination. Users can assign the neighbor peers to the super peer program. It will be stored as a global list in the super peer program and be used to broadcast the message. When the super peers receive a QUERY request from weak peers, it will first create a new `json` message with type QUERY, file name, global ID and the TTL(can be set by users) then broadcast to every neighbor peers. Moreover, it will create an entry in the global variable `queryhit_table` which will be used to indentify received QUERYHIT message. The global ID is consist of the weak peer's address, port, and timestamp so that we can make sure that the ID will be globally unique.

To properly broadcast messages to other peers, the super peer will broadcast received messages if the TTL of that message is greater than 0 and the value of TTL will decrease one when it be broadcasted. When a super peer received a QUERY message, it will check the `peer_table` for the target file. If it found a match peer that holds the target file, it will broadcast out the QUERYHIT message out to its neighbors. When a super peer received a QUERYHIT message, it will check if the message id is in the `queryhit_table`. If it is, it will add the peer information to the response message which will be later send back to the weak peer.

To prevent broadcasting duplicate message which will highly increase the loading of all super nodes, I have another global variable `visited` to store every sent messages. Before the super peer send any message, it will first check if this messages has been sent before. If it has, it won't send it again to the network.

### Possible Improvements

I use only a single `dictionary` to store the information of every peers. If there are many peers in the system, it might cause a lot of time on `QUERY` request since it needs to go through the table and find any matched file in peers. It's is possible to have a more efficient way to store the information such as two `dictionary`, one maps the peer to their file list and one maps the file to the peer ip address.

When a super peer send our a QUERY message, it is possible that there's no QUERYHIT in the network or there's many QUERYHIT, so it is hard to decide how long should a super peer waiting for the QUERYHIT message be sent back. I use a simple while loop with a short `sleep()` to continuously check for the incomming QUERYHIT message which will cause some overhead. There might be a more efficient way to solve this problem.

## Weak Peer

For the weak peer, we need both clients and servers mechanism at the same time which can be divided to a client that responsible for connecting super peer, a server that respondible for other peers to download files and serveral clients that try to download files from other peers. I acheive all this by `socket` and `threading`  which are built-in modules in `Python 3` to make all components work indivisually.

The peer script will first try to connect to the super peer(can be specify by argument). Since the super peer is necessary to our P2P system, the peer script keep running only if it successfully connects to the super peer. After connect to the super peer, it will send a `REGISTER` message to the super peer with the local file list and also create a server at the same time listenning to any request of files from other peers. After register with the super peer, it will start a prompt and waiting for users to enter any instructions(supported instructions: `QUERY`, `WAIT`, `EXIT`). All invalid input will occur an error message and redirect to the prompt again.

`QUERY` instruction plays an important role in the peer script. What it mainly do is passing the filename that the user want to download to the super peer and wait for response. After receive the ip address that hold the file, the peer script will show a new prompt letting users to choose which peer to download the target file. The peer script will then create another thread to connect to the peer chosed by the user and try to download the target files.

To support an automatic update mechanism, I use `watchdog` python package. I create another thread and run an `oberver` that keep watching any changes in the hosting folder. It will send an `UPDATE` request to the super peer whenever it detects any changes.

Due to the fact that the weak peer needs at least a client(connecting super peer) and a server(hosting files for other peers to download), a weak peer needs two ports - A(for client) and B(for server). The problem is that for super peer, it only knows the A port that the peer used to connect to the super peer so the super peer won't have any records of the B port. However, other peers need to know the B port from the super peer to download files. To solve this issue, I make the relation of A and B to be B = A + 1. Port B will always equal to A + 1 so that the other weak peers can easily calculate the port B by getting port A from super peer.

### Possible Improvements

I think the way I solve the double port issue might not be very ideal. It will casue some potential errors that multiple peer is trying to use the same port. Users also need to aware that don't start two peers with adjacent port. For example, start a peer on port 50000 and port 50001 will cause an error since that the peer with 50000 will also use 50001 at the same time. Maybe I should not bind a specific port to the client component. I can try to send the port information to the super peer when register.

## Others

To make the server script more easily to use, I use [click](https://github.com/pallets/click) to create a user friendly command line interface. Users can simply run `python peer.py --help` to see every options that can be passed into the peer script and the default values.
