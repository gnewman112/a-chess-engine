import chess as ch
import shelve
from typing import List, Tuple, Optional


class Node:
    """
    A Node represents a possible move. The Node.board will have the possible move in the move stack and therefore the
    score will represent the value to the opponent. In other words, the lower the score the better the move for the
    player considering it.

    Variable names:

    * 'mp' prefix represents the player who made the move (self.uci_move)
    * 'cp' prefix represents the current player which has legal moves in self.board.legal_moves
    * 'mp_board is the current board with a null turn pushed to the move stack. This is needed for attackers_mask and
      legal moves to produce correct results for the moving player (mp).
    """
    def __init__(self, shelved_scores: shelve.DbfilenameShelf, current_board: ch.Board = None, uci_move: ch.Move = None) -> None:
        self.shelf = shelved_scores
        self.uci_move = uci_move or ch.Move.null()
        self._children: List[Node] = []

        this_board = current_board or ch.Board()
        if this_board.is_legal(uci_move):
            self.board = this_board.copy()
            self.board.push(uci_move)
        elif uci_move is None:
            self.board = this_board
        else:
            raise ValueError('Board must be valid and uci_move must be a legal move')

        self.outcome = self.board.outcome()
        self.fen: str = self.board.fen()
        self.score = self.score_move()

    def __str__(self):
        if not self.uci_move:
            return '(root) {}'.format(self.fen)

        if self.score:
            return '({} for {}) {}'.format(self.uci_move, self.score, self.fen)
        else:
            return '({} not scored) {}'.format(self.uci_move, self.fen)

    def __repr__(self):
        if not self.uci_move:
            return 'move_node.Node({}, None)'.format(self.fen)
        if self.score:
            return 'move_node.Node({}, {}) Score: {}'.format(self.fen, self.uci_move, self.score)
        else:
            return 'move_node.Node({}, {})'.format(self.fen, self.uci_move)

    def score_move(self) -> int:
        if self.shelf.get(self.fen):
            return self.shelf[self.fen]

        if self.outcome != None:
            if self.outcome.winner == self.board.turn: return 5000 # This move causes current player to win
            elif self.outcome.winner != self.board.turn: return -5000 # This move causes the moving player to win
            else: return -4000 # This move causes a draw (excludes optional draws. see 'chess.Board.outcome()')

        mp_board = self.board.copy() # the current board offset by a null turn
        mp_board.push(ch.Move.null())

        score = 0
        for move in self.board.legal_moves:
            cp_piece_type = self.board.piece_type_at(move.from_square)
            cp_piece_moves_after = ch.popcount(
                self._attacks_mask_after(move.to_square, cp_piece_type, self.board.turn, self.board.occupied)
            )
            cp_square_defenders = ch.popcount(self.board.attackers_mask(self.board.turn, move.to_square)) - 1
            mp_square_defenders = ch.popcount(mp_board.attackers_mask(mp_board.turn, move.to_square))
            mp_piece_moves_before = ch.popcount(mp_board.attacks_mask(move.to_square)) # This is 0 if the square is not occupied

            score += (cp_square_defenders - mp_square_defenders) * (cp_piece_moves_after + mp_piece_moves_before)
        score += ch.popcount(self.board.occupied_co[self.board.turn]) \
                 - ch.popcount(self.board.occupied_co[~self.board.turn])

        self.shelf[self.fen] = score
        return score

    def get_move_w_debug(self, depth: int = 4) -> Tuple[List[int], List[ch.Move], int]:
        if self.outcome != None or depth < 1:
            return [self.score], [self.uci_move.uci()], 0
        else:  # get scores from each node and report the best for the active turn
            best_scores = [5000]
            best_index = 0
            best_moves = []
            for i in range(len(self.children)):
                node_scores, node_moves, _ = self.children[i].get_move_w_debug(depth - 1)
                if node_scores[0] < best_scores[0]:
                    best_scores = node_scores
                    best_index = i
                    best_moves = node_moves
            return [self.score] + best_scores, [self.uci_move.uci()] + best_moves, best_index

    def get_move(self, depth: int = 4) -> Tuple[int, int]:
        if self.outcome != None or depth < 1:
            return self.score, 0
        else:
            best_score = 5000
            best_index = 0
            for i in range(len(self.children)):
                child_score, child_index = self.children[i].get_move(depth - 1)
                if child_score < best_score:
                    best_score = child_score
                    best_index = i
            return self.score, best_index

    def _attacks_mask_after(self, square: ch.Square, piece_type: ch.PieceType,
                            color: ch.Color, occupied: ch.Bitboard) -> ch.Bitboard:
        '''
        This is similar to 'chess.BaseBoard.attacks_mask()' except 'square' can be empty. This allows simulating the
        attacks if a piece were there.

        :param square: A square to launch attacks from
        :param piece_type: The type of piece attacking
        :param color: The color of the piece attacking
        :param occupied: The occupied squares on the board
        :return: A bitboard of the piece's attacks
        '''
        def pawns_attack():
            return ch.BB_PAWN_ATTACKS[color][square]
        def knights_attack():
            return ch.BB_KNIGHT_ATTACKS[square]
        def kings_attack():
            return ch.BB_KING_ATTACKS[square]
        def other_attacks():
            attacks = 0
            if piece_type == 3 or piece_type == 5:
                attacks = ch.BB_DIAG_ATTACKS[square][ch.BB_DIAG_MASKS[square] & occupied]
            if piece_type == 4 or piece_type == 5:
                attacks |= (ch.BB_RANK_ATTACKS[square][ch.BB_RANK_MASKS[square] & occupied] |
                            ch.BB_FILE_ATTACKS[square][ch.BB_FILE_MASKS[square] & occupied])
            return attacks

        attack_functions = {
            1: pawns_attack,
            2: knights_attack,
            3: other_attacks,
            4: other_attacks,
            5: other_attacks,
            6: kings_attack
        }
        return attack_functions[piece_type]()

    @property
    def children(self) -> List:
        if self._children:
            return self._children
        else:
            for move in self.board.legal_moves:
                self._children.append(Node(self.shelf, self.board, move))
            return self._children


def print_board(print_list: List):
    """
    Prints a 8x8 grid of characters from a list 64 items long. Replaces '0' with '.'.

    :param print_list: A 64 item list of single characters or ints
    """
    print_string = []
    for square in ch.SQUARES_180:
        mask = ch.BB_SQUARES[square]
        print_string.append(str(print_list[square]) if print_list[square] != 0 else '.')

        if not mask & ch.BB_FILE_H:
            print_string.append(' ')
        else:
            print_string.append('\n')
    print(''.join(print_string))
