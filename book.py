# Generate book using existing connect4 solver
# https://github.com/PascalPons/connect4/

import subprocess
import pickle

from connect_four import ConnectFourBoard


BOARD_WIDTH = 7
BOARD_HEIGHT = 6

PROTOCOL = 5

# key: (board.current, board.all)
# value: best_move
book = {(0, 0): 3}


def gen_book(best_turn, max_depth=18):
    p = subprocess.Popen(
        ('./c4solver.exe', '-a'),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    board = ConnectFourBoard(BOARD_WIDTH, BOARD_HEIGHT)
    moves = []
    if best_turn == 1:
        book[(board.current, board.all)] = 3
        board.move(3)
        moves.append(3)

    def best():
        p.stdin.write((''.join(str(m + 1) for m in moves)).encode() + b'\n')
        p.stdin.flush()
        o = p.stdout.readline()
        evals = map(int, o.split()[1:])
        best_m = 0
        best_e = next(evals)
        for m in range(1, 7):
            e = next(evals)
            if e == 100:
                continue
            elif e > best_e:
                best_m, best_e = m, e

        return best_m

    def step():
        if len(moves) == max_depth:
            return
        if board.turn == best_turn:
            best_move = book.get((board.current, board.all), None)
            if best_move is None:
                best_move = best()
                book[(board.current, board.all)] = best_move
            moves.append(best_move)
            m = board.move(best_move)
            if not m:
                moves.pop()
                return
            if not board.finished:
                step()
            moves.pop()
            board.undo(m)
        else:
            for i in range(7):
                moves.append(i)
                m = board.move(i)
                if not m:
                    moves.pop()
                    continue
                if not board.finished:
                    step()
                moves.pop()
                board.undo(m)

    try:
        step()
    except:
        print(board)

    p.terminate()


def main():
    global book
    try:
        with open('book.pkl', 'rb') as f:
            book = pickle.load(f)
    except:
        pass
    gen_book(1)
    gen_book(-1)

    with open('book.pkl', 'wb') as f:
        pickle.dump(book, f, PROTOCOL)


if __name__ == '__main__':
    main()
