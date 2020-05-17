import peer
from message import Connection, Announce, AnnounceOutput
from peers_manager import PeersManager
import socket
from urllib.parse import urlparse


class Tracker(object):
    def __init__(self, torrent):
        self.torrent = torrent
        self.threads_list = []
        self.connected_peers = {}
        self.addresses = []

    def get_peers_from_trackers(self):
        for i, tracker in enumerate(self.torrent.announce_list):
            try:
                self.scrapper(tracker[0])
            except:
                print('Failed to get peers list')
        self.connect_peers()
        return self.connected_peers

    def connect_peers(self):
        for sock_addr in self.addresses:
            new_peer = peer.Peer(int(self.torrent.number_of_pieces), sock_addr[0], sock_addr[1])
            if not new_peer.connect():
                continue
            print('Connected to ',(len(self.connected_peers)))
            self.connected_peers[new_peer.__hash__()] = new_peer
            if len(self.connected_peers) >2:
                break


    def scrapper(self, announce):
        url = urlparse(announce)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(4)
        ip, port = socket.gethostbyname(url.hostname), url.port
        response = self.send_message((ip, port), sock,  Connection())
        if not response: print('no response for connection')
        output = Connection()
        output.from_bytes(response)
        announce = Announce(self.torrent.info_hash, output.conn_id, self.torrent.peer_id)
        response = self.send_message((ip, port), sock, announce)
        if not response: print('no response for announce')
        output = AnnounceOutput()
        output.from_bytes(response)
        for ip, port in output.addresses:
            sock_addr = [ip, port]
            if sock_addr not in self.addresses:
                self.addresses.append(sock_addr)
        print("Got %d peers" % len(self.addresses))

    def send_message(self, conn, sock, tracker_message):
        message = tracker_message.to_bytes()
        sock.sendto(message, conn)
        try:
            response = PeersManager._read_from_socket(sock)
        except:
            return
        return response
