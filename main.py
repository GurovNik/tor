import time
import peers_manager
import pieces_manager
import torrent
import tracker
import os
import message

torrent = torrent.Torrent().load_from_path("sintel.torrent")
tracker = tracker.Tracker(torrent)
pieces_manager = pieces_manager.PiecesManager(torrent)
peers_manager = peers_manager.PeersManager(torrent, pieces_manager)
peers_manager.start()

peers_dict = tracker.get_peers_from_trackers()
peers_manager.add_peers(peers_dict.values())

while not pieces_manager.all_pieces_completed():
    if not peers_manager.has_unchoked_peers():
        time.sleep(1)
        continue

    for piece in pieces_manager.pieces:
        index = piece.piece_index

        if pieces_manager.pieces[index].is_full:
            continue

        peer = peers_manager.get_random_peer_having_piece(index)
        if not peer:
            continue

        pieces_manager.pieces[index].update_block_status()

        data = pieces_manager.pieces[index].get_empty_block()
        if not data:
            continue

        piece_index, block_offset, block_length = data
        piece_data = message.Request(piece_index, block_offset, block_length).to_bytes()
        peer.send_to_peer(piece_data)
        print((pieces_manager.complete_pieces/pieces_manager.number_of_pieces))

    time.sleep(0.1)

peers_manager.is_active = False
os._exit(0)


