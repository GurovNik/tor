import math
import hashlib
import time
from bcoding import bencode, bdecode
import os


class Torrent(object):
    def __init__(self):
        self.torrent_file = {}
        self.total_length = 0
        self.piece_length = 0
        self.pieces = 0
        self.info_hash = ''
        self.peer_id = ''
        self.announce_list = ''
        self.file_names = []
        self.number_of_pieces = 0

    def load_from_path(self, path):
        with open(path, 'rb') as file:
            contents = bdecode(file)
        self.torrent_file = contents
        self.piece_length = self.torrent_file['info']['piece length']
        self.pieces = self.torrent_file['info']['pieces']
        self.info_hash = hashlib.sha1(bencode(self.torrent_file['info'])).digest()
        self.peer_id = self.generate_peer_id()
        self.announce_list = self.get_trakers()
        self.init_files()
        self.number_of_pieces = math.ceil(self.total_length / self.piece_length)
        return self

    def init_files(self):
        path = self.torrent_file['info']['name']
        if 'files' in self.torrent_file['info']:
            if not os.path.exists(path):
                os.mkdir(path)

            for file in self.torrent_file['info']['files']:
                path_file = os.path.join(path, *file["path"])
                if not os.path.exists(os.path.dirname(path_file)):
                    os.makedirs(os.path.dirname(path_file))
                self.file_names.append({"path": path_file , "length": file["length"]})
                self.total_length += file["length"]
        else:
            self.file_names.append({"path": path , "length": self.torrent_file['info']['length']})
            self.total_length = self.torrent_file['info']['length']

    def get_trakers(self):
        if 'announce-list' in self.torrent_file:
            return self.torrent_file['announce-list']
        else:
            return [[self.torrent_file['announce']]]

    def generate_peer_id(self):
        seed = str(time.time())
        return hashlib.sha1(seed.encode('utf-8')).digest()
