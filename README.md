Marznode
---------
Just a fork of Marzban-node.

- [X] xray-core
- [X] hysteria
- [ ] wireguard
- [ ] sing-box

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
