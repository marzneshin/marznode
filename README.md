Marznode
---------
A fork of Marzban-node that aims to bring stability to nodes by using sqlite as the database and grpc as the protocol.


Mechanism
---------
The protocol used between the client(Marzneshin) and server(Marznode) does the mere job of **updating users' information 
in marznode, updating marznode inbounds in Marzneshin and getting stats from xray**; nothing more.

Marznode saves users' information in a database and the client could be assured of synchronization by repopulating the 
storage whenever necessary e.g. when the response is not correct.

Whenever a client connects marznode it could get a list of inbounds and then repopulate it's users.

## Setup Guide

Setup python virtual environment
```sh
python -m venv .venv/
source .venv/bin/activate
```

Install the requirements

```sh
pip install -r requirements.txt
```

Configure the node. you should provide the correct path to your xray binary and your xray config file.

```sh
cp .env.example .env
```


Set your certificate for the node by saving the certificate in a file and providing address of the certificate
file using `CLIENT_SSL_CERT`. And then execute and start the node:

```sh
python marznode.py
```
