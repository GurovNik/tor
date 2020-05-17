import random
import socket
from struct import pack, unpack
import bitstring


HANDSHAKE_PSTR = b"BitTorrent protocol"
HANDSHAKE_PSTR_LEN = len(HANDSHAKE_PSTR)
LENGTH_PREFIX = 4


class WrongMessageException(Exception):
    pass

class MessageDispatcher:

    def __init__(self, payload):
        self.payload = payload

    def dispatch(self):
        try:
            payload_length, message_id, = unpack(">IB", self.payload[:5])
        except:
            return None

        map_id_to_message = {
            0: Choke,
            1: UnChoke,
            2: Interested,
            3: NotInterested,
            4: Have,
            5: BitField,
            6: Request,
            7: Piece,
            8: Cancel,
            9: Port
        }
        return map_id_to_message[message_id].from_bytes(self.payload)


class Message:
    def to_bytes(self):
        raise NotImplementedError()

    @classmethod
    def from_bytes(cls, payload):
        raise NotImplementedError()


class Connection(Message):
    def __init__(self):
        super(Connection, self).__init__()
        self.conn_id = pack('>Q', 0x41727101980)
        self.action = pack('>I', 0)
        self.trans_id = pack('>I', random.randint(0, 100000))

    def to_bytes(self):
        return self.conn_id + self.action + self.trans_id

    def from_bytes(self, payload):
        self.action, = unpack('>I', payload[:4])
        self.trans_id, = unpack('>I', payload[4:8])
        self.conn_id, = unpack('>Q', payload[8:])


class Announce(Message):
    def __init__(self, info_hash, conn_id, peer_id):
        super(Announce, self).__init__()
        self.peer_id = peer_id
        self.conn_id = conn_id
        self.info_hash = info_hash
        self.trans_id = pack('>I', random.randint(0, 100000))
        self.action = pack('>I', 1)

    def to_bytes(self):
        conn_id = pack('>Q', self.conn_id)
        action = self.action
        trans_id = self.trans_id
        downloaded = pack('>Q', 0)
        left = pack('>Q', 0)
        uploaded = pack('>Q', 0)
        event = pack('>I', 0)
        ip = pack('>I', 0)
        key = pack('>I', 0)
        num_want = pack('>i', -1)
        port = pack('>h', 8000)
        msg = (conn_id + action + trans_id + self.info_hash + self.peer_id + downloaded +
               left + uploaded + event + ip + key + num_want + port)
        return msg


class AnnounceOutput:

    def __init__(self):
        self.action = None
        self.trans_id = None
        self.interval = None
        self.leechs = None
        self.seeds = None
        self.addresses = []

    def from_bytes(self, payload):
        self.action, = unpack('>I', payload[:4])
        self.trans_id, = unpack('>I', payload[4:8])
        self.interval, = unpack('>I', payload[8:12])
        self.leechs, = unpack('>I', payload[12:16])
        self.seeds, = unpack('>I', payload[16:20])
        self.addresses = self._parse_address(payload[20:])

    def _parse_address(self, raw_bytes):
        socks_addr = []
        for i in range(int(len(raw_bytes) / 6)):
            start = i * 6
            end = start + 6
            ip = socket.inet_ntoa(raw_bytes[start:(end - 2)])
            raw_port = raw_bytes[(end - 2):end]
            port = raw_port[1] + raw_port[0] * 256
            socks_addr.append((ip, port))
        return socks_addr


class Handshake(Message):
    total_length = 68

    def __init__(self, info_hash, peer_id=b'-nekitos000000000000'):
        super(Handshake, self).__init__()
        self.peer_id = peer_id
        self.info_hash = info_hash

    def to_bytes(self):
        reserved = b'\x00' * 8
        handshake = pack(">B{}s8s20s20s".format(HANDSHAKE_PSTR_LEN), HANDSHAKE_PSTR_LEN, HANDSHAKE_PSTR, reserved, self.info_hash, self.peer_id)

        return handshake

    @classmethod
    def from_bytes(cls, payload):
        pstrlen, = unpack(">B", payload[:1])
        pstr, reserved, info_hash, peer_id = unpack(">{}s8s20s20s".format(pstrlen), payload[1:cls.total_length])
        return Handshake(info_hash, peer_id)


class KeepAlive(Message):
    payload_length = 0
    total_length = 4

    def __init__(self):
        super(KeepAlive, self).__init__()

    def to_bytes(self):
        return pack(">I", self.payload_length)

    @classmethod
    def from_bytes(cls, payload):
        payload_length = unpack(">I", payload[:cls.total_length])
        if payload_length != 0:
            raise WrongMessageException()
        return KeepAlive()


class Choke(Message):
    id = 0
    chokes = True
    payload_len = 1
    total_len = 5

    def __init__(self):
        super(Choke, self).__init__()

    def to_bytes(self):
        return pack(">IB", self.payload_len, self.id)

    @classmethod
    def from_bytes(cls, payload):
        payload_length, id = unpack(">IB", payload[:cls.total_len])
        if id != cls.id:
            raise WrongMessageException()
        return Choke()


class UnChoke(Message):
    id = 1
    chokes = False
    payload_len = 1
    total_len = 5

    def __init__(self):
        super(UnChoke, self).__init__()

    def to_bytes(self):
        return pack(">IB", self.payload_len, self.id)

    @classmethod
    def from_bytes(cls, payload):
        payload_len, id = unpack(">IB", payload[:cls.total_len])
        if id != cls.id:
            raise WrongMessageException()
        return UnChoke()


class Interested(Message):
    id = 2
    interested = True
    payload_len = 1
    total_len = 4 + payload_len

    def __init__(self):
        super(Interested, self).__init__()

    def to_bytes(self):
        return pack(">IB", self.payload_len, self.id)

    @classmethod
    def from_bytes(cls, payload):
        payload_len, id = unpack(">IB", payload[:cls.total_len])
        if id != cls.id:
            raise WrongMessageException()
        return Interested()


class NotInterested(Message):
    id = 3
    interested = False
    payload_len = 1
    total_len = 5

    def __init__(self):
        super(NotInterested, self).__init__()

    def to_bytes(self):
        return pack(">IB", self.payload_len, self.id)

    @classmethod
    def from_bytes(cls, payload):
        payload_len, id = unpack(">IB", payload[:cls.total_len])
        if id != cls.id:
            raise WrongMessageException()
        return Interested()


class Have(Message):
    id = 4
    payload_len = 5
    total_len = 4 + payload_len

    def __init__(self, piece_index):
        super(Have, self).__init__()
        self.piece_index = piece_index

    def to_bytes(self):
        pack(">IBI", self.payload_len, self.id, self.piece_index)

    @classmethod
    def from_bytes(cls, payload):
        payload_len, id, piece_index = unpack(">IBI", payload[:cls.total_len])
        if id != cls.id:
            raise WrongMessageException()
        return Have(piece_index)


class BitField(Message):
    id = 5
    payload_len = -1
    total_len = -1

    def __init__(self, bitfield):
        super(BitField, self).__init__()
        self.bitfield = bitfield
        self.bitfield_as_bytes = bitfield.tobytes()
        self.bitfield_length = len(self.bitfield_as_bytes)
        self.payload_len = 1 + self.bitfield_length
        self.total_len = 4 + self.payload_len

    def to_bytes(self):
        return pack(">IB{}s".format(self.bitfield_length), self.payload_len, self.id, self.bitfield_as_bytes)

    @classmethod
    def from_bytes(cls, payload):
        payload_len, id = unpack(">IB", payload[:5])
        bitfield_len = payload_len - 1
        if id != cls.id:
            raise WrongMessageException("Not a BitField message")
        raw_bitfield, = unpack(">{}s".format(bitfield_len), payload[5:5 + bitfield_len])
        bitfield = bitstring.BitArray(bytes=bytes(raw_bitfield))
        return BitField(bitfield)


class Request(Message):
    id = 6
    payload_len = 13
    total_len = 4 + payload_len

    def __init__(self, piece_index, block_offset, block_length):
        super(Request, self).__init__()
        self.piece_index = piece_index
        self.block_offset = block_offset
        self.block_length = block_length

    def to_bytes(self):
        return pack(">IBIII", self.payload_len, self.id, self.piece_index, self.block_offset, self.block_length)

    @classmethod
    def from_bytes(cls, payload):
        payload_len, id, piece_index, block_offset, block_len = unpack(">IBIII", payload[:cls.total_len])
        if id != cls.id:
            raise WrongMessageException("Not a Request message")
        return Request(piece_index, block_offset, block_len)


class Piece(Message):
    id = 7
    payload_len = -1
    total_len = -1

    def __init__(self, block_length, piece_index, block_offset, block):
        super(Piece, self).__init__()
        self.block_length = block_length
        self.piece_index = piece_index
        self.block_offset = block_offset
        self.block = block
        self.payload_len = 9 + block_length
        self.total_len = 4 + self.payload_len

    def to_bytes(self):
        return pack(">IBII{}s".format(self.block_length), self.payload_len, self.id, self.piece_index, self.block_offset, self.block)

    @classmethod
    def from_bytes(cls, payload):
        block_len = len(payload) - 13
        payload_len, id, piece_index, block_offset, block = unpack(">IBII{}s".format(block_len), payload[:13 + block_len])
        if id != cls.id:
            raise WrongMessageException("Not a Piece message")
        return Piece(block_len, piece_index, block_offset, block)


class Cancel(Message):
    id = 8
    payload_len = 13
    total_len = 4 + payload_len

    def __init__(self, piece_index, block_offset, block_length):
        super(Cancel, self).__init__()
        self.piece_index = piece_index
        self.block_offset = block_offset
        self.block_length = block_length

    def to_bytes(self):
        return pack(">IBIII", self.payload_len, self.id, self.piece_index, self.block_offset, self.block_length)

    @classmethod
    def from_bytes(cls, payload):
        payload_len, id, piece_index, block_offset, block_len = unpack(">IBIII", payload[:cls.total_len])
        if id != cls.id:
            raise WrongMessageException("Not a Cancel message")
        return Cancel(piece_index, block_offset, block_len)


class Port(Message):
    id = 9
    payload_len = 5
    total_len = 4 + payload_len

    def __init__(self, listen_port):
        super(Port, self).__init__()
        self.listen_port = listen_port

    def to_bytes(self):
        return pack(">IBI", self.payload_len, self.id, self.listen_port)

    @classmethod
    def from_bytes(cls, payload):
        payload_len, id, listen_port = unpack(">IBI", payload[:cls.total_len])
        if id != cls.id:
            raise WrongMessageException("Not a Port message")
        return Port(listen_port)
