import pygame
import random
from env.Chessboard import Chessboard
from env.gobang import Game


class Gomoku():
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("五子棋")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('arial', 24)
        self.going = True
        self.g = Game()
        self.INFO = "P"
        self.chessboard = Chessboard()
        self.init_chessboard_list = []  # 在这里修改棋盘

    def init_chessboard(self):
        for (x, y) in self.init_chessboard_list:
            if self.chessboard.set_piece(x, y):
                pass
            else:
                print("init_chessboard failed... exit")
                self.going = False
                return

    def loop(self):
        while self.going:
            if not self.chessboard.game_over:
                self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()

    def update(self):

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.going = False
            elif (e.type == pygame.MOUSEBUTTONUP):

                x, y = self.chessboard.handle_key_event(e)
                print(x, y)
                if x > 0:
                    self.INFO = self.g.add(x, y)

    def draw(self):
        self.screen.fill((255, 255, 255))
        self.screen.blit(
            self.font.render("FPS: {0:.2F}".format(self.clock.get_fps()), True,
                             (0, 0, 0)), (10, 10))

        self.chessboard.draw(self.screen)

        self.screen.blit(
            self.font.render("RESULT: {}".format(self.INFO), True, (0, 0, 0)),
            (500, 10))

        pygame.display.update()


if __name__ == '__main__':
    game = Gomoku()
    game.init_chessboard()
    game.loop()
