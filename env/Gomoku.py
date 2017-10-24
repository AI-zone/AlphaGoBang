import pygame
import random
from env.Chessboard import Chessboard


class Gomoku():

    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("五子棋")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('arial', 24)
        self.going = True
        self.ai_turn = True  # 可修改先后顺序
        self.chessboard = Chessboard()
        self.step = 0

    def loop(self):
        while self.going:
            if not self.chessboard.game_over:
                self.update()
                # print("loop...")
                self.check_win()
            self.draw()
            self.clock.tick(60)

        pygame.quit()

    def update(self):
        if self.ai_turn:
            # self.chessboard.set.piece(x, y), 传入坐标即可
            if self.chessboard.set_piece(random.randint(0, 14), random.randint(0, 14)):
                self.step += 1
                self.ai_turn = False
        else:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.going = False
                elif e.type == pygame.MOUSEBUTTONDOWN and not self.ai_turn:
                    if self.chessboard.handle_key_event(e):
                        self.ai_turn = True
                        self.step += 1

    def check_win(self):
        # 这部分需要服务端传递一个参数，表面游戏是否结束
        # 若结束 设置：
        # self.chessboard.game_over = True
        # self.chessboard.winner = 'b' or 'w'

        if(self.step > 15):
            self.chessboard.game_over = True
            self.chessboard.winner = 'b'

    def draw(self):
        self.screen.fill((255, 255, 255))
        self.screen.blit(self.font.render("FPS: {0:.2F}".format(
            self.clock.get_fps()), True, (0, 0, 0)), (10, 10))

        self.chessboard.draw(self.screen)
        if self.chessboard.game_over:
            self.screen.blit(self.font.render("{0} Win".format(
                "Black" if self.chessboard.winner == 'b' else "White"),
                                              True, (0, 0, 0)), (500, 10))

        pygame.display.update()


if __name__ == '__main__':
    game = Gomoku()
    game.loop()
