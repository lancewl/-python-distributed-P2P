# Python Distributed P2P System

## Requirement

* Python 3.7 and above

## Installation

### [pip](https://pip.pypa.io/en/stable/)

```bash
pip install requirements.txt
```

### [pipenv](https://pipenv.kennethreitz.org/en/latest/#) 

Use pipenv to manage and install the Python packages.

```bash
pipenv install
```

## Usage

### Super Peer Script

The `server.py` will start an super peer for the P2P system.

```bash
Usage: superPeer.py [OPTIONS]

Options:
  -t, --tport TEXT      Hosting TCP port(for connecting weak peer)
  -u, --uport TEXT      Hosting UDP port(for broadcasting)
  -n, --neighbors TEXT  Specify neighbor super nodes
  --ttl INTEGER         Broadcast TTL
  --help                Show this message and exit.
```

Example:

```bash
python superPeer.py -t 5001 -u 10001 -n 127.0.0.1:10000
```

Above command will start a super peer and connect to 127.0.0.1:10000 neighbor peer.

### Weak Peer Script

The `weakPeer.py` will start a weak peer node in the P2P system.

```bash
Usage: weakPeer.py [OPTIONS] PORT

Options:
  --dir TEXT     Serving directory relative to current directory
  --server TEXT  Indexing server address
  --help         Show this message and exit.
```

Example:

```bash
python weakPeer.py 3001 --server 127.0.0.1:5001
```

Above command will start a weak peer node and host on port 3001.

### Evaluation Scripts

The `runAll.sh` will evaluate the performance of QUERY action under different number of clients in all to all topology setting.

```bash
Usage: ./runAll.sh [clients]
```

The `runLinear.sh` will evaluate the performance of QUERY action under different number of clients in linear topology setting.

```bash
Usage: ./runLinear.sh [clients]
```
