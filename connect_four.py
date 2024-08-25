import pygame
import itertools
import random
import time

pygame.init()

CELL_SIZE = 100
RADIUS = CELL_SIZE * 0.37
BOARD_WIDTH = 7
BOARD_HEIGHT = 6
WINDOW_WIDTH = BOARD_WIDTH * CELL_SIZE
WINDOW_HEIGHT = BOARD_HEIGHT * CELL_SIZE
EMPTY = 0
FIRST = 1
LAST = 2

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


class ConnectFourBoard:
    def __init__(self, width=7, height=6):
        self.width = width
        self.height = height
        self.board = [[0 for x in range(width)] for y in range(height)]
        self.turn = 1
        self.ply = 0
        self.finished = False
        self.winner = 0
        self.symbols = ['.', 'O', 'X']

    def move(self, column):
        if self.finished:
            return False
        if column < 0 or column >= self.width:
            return False
        if self.board[0][column] != 0:
            return False

        for row in range(self.height - 1, -1, -1):
            if self.board[row][column] == 0:
                self.board[row][column] = self.turn
                break
        self.ply += 1
        self.turn = 3 - self.turn

        self.finished = self.ply >= self.width * self.height or self.check_win()
        return True

    def undo(self, column):
        for row in range(self.height):
            if self.board[row][column] == 0:
                continue
            elif self.board[row][column] == self.turn:
                raise ValueError('Cannot undo opponent\'s piece')
            else:
                self.board[row][column] = 0
                self.ply -= 1
                self.turn = 3 - self.turn
                self.finished = False
                break
        else:
            raise ValueError('Cannot undo empty column')

    def best_move(self, depth=5):
        # return: (move, evaluation)
        # evaluation
        # 0: draw, 1: 1 wins, 2: 2 wins
        if depth == 0:
            return -1, 0

        best_eval = 3 - self.turn
        best_move = -1

        candidates = []

        for i in range(7):
            if not self.move(i):
                continue

            if self.finished:
                if self.check_win():
                    # return won player
                    self.undo(i)
                    return i, self.turn
                else:
                    # board full, draw
                    self.undo(i)
                    return i, 0

            _, eval = self.best_move(depth - 1)

            # self.turn is switched here
            if eval == 3 - self.turn:
                # winning move
                best_eval = eval
                best_move = i
                self.undo(i)
                break

            if best_eval == eval:
                candidates.append(i)

            elif best_eval == self.turn and eval == 0:
                best_eval = eval
                best_move = i
                candidates = [i]

            # restore board
            self.undo(i)

        if best_eval != self.turn:
            best_move = random.choice(candidates)
        return best_move, best_eval

    def check_win(self):
        for row in range(self.height):
            for column in range(self.width):
                if self.board[row][column] != 0:
                    if (
                        self.check_horizontal(row, column)
                        or self.check_vertical(row, column)
                        or self.check_diagonal1(row, column)
                        or self.check_diagonal2(row, column)
                    ):
                        self.winner = self.board[row][column]
                        return True
        return False

    def check_horizontal(self, row, column):
        for i in range(4):
            if (
                column + i >= self.width
                or self.board[row][column + i] != self.board[row][column]
            ):
                return False
        return True

    def check_vertical(self, row, column):
        for i in range(4):
            if (
                row + i >= self.height
                or self.board[row + i][column] != self.board[row][column]
            ):
                return False
        return True

    def check_diagonal1(self, row, column):
        for i in range(4):
            if (
                row + i >= self.height
                or column + i >= self.width
                or self.board[row + i][column + i] != self.board[row][column]
            ):
                return False
        return True

    def check_diagonal2(self, row, column):
        for i in range(4):
            if (
                row + i >= self.height
                or column - i < 0
                or self.board[row + i][column - i] != self.board[row][column]
            ):
                return False
        return True

    def __str__(self):
        s = ""
        for row in self.board:
            for cell in row:
                s += self.symbols[cell]
            s += "\n"
        return s

    def draw(self, window, highlight=None):
        window.fill(COLOR['BLUE'])
        for i, j in itertools.product(range(BOARD_WIDTH), range(BOARD_HEIGHT)):
            window.blit(
                CIRCLES[self.board[j][i]],
                (CELL_SIZE * i, CELL_SIZE * j),
            )

        if self.finished:
            text = FONT.render('GAME OVER', True, COLOR['BLACK'])
            x = (WINDOW_WIDTH - text.get_width()) // 2
            y = (WINDOW_HEIGHT - text.get_height()) // 2
            window.blit(text, (x, y))

        elif highlight != None:
            # don't highlight if column is full
            if self.board[0][highlight]:
                return

            # find lowest blank cell in highlighted column
            for i in range(self.height - 1, -1, -1):
                if self.board[i][highlight] == 0:
                    break
            CIRCLES[self.turn].set_alpha(64)
            window.blit(
                CIRCLES[self.turn],
                (CELL_SIZE * highlight, CELL_SIZE * i),
            )
            CIRCLES[self.turn].set_alpha(255)


def main():
    gui()
    # cli()


def cli():
    while True:
        mode = input('Number of players (1 or 2): ')
        if mode == '1':
            turn = int(input('Select turn (1 or 2): '))
            if turn == 1 or turn == 2:
                break
        elif mode == '2':
            break
    if mode == '1':
        board = ConnectFourBoard(BOARD_WIDTH, BOARD_HEIGHT)
        if turn == 2:
            print(board)
            board.move(board.best_move()[0])
        while True:
            print(board)
            move = int(input("Input move (0-6): "))
            board.move(move)
            if board.finished:
                print(board)
                break
            print(board)
            board.move(board.best_move()[0])
            if board.finished:
                print(board)
                break

    else:
        board = ConnectFourBoard(BOARD_WIDTH, BOARD_HEIGHT)
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
                    pygame.quit()
                    return
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
            player_turn = random.randint(1, 2)
        prev_time = time.time()

        selected = None
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
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
                board.move(board.best_move()[0])

            clock.tick(FPS)

    players = menu()
    game(players)


if __name__ == '__main__':
    main()
