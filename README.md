Marznode
---------
A fork of Marzban-node that aims to bring stability to nodes by using sqlite as the database and grpc as the protocol.


Mechanism
---------
The protocol used between the client(Marzneshin) and server(Marznode) does the mere job of **updating users' information 
in marznode, updating marznode inbounds in Marzneshin and getting stats from xray**; nothing more.

Marznode saves users' information in a database and the client could be assured of synchronization by repopulating the 
storage whenever necessary e.g. when the response is not correct.

Whenever Marznode starts up, it generates a checksum of the inbounds fed to xray. the client could store this sum and 
send it to the server with each request as metadata, whenever it changes the server return an error and the client has
to fetch the list again. This ensures any changes to xray inbounds are known by both sides.

Right now users are considered to be immutable objects consisting of _id_, _username_ and a _key_.