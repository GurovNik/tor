import select
from threading import Thread
import message
import peer
import random


class PeersManager(Thread):
    def __init__(self, torrent, pieces_manager):
        Thread.__init__(self)
        self.peers = []
        self.torrent = torrent
        self.pieces_manager = pieces_manager
        self.pieces_by_peer = [[0, []] for _ in range(pieces_manager.number_of_pieces)]
        self.is_active = True

    def get_random_peer_having_piece(self, index):
        ready_peers = []

        for peer in self.peers:
            if peer.is_eligible() and peer.is_unchoked() and peer.am_interested() and peer.has_piece(index):
                ready_peers.append(peer)

        return random.choice(ready_peers) if ready_peers else None

    def has_unchoked_peers(self):
        for peer in self.peers:
            if peer.is_unchoked():
                return True
        return False


    @staticmethod
    def _read_from_socket(sock):
        data = b''

        while True:
            try:
                buff = sock.recv(4096)
                if len(buff) <= 0:
                    break
                data += buff
            except:
                break

        return data

    def run(self):
        while self.is_active:
            read = [peer.socket for peer in self.peers]
            read_list, _, _ = select.select(read, [], [], 1)

            for socket in read_list:
                peer = self.get_peer_by_socket(socket)
                if not peer.healthy:
                    self.remove_peer(peer)
                    continue
                try:
                    payload = self._read_from_socket(socket)
                except:
                    continue

                peer.read_buffer += payload
                for message in peer.get_messages():
                    self._process_new_message(message, peer)

    def _do_handshake(self, peer):
        try:
            handshake = message.Handshake(self.torrent.info_hash)
            peer.send_to_peer(handshake.to_bytes())
            return True
        except:
            return False

    def add_peers(self, peers):
        for peer in peers:
            if self._do_handshake(peer):
                self.peers.append(peer)

    def remove_peer(self, peer):
        if peer in self.peers:
            try:
                peer.socket.close()
            except:
                pass
            self.peers.remove(peer)

    def get_peer_by_socket(self, socket):
        for peer in self.peers:
            if socket == peer.socket:
                return peer

    def _process_new_message(self, new_message: message.Message, peer: peer.Peer):
        if isinstance(new_message, message.Choke):
            peer.handle_choke()
        elif isinstance(new_message, message.UnChoke):
            peer.handle_unchoke()
        elif isinstance(new_message, message.Interested):
            peer.handle_interested()
        elif isinstance(new_message, message.NotInterested):
            peer.handle_not_interested()
        elif isinstance(new_message, message.Have):
            peer.handle_have(new_message)
        elif isinstance(new_message, message.BitField):
            peer.handle_bitfield(new_message)
        elif isinstance(new_message, message.Request):
            peer.handle_request(new_message)
        elif isinstance(new_message, message.Piece):
            peer.handle_piece(new_message)