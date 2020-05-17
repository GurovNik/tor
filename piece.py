import hashlib
import math
import time
from pubsub import pub
from enum import Enum

BLOCK_SIZE = 2 ** 14


class State(Enum):
    FREE = 0
    PENDING = 1
    FULL = 2


class Block():
    def __init__(self, state=State.FREE, block_size=BLOCK_SIZE, data=b'', last_seen=0):
        self.state: State = state
        self.block_size = block_size
        self.data = data
        self.last_seen = last_seen



class Piece(object):
    def __init__(self, piece_index, piece_size, piece_hash):
        self.piece_index = piece_index
        self.piece_size = piece_size
        self.piece_hash = piece_hash
        self.is_full = False
        self.files = []
        self.raw_data = b''
        self.number_of_blocks = int(math.ceil(float(piece_size) / BLOCK_SIZE))
        self.blocks = []
        self._init_blocks()

    def update_block_status(self):
        for i, block in enumerate(self.blocks):
            if block.state == State.PENDING and (time.time() - block.last_seen) > 5:
                self.blocks[i] = Block()

    def set_block(self, offset, data):
        index = int(offset / BLOCK_SIZE)        #todo как так
        if not self.is_full and not self.blocks[index].state == State.FULL:
            self.blocks[index].data = data
            self.blocks[index].state = State.FULL

    def get_block(self, block_offset, block_length):
        return self.raw_data[block_offset:block_length]

    def get_empty_block(self):
        if self.is_full:
            return None

        for block_index, block in enumerate(self.blocks):
            if block.state == State.FREE:
                self.blocks[block_index].state = State.PENDING
                self.blocks[block_index].last_seen = time.time()
                return self.piece_index, block_index * BLOCK_SIZE, block.block_size
        return None

    def are_all_blocks_full(self):
        for block in self.blocks:
            if block.state == State.FREE or block.state == State.PENDING:
                return False
        return True

    def set_to_full(self):
        data = self._merge_blocks()
        if not self._valid_blocks(data):
            self._init_blocks()
            return False
        self.is_full = True
        self.raw_data = data
        self._write_piece_on_disk()
        pub.sendMessage('PiecesManager.PieceCompleted', piece_index=self.piece_index)

        return True

    def _init_blocks(self):
        self.blocks = []
        if self.number_of_blocks > 1:
            for i in range(self.number_of_blocks):
                self.blocks.append(Block())
            if (self.piece_size % BLOCK_SIZE) > 0:
                self.blocks[self.number_of_blocks - 1].block_size = self.piece_size % BLOCK_SIZE
        else:
            self.blocks.append(Block(block_size=int(self.piece_size)))

    def _write_piece_on_disk(self):
        for file in self.files:
            path_file = file["path"]
            file_offset = file["fileOffset"]
            piece_offset = file["pieceOffset"]
            length = file["length"]

            try:
                f = open(path_file, 'r+b')
            except IOError:
                f = open(path_file, 'wb')
            except Exception:
                return

            f.seek(file_offset)
            f.write(self.raw_data[piece_offset:piece_offset + length])
            f.close()

    def _merge_blocks(self):
        buf = b''
        for block in self.blocks:
            buf += block.data
        return buf

    def _valid_blocks(self, piece_raw_data):
        piece_data = hashlib.sha1(piece_raw_data).digest()
        if piece_data == self.piece_hash:
            return True
        return False
