from struct import pack

HANDSHAKE_PSTR_V1 = b"BitTorrent protocol"
HANDSHAKE_PSTR_LEN = len(HANDSHAKE_PSTR_V1)
LENGTH_PREFIX = 4


def make_handshake(torrent):
	reserved = b'\x00' * 8
	return pack(">B{}s8s20s20s".format(HANDSHAKE_PSTR_LEN),
	                 HANDSHAKE_PSTR_LEN,
	                 HANDSHAKE_PSTR_V1,
	                 reserved,
	                 torrent.info_hash,
	                 torrent.peer_id)



def make_keep_alive():
	return pack(">I", 0)


def make_choke():
	return pack(">IB", 1, 0)


def make_unchoke():
	return pack(">IB", 1, 1)


def make_interested():
	return pack(">IB", 1, 2)


def make_uninterested():
	return pack(">IB", 1, 3)


def make_have(piece):
	pack(">IBI", 5, 4, piece)


def make_bitfield(bitfield):
	bitfield_bytes = bitfield.to_bytes()
	bitfield_len = len(bitfield_bytes)
	payload_len = 1 + bitfield_len
	return pack(">IB{}s".format(bitfield_len), payload_len, 5, bitfield_bytes)


def make_request(piece, block_offset, block_len):
	payload_len = 13
	return pack(">IBIII", payload_len, 6, piece, block_offset, block_len)


def make_piece(block_len, piece, block_offset, block):
	payload_len = 9 + block_len
	return pack(">IBII{}s".format(block_len), payload_len, 7,
	            piece, block_offset, block)


def make_cancel(piece, block_offset, block_length):
	return pack(">IBIII", 13, 8, piece, block_offset, block_length)


def make_port(port):
	return pack(">IBI", 5, 9, port)
