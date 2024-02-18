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
