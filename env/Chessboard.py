import pygame


class Chessboard:
    def __init__(self):
        self.grid_size = 26
        self.start_x, self.start_y = 30, 50
        self.edge_size = self.grid_size / 2
        self.grid_count = 15
        self.piece = 'b'
        self.winner = None
        self.game_over = False
        self.step = -1
        self.grid = []
        self.step_grid = []
        for i in range(self.grid_count):
            self.grid.append(list("." * self.grid_count))
            self.step_grid.append(list("." * self.grid_count))

    def handle_key_event(self, e):
        origin_x = self.start_x - self.edge_size
        origin_y = self.start_y - self.edge_size
        size = (self.grid_count - 1) * self.grid_size + self.edge_size * 2
        pos = pygame.mouse.get_pos()
        if (origin_x <= pos[0] <= origin_x + size) and \
                (origin_y <= pos[1] <= origin_y + size):

            x = pos[0] - origin_x
            y = pos[1] - origin_y
            r = int(y // self.grid_size)
            c = int(x // self.grid_size)
            print("x:", x, " y:", y, " r:", r, " c:", c)
            if self.set_piece(r, c):
                return r, c
        return (-1, -1)

    def set_piece(self, r, c):
        if self.grid[r][c] == '.':
            self.grid[r][c] = self.piece
            self.step += 1
            self.step_grid[r][c] = self.step
            if self.piece == 'b':
                self.piece = 'w'
            else:
                self.piece = 'b'

            return True
        return False

    def draw(self, screen):
        # 棋盤底色
        font = pygame.font.SysFont('arial', 12)
        pygame.draw.rect(screen, (185, 122, 87), [
            self.start_x - self.edge_size, self.start_y - self.edge_size,
            (self.grid_count - 1) * self.grid_size + self.edge_size * 2,
            (self.grid_count - 1) * self.grid_size + self.edge_size * 2
        ], 0)

        for r in range(self.grid_count):
            y = self.start_y + r * self.grid_size
            pygame.draw.line(screen, (0, 0, 0), [self.start_x, y], [
                self.start_x + self.grid_size * (self.grid_count - 1), y
            ], 2)

        for c in range(self.grid_count):
            x = self.start_x + c * self.grid_size
            pygame.draw.line(screen, (0, 0, 0), [x, self.start_y], [
                x, self.start_y + self.grid_size * (self.grid_count - 1)
            ], 2)

        for r in range(self.grid_count):
            for c in range(self.grid_count):
                piece = self.grid[r][c]
                if piece != '.':
                    if piece == 'b':
                        color = (0, 0, 0)
                        font_color = (255, 255, 255)
                    else:
                        color = (255, 255, 255)
                        font_color = (0, 0, 0)

                    x = self.start_x + c * self.grid_size
                    y = self.start_y + r * self.grid_size
                    # print("draw x: ", x, " draw y: ", y)
                    pygame.draw.circle(screen, color, [x, y],
                                       self.grid_size // 2)
                    if self.step_grid[r][c] > 99:
                        font_color = (255, 0, 0)
                        cur_step = '%02d' % (self.step_grid[r][c] - 100)
                    else:
                        cur_step = '%02d' % (self.step_grid[r][c])
                    position = font.render(cur_step, True, font_color)
                    screen.blit(position, [x - 6, y - 6])
