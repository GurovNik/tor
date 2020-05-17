import socket
from make_message import *
import time

REQUESTED = []

def make_req(l):
	global REQUESTED
	REQUESTED = l

def download(connecions):


	for conn in active_connecions:
		queue = []
		resp = _read_from_socket(conn)
		resp = handle_messages(resp, conn, queue)
	print()


def connect(peer, torrent):
	try:
		# with socket.socket() as s:
		ip_nums = [num for num in peer['ip']]
		ip = ''.join(ip_nums)
		s = socket.create_connection((ip, peer['port']), timeout=2)
		# s.setblocking(False)
		s.send(make_handshake(torrent))
		time.sleep(1)
		resp = _read_from_socket(s)
		if is_handshake(resp, torrent):
			print('Handshake success')
			status = start_communication(torrent, s)
			if status:
				print(ip, 'unchoked')
		return s, status


	except:
		print('Failed to connect')
		return None


# s.sendall()
# data = s.recv(1024)
import errno


def _read_from_socket(sock):
	attempts = 3
	data = b''
	for i in range(attempts):
		# print('attempt: ',i)
		try:
			buff = sock.recv(4096)
			if len(buff) <= 0:
				attempts -= 1
				time.sleep(0.2)

			data += buff
			print(len(data))
		except socket.error as e:
			err = e.args[0]
			if err != errno.EAGAIN or err != errno.EWOULDBLOCK:
				print("Wrong errno {}".format(err))
		# break
		except Exception:
			print("Recv failed")
	# break

	return data


def is_handshake(msg, tor):
	pstrlen, = unpack(">B", msg[:1])
	pstr, reserved, info_hash, peer_id = unpack(">{}s8s20s20s".format(pstrlen), msg[1:68])
	return tor.info_hash == info_hash


def handle_messages(msg, s=None, queue=None):
	if len(msg) < 4:
		return None
	else:
		msg_id = msg[4]
	if len(msg) > 5:
		payload = msg[5:]
	if msg_id == 0: return choke_handler()
	if msg_id == 1: return unchoke_handler()
	if msg_id == 4: return have_handler(payload, s, queue)
	if msg_id == 5: return bitfield_handler(payload)
	if msg_id == 7: return piece_handler(payload, s, queue)


def start_communication(torrent, s):
	print('sent intr')
	resp = None
	attempts = 1
	for i in range(attempts):
		s.send(make_interested())
		time.sleep(1)
		resp = _read_from_socket(s)
	if not resp:
		print('Peer is silent')
		return None
	else:
		status = handle_messages(resp)
	return status


def choke_handler():
	pass


def unchoke_handler():
	return 1


def have_handler(payload, s, q):
	piece = unpack(">I", payload[0])
	q.append(piece)
	if not REQUESTED[piece]:
		s.send(make_request())
		REQUESTED[piece] = 1
		print()


def bitfield_handler():
	pass


def piece_handler():
	pass

