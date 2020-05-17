import hashlib
import json
from bcoding import bencode, bdecode

def size(torrent):
	size = sum([l['length'] for l in torrent['info']['files']]) if 'files' in torrent['info'] else torrent['info']['length']
	return size.to_bytes(4, 'big')

def info_hash(torrent):
	raw_info_hash = (bencode(torrent['info']))
	hash = hashlib.sha1(raw_info_hash).digest()

	return hash
