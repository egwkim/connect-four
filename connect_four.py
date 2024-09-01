import pickle
import random
import time

from types import GeneratorType

import pygame

pygame.init()

book = {}
try:
    with open('book.pkl', 'rb') as f:
        book = pickle.load(f)
except:
    pass

CELL_SIZE = 100
RADIUS = CELL_SIZE * 0.37
BOARD_WIDTH = 7
BOARD_HEIGHT = 6
WINDOW_WIDTH = BOARD_WIDTH * CELL_SIZE
WINDOW_HEIGHT = BOARD_HEIGHT * CELL_SIZE

COLOR = {
    'WHITE': (255, 255, 255),
    'BLACK': (0, 0, 0),
    'RED': (240, 60, 64),
    'YELLOW': (248, 248, 0),
    'BLUE': (78, 92, 199),
}

COLOR[0] = COLOR["WHITE"]
COLOR[1] = COLOR["YELLOW"]
COLOR[2] = COLOR["RED"]

CIRCLES = []
for i in range(3):
    CIRCLES.append(pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA))
    pygame.draw.circle(CIRCLES[i], COLOR[i], (CELL_SIZE // 2, CELL_SIZE // 2), RADIUS)

FPS = 60

FONT = pygame.font.SysFont(None, 64)

BATCH = int(1e4)

LOG = True


def log(*args, **kwargs):
    if LOG:
        print(*args, **kwargs)


def quit():
    # pygame.quit()
    raise


def bootstrap(f, stack=[]):
    def wrappedfunc(*args, **kwargs):
        if stack:
            return f(*args, **kwargs)
        else:
            to = f(*args, **kwargs)
            while True:
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        quit()
                        return False
                for _ in range(BATCH):
                    if type(to) is GeneratorType:
                        stack.append(to)
                        to = next(to)
                    else:
                        stack.pop()
                        if not stack:
                            break
                        to = stack[-1].send(to)
                else:
                    continue
                break
        return to

    return wrappedfunc


class ConnectFourBoard:
    def __init__(self, width=7, height=6):
        # Doesn't change after init
        self.width = width
        self.height = height
        self.cells = width * height
        self.symbols = ['.', 'O', 'X']
        self.max_depth = 9
        self.full = 0
        tmp = (1 << width) - 1
        for _ in range(height):
            self.full <<= width + 1
            self.full += tmp
        self.full_fours = 4 * width * height - 9 * (width + height) + 18

        # Can change during the game
        self.current = 0
        self.all = 0
        # turn = 1: first, -1: last
        self.turn = 1

        # Cache to reduce calculation
        # key: (current, all), value: evaluation
        self.cache = {}

        # Set after game ends
        self.finished = 0
        self.winner = 0

    def highest_blank(self, column):
        """
        Return the highest blank cell in the column
        If the column is full, return None
        """
        if (self.all >> ((self.width + 1) * (self.height) - column - 2)) & 1:
            return None

        # Lowest cell on the column
        cell = 1 << self.width - (column + 1)
        # Search one cell above until the cell is empty
        while self.all & cell:
            cell <<= self.width + 1

        return cell

    def move(self, column):
        """
        Make a move on the board

        0 <= column < board width

        Return False on fail.
        Return an integer (2**n) representing the move on success.
        """

        # 0 <= column < self.width
        if self.finished:
            # Game already finished
            return False

        selected = self.highest_blank(column)

        if selected is None:
            # Selected column is full
            return False

        # Make a move to the board
        self.all += selected
        self.current += selected

        # Check if the game is finished
        if self.check_win():
            # game finished with winner
            self.finished = True
            self.winner = self.turn
        elif self.all.bit_count() == self.cells:
            # draw
            self.finished = True
            self.winner = 0

        # Switch turn
        self.turn *= -1
        self.current ^= self.all

        return selected

    def undo(self, cell):
        if not self.all & cell:
            raise ValueError('Cannot undo empty cell')
        if self.current & cell:
            raise ValueError('Cannot undo opponent\'s piece')

        self.all -= cell
        self.current ^= self.all
        self.turn *= -1
        self.finished = False
        self.winner = 0

    def heuristic(self):
        # Heuristic function is not consistence
        # Only meaningful to compare positions
        # with same depth starting from same position
        def count_fours(c):
            x = c & (c >> 1)
            h = x & (x >> 2)

            x = c & (c >> self.width + 1)
            v = x & (x << 2 * (self.width + 1))

            x = c & (c >> self.width)
            d1 = x & (x << 2 * (self.width))

            x = c & c >> self.width + 2
            d2 = x & (x << 2 * (self.width + 2))
            return sum(map(lambda x: x.bit_count(), (h, v, d1, d2)))

        # Opponent inverse
        c_inv = self.full ^ self.current
        o_inv = c_inv ^ self.all

        h = self.turn * (count_fours(o_inv) - count_fours(c_inv)) / self.full_fours

        assert -1 < h < 1

        return h

    def best_move(self):
        m = book.get((self.current, self.all), None)
        if m is None:
            return self.search()[0]
        print(m)
        return m

    @bootstrap
    def search(self, depth=0, alpha=-3, beta=3):
        """
        Calculate the best move of the current position

        evaluation range: [-2, 2]
        0: draw, positive: first wins, negative: last wins
        |eval| > 1: forced win exists

        Return: (move, evaluation)
        """

        if depth == self.max_depth:
            yield None, self.heuristic()

        if depth == 0:
            self.cache = {}

        if (self.current, self.all) in self.cache:
            yield None, self.cache[(self.current, self.all)]

        sgn = self.turn

        best_eval = -sgn * 3
        best_move = None

        for i in range(7):
            m = self.move(i)
            if not m:
                continue

            if self.finished:
                result = self.winner * (1 + 1 / (depth + 1))
                self.undo(m)
                self.cache[(self.current, self.all)] = result
                yield i, result

            _, eval = yield self.search(depth + 1, alpha, beta)

            # Alpha beta pruning
            # Don't cache eval when pruning nodes
            if sgn == 1:
                if eval > beta:
                    self.undo(m)
                    yield i, eval
                alpha = max(eval, alpha)
            else:
                if eval < alpha:
                    self.undo(m)
                    yield i, eval
                beta = min(eval, beta)

            if depth == 0:
                log(i, eval)

            if eval * sgn > best_eval * sgn:
                best_eval = eval
                best_move = i

            self.undo(m)

        self.cache[(self.current, self.all)] = best_eval
        yield best_move, best_eval

    def check_win(self):
        # Return true if the current player has won
        c = self.current

        # Check if there are two stones in a row
        # and then check if there are two "two in a row" in a row
        return (
            (x := c & (c >> 1)) & (x >> 2)
            or (x := c & (c >> self.width + 1)) & (x >> 2 * (self.width + 1))
            or (x := c & (c >> self.width)) & (x >> 2 * self.width)
            or (x := c & (c >> self.width + 2)) & (x >> 2 * (self.width + 2))
        )

    def __str__(self):
        s = ""
        last = self.current
        if self.turn == 1:
            last ^= self.all
        all = self.all
        for row in range(self.height):
            for cell in range(self.width):
                s = self.symbols[(last & 1) + (all & 1)] + s
                last >>= 1
                all >>= 1
            s = "\n" + s
            last >>= 1
            all >>= 1
        return s

    def draw(self, window, highlight=None):
        window.fill(COLOR['BLUE'])
        last = self.current
        if self.turn == 1:
            last ^= self.all
        all = self.all

        y = self.height - 1
        for row in range(self.height):
            x = self.width - 1
            for cell in range(self.width):
                window.blit(
                    CIRCLES[(last & 1) + (all & 1)],
                    (CELL_SIZE * x, CELL_SIZE * y),
                )
                x -= 1
                last >>= 1
                all >>= 1
            y -= 1
            last >>= 1
            all >>= 1

        if self.finished:
            text = FONT.render('GAME OVER', True, COLOR['BLACK'])
            x = (WINDOW_WIDTH - text.get_width()) // 2
            y = (WINDOW_HEIGHT - text.get_height()) // 2
            window.blit(text, (x, y))

        elif highlight != None:
            # don't highlight if column is full
            cell = self.highest_blank(highlight)
            if cell is None:
                return

            cell_idx = cell.bit_length() - 1
            x = self.width - 1 - cell_idx % (self.width + 1)
            y = self.height - 1 - cell_idx // (self.width + 1)

            CIRCLES[self.turn].set_alpha(64)
            window.blit(
                CIRCLES[self.turn],
                (CELL_SIZE * x, CELL_SIZE * y),
            )
            CIRCLES[self.turn].set_alpha(255)


def main():
    gui()
    # cli()


def cli():
    while True:
        mode = input('Number of players (1 or 2): ')
        if mode == '1':
            turn = int(input('Select turn (1 or -1): '))
            if turn == 1 or turn == -1:
                break
        elif mode == '2':
            break

    board = ConnectFourBoard(BOARD_WIDTH, BOARD_HEIGHT)
    if mode == '1':
        if turn == -1:
            print(board)
            board.move(board.best_move())
        while True:
            print(board)
            move = -1
            while not (0 <= move < board.width):
                move = int(input("Input move (0-6): "))
            board.move(move)
            if board.finished:
                print(board)
                break
            print(board)
            board.move(board.best_move())
            if board.finished:
                print(board)
                break

    else:
        while True:
            print(board)
            move = int(input("Input move (0-6): "))
            board.move(move)
            if board.finished:
                print(board)
                break


def gui():
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    board = ConnectFourBoard()

    def menu():
        window.fill(COLOR['WHITE'])
        title = FONT.render('CONNECT FOUR', True, COLOR['BLACK'])
        text_1p = FONT.render('1p', True, COLOR['BLACK'])
        text_2p = FONT.render('2p', True, COLOR['BLACK'])

        window.blit(
            title,
            (
                WINDOW_WIDTH / 2 - title.get_width() / 2,
                WINDOW_HEIGHT / 4 - title.get_height() / 2,
            ),
        )

        window.blit(
            text_1p,
            (
                WINDOW_WIDTH / 4 - text_1p.get_width() / 2,
                WINDOW_HEIGHT / 2 - text_1p.get_height() / 2,
            ),
        )

        window.blit(
            text_2p,
            (
                WINDOW_WIDTH * 3 / 4 - text_2p.get_width() / 2,
                WINDOW_HEIGHT / 2 - text_2p.get_height() / 2,
            ),
        )
        pygame.display.flip()
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    quit()
                    return False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.pos[0] < WINDOW_WIDTH / 2:
                        return 1
                    else:
                        return 2

    def get_col(pos):
        # return column by x position
        # clip value for safety
        return min(BOARD_WIDTH - 1, max(0, pos // CELL_SIZE))

    def game(players=2):
        if players == 1:
            player_turn = random.choice((1, -1))
        prev_time = time.time()

        selected = None
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    quit()
                    return
                elif event.type == pygame.MOUSEMOTION:
                    if players == 2 or player_turn == board.turn:
                        # change selected cell when mouse moves
                        selected = get_col(event.pos[0])
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if players == 2 or player_turn == board.turn:
                        selected = get_col(event.pos[0])
                        board.move(selected)
                        selected = None
                        prev_time = time.time()
                elif event.type == pygame.WINDOWLEAVE:
                    selected = None

            board.draw(window, selected)
            pygame.display.flip()

            if players == 1 and player_turn != board.turn and not board.finished:
                m = board.best_move()
                log(time.time() - prev_time)
                board.move(m)
                # board.best_move()

            clock.tick(FPS)

    players = menu()
    if not players:
        # Quit event occured, exit program
        return

    game(players)


if __name__ == '__main__':
    main()
