import math


import hashlib
from bcoding import bencode, bdecode
import os
import random
user_id = None


class Torrent(object):
	def __init__(self, torrent):
		self.torrent_file = torrent
		self.total_length: int = 0
		self.piece_length = torrent['info']['piece length']
		self.pieces = torrent['info']['pieces']
		self.info_hash = self.get_info_hash()
		self.peer_id = self.get_id()
		self.announce_list = self.get_trakers()
		self.file_names = []
		self.init_files()
		self.number_of_pieces = math.ceil(self.total_length / self.piece_length)


	def init_files(self):
		root = self.torrent_file['info']['name']

		if 'files' in self.torrent_file['info']:
			if not os.path.exists(root):
				os.mkdir(root, 0o0766)

			for file in self.torrent_file['info']['files']:
				path_file = os.path.join(root, *file["path"])

				if not os.path.exists(os.path.dirname(path_file)):
					os.makedirs(os.path.dirname(path_file))

				self.file_names.append({"path": path_file, "length": file["length"]})
				self.total_length += file["length"]

		else:
			self.file_names.append({"path": root, "length": self.torrent_file['info']['length']})
			self.total_length = self.torrent_file['info']['length']

	def get_trakers(self):
		if 'announce-list' in self.torrent_file:
			return self.torrent_file['announce-list']
		else:
			return [[self.torrent_file['announce']]]

	def get_info_hash(self):
		raw_info_hash = (bencode(self.torrent_file['info']))
		hash = hashlib.sha1(raw_info_hash).digest()

		return hash

	def get_id(self):
		global user_id
		if not user_id:
			user_id = bytearray(random.getrandbits(8) for _ in range(20))
			user_id[0:7] = str('nekitos').encode()
		return user_id
