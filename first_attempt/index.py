from tracker import get_peers
import download
import torr
from bcoding import bdecode

with open('../sintel.torrent', 'rb') as tor_file:
	# with open('cosmos-laundromat.torrent', 'rb') as tor_file:
	# with open('big-buck-bunny.torrent', 'rb') as tor_file:
	# with open('puppy.torrent', 'rb') as tor_file:

	torrent = bdecode(tor_file)
	torrent = torr.Torrent(torrent)

def unchoke_peers():

	peers = []
	while not peers:
		print('Looking for peers')
		peers = get_peers(torrent)
	print('Got ',len(peers),' num of peers')
	connections = []
	for p in peers:
		connections.append(download.connect(p, torrent))
	active_connecions = []
	for c in connections:
		if c and c[1] == 1:
			active_connecions.append(c[0])
	return active_connecions

unchoke_peers()