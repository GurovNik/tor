import socket
from urllib import parse as url_parse
from first_attempt.utils import *
from struct import pack

PORT = 8000
import random



def get_peers(torrent):
	# udp_send(sock, connection_req(), torrent)
	resp = []
	for ann in torrent.announce_list:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.settimeout(4)

		connection_resp = parse_connection_resp(udp_send(sock, connection_req(), ann[0]))
		# connection_resp = parse_connection_resp(sock.recv(16))
		# announce_resp = parse_announce_pesp(udp_send(sock, a, torrent))
		announce_resp = parse_announce_pesp(udp_send(sock, announce_req(connection_resp['conn_id'], torrent), ann[0]))
		# announce_resp = parse_announce_pesp(sock.recv(2048))
		resp = resp + announce_resp['peer']
		print('found peers: ',len(resp))
	return resp


def resp_type(resp):
	t = int.from_bytes(resp['action'])
	if t == 0:
		return 'connect'
	elif t == 1:
		return 'announce'


def udp_send(sock, message, url):

	# except:
	# 	print("fail to get host ip")
	data = b''
	try:
		url = url_parse.urlparse(url)
		# try:
		host_ip = socket.gethostbyname(url.hostname)
		sock.sendto(message,(host_ip, url.port))
	except:
		print('failed to access peer: ',url)
	while True:
		try:
			buff = sock.recv(4096)
			if len(buff) <= 0:
				break
			data += buff
		except:
			# print('Timeout')
			break
	return data

def announce_req(connection_id, torrent, port=PORT):
	action = pack('>I', 1)
	transaction_id = pack('>I', random.randint(0, 100000))
	hash = torrent.info_hash
	id = get_id()
	downloaded = pack('>Q', 0)
	left = pack('>Q', 0)
	uploaded = pack('>Q', 0)
	event = pack('>I', 0)
	ip = pack('>I', 0)
	key = pack('>I', 0)
	num_want = pack('>i', -1)
	port = pack('>h', port)
	message = (connection_id + action + transaction_id + hash + id + downloaded +
	           left + uploaded + event + ip + key + num_want + port)
	return message


def parse_announce_pesp(resp):
	def extract_peers(data):
		peers = ([data[i:i + 6] for i in range(int(len(data) / 6))])
		return ([{'ip': socket.inet_ntoa(peer[:4]), 'port': peer[5] + peer[4] * 256} for peer in peers])

	return {
		'action': (resp[0:4]),
		'transaction': (resp[4:8]),
		'leech': (resp[12:16]),
		'seed': (resp[16:20]),
		'peer': extract_peers(resp[20:])
	}


def connection_req():
	conn_id = pack('>Q', 0x41727101980)
	action = pack('>I', 0)
	trans_id = pack('>I', random.randint(0, 100000))

	return conn_id + action + trans_id


def parse_connection_resp(resp):
	return {
		'action': resp[:4],
		'transaction': resp[4:8],
		'conn_id': resp[8:]
	}

