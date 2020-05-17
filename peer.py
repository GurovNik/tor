import time
import socket
import struct
import bitstring
from pubsub import pub
import message


class Peer(object):
    def __init__(self, number_of_pieces, ip, port=6881):
        self.last_call = 0.0
        self.has_handshaked = False
        self.healthy = False
        self.read_buffer = b''
        self.socket = None
        self.ip = ip
        self.port = port
        self.number_of_pieces = number_of_pieces
        self.bit_field = bitstring.BitArray(number_of_pieces)
        self.state = {
            'am_choking': True,
            'am_interested': False,
            'peer_choking': True,
            'peer_interested': False,
        }

    def __hash__(self):
        return "%s:%d" % (self.ip, self.port)

    def connect(self):
        try:
            self.socket = socket.create_connection((self.ip, self.port), timeout=2)
            self.socket.setblocking(False)
            self.healthy = True

        except Exception:
            print("Failed to connect to peer")
            return False

        return True

    def send_to_peer(self, msg):
        try:
            self.socket.send(msg)
            self.last_call = time.time()
        except:
            self.healthy = False

    def is_eligible(self):
        return (time.time() - self.last_call) > 0.2

    def has_piece(self, index):
        return self.bit_field[index]

    def am_choking(self):
        return self.state['am_choking']

    def am_unchoking(self):
        return not self.am_choking()

    def is_choking(self):
        return self.state['peer_choking']

    def is_unchoked(self):
        return not self.is_choking()

    def is_interested(self):
        return self.state['peer_interested']

    def am_interested(self):
        return self.state['am_interested']

    def handle_choke(self):
        self.state['peer_choking'] = True

    def handle_unchoke(self):
        self.state['peer_choking'] = False

    def handle_interested(self):
        self.state['peer_interested'] = True
        if self.am_choking():
            self.send_to_peer(message.UnChoke().to_bytes())

    def handle_not_interested(self):
        self.state['peer_interested'] = False

    def handle_have(self, have):
        self.bit_field[have.piece_index] = True
        if self.is_choking() and not self.state['am_interested']:
            interested = message.Interested().to_bytes()
            self.send_to_peer(interested)
            self.state['am_interested'] = True

    def handle_bitfield(self, bitfield):
        self.bit_field = bitfield.bitfield
        if self.is_choking() and not self.state['am_interested']:
            interested = message.Interested().to_bytes()
            self.send_to_peer(interested)
            self.state['am_interested'] = True

    def handle_request(self, request):
        if self.is_interested() and self.is_unchoked():
            pub.sendMessage('PiecesManager.PeerRequestsPiece', request=request, peer=self)

    def handle_piece(self, message):
        pub.sendMessage('PiecesManager.Piece', piece=(message.piece_index, message.block_offset, message.block))

    def _handle_handshake(self):
        try:
            handshake_message = message.Handshake.from_bytes(self.read_buffer)
            self.has_handshaked = True
            self.read_buffer = self.read_buffer[handshake_message.total_length:]
            return True
        except:
            self.healthy = False
        return False

    def _handle_keep_alive(self):
        try:
            keep_alive = message.KeepAlive.from_bytes(self.read_buffer)
        except:
            return False
        self.read_buffer = self.read_buffer[keep_alive.total_length:]
        return True

    def get_messages(self):
        while len(self.read_buffer) > 4 and self.healthy:
            if (not self.has_handshaked and self._handle_handshake()) or self._handle_keep_alive():
                continue
            payload_length, = struct.unpack(">I", self.read_buffer[:4])
            total_length = payload_length + 4
            if len(self.read_buffer) < total_length:
                break
            else:
                payload = self.read_buffer[:total_length]
                self.read_buffer = self.read_buffer[total_length:]
            try:
                m = message.MessageDispatcher(payload).dispatch()
                if m:
                    yield m
            except:
                pass