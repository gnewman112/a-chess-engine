import time
from move_node import Node
import shelve
import chess
from timing_functions import time_score, time_search


DEPTH = 3


def prompt_move(moves, len_moves) -> int:
    print(['{}. {}'.format(index, move) for index, move in enumerate(moves)])
    choice: str = str(input('Select a move by number from the list or type its uci:  '))
    print()

    try:
        move = int(choice)
        if move >= len_moves:
            print('Selected move {}. Move must be less than {} to be valid.'.format(move, num_moves))
            move = prompt_move(moves, len_moves)
    except ValueError:
        if choice in moves:
            move = moves.index(choice)
        else:
            print('Selected move {} is not a legal move. Please enter another move from the following list.'
                  .format(choice))
            move = prompt_move(moves, len_moves)
    return move


if __name__ == '__main__':
    with shelve.open('shelf/dev_scores') as shelved_scores:
        root: Node = Node(shelved_scores)

        human = input('Play as ("0" for white, "1" for black): ') in {'0'}
        print()

        while True:
            legal_moves = [move.uci() for move in root.board.legal_moves]
            num_moves = len(legal_moves)
            if not num_moves:
                break

            print(root.board, '\n')
            if root.board.turn == human:
                my_choice = prompt_move(legal_moves, num_moves)
                root = root.children[my_choice]
            else:
                start = time.time()
                ai_scores, ai_moves, ai_index = root.get_move_w_debug(DEPTH)
                end = time.time()
                print('Evaluation time: {}s'.format(round(end - start, 7)))

                root = root.children[ai_index]
                print("(Debug:", ai_scores, ai_moves, ai_index, ')\n')
    print(root.board)
    print([move.uci() for move in root.board.move_stack])
