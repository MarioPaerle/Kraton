import pygame
from checkers import CheckersGame, Move, RED, BLACK, RED_KING, BLACK_KING, EMPTY, BOARD_SIZE

WINDOW_SIZE = 640
CELL = WINDOW_SIZE // BOARD_SIZE
PIECE_RADIUS = CELL // 2 - 6
CROWN_FONT_SIZE = 20

PALETTE = {
    "light": (240, 217, 181),
    "dark": (181, 136, 99),
    "red": (200, 50, 50),
    "red_king": (220, 90, 90),
    "black": (30, 30, 30),
    "black_king": (80, 80, 80),
    "highlight": (100, 220, 100, 160),
    "selected": (255, 220, 0, 180),
    "bg": (20, 20, 20),
    "text": (255, 255, 255),
}


class CheckersRenderer:
    def __init__(self, game: CheckersGame):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption("Checkers")
        self.clock = pygame.time.Clock()
        self.game = game
        self.font = pygame.font.SysFont("arial", CROWN_FONT_SIZE, bold=True)
        self.overlay = pygame.Surface((CELL, CELL), pygame.SRCALPHA)

    def cell_to_pixel(self, r: int, c: int) -> tuple[int, int]:
        return c * CELL + CELL // 2, r * CELL + CELL // 2

    def pixel_to_cell(self, x: int, y: int) -> tuple[int, int]:
        return y // CELL, x // CELL

    def draw_board(self):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                color = PALETTE["light"] if (r + c) % 2 == 0 else PALETTE["dark"]
                pygame.draw.rect(self.screen, color, (c * CELL, r * CELL, CELL, CELL))

    def draw_highlights(self, cells: list[tuple[int, int]], color_key: str):
        self.overlay.fill((0, 0, 0, 0))
        col = PALETTE[color_key]
        pygame.draw.rect(self.overlay, col, (0, 0, CELL, CELL))
        for r, c in cells:
            self.screen.blit(self.overlay, (c * CELL, r * CELL))

    def draw_piece(self, r: int, c: int, piece: int):
        x, y = self.cell_to_pixel(r, c)
        is_king = abs(piece) == 2
        if piece == RED or piece == RED_KING:
            base = PALETTE["red_king"] if is_king else PALETTE["red"]
            shadow = (120, 20, 20)
        else:
            base = PALETTE["black_king"] if is_king else PALETTE["black"]
            shadow = (0, 0, 0)
        pygame.draw.circle(self.screen, shadow, (x + 3, y + 3), PIECE_RADIUS)
        pygame.draw.circle(self.screen, base, (x, y), PIECE_RADIUS)
        pygame.draw.circle(self.screen, (255, 255, 255, 60), (x, y), PIECE_RADIUS, 2)
        if is_king:
            crown = self.font.render("K", True, (255, 215, 0))
            self.screen.blit(crown, crown.get_rect(center=(x, y)))

    def draw_pieces(self):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = self.game.board[r][c]
                if piece != EMPTY:
                    self.draw_piece(r, c, piece)

    def render(self, selected: tuple[int, int] = None, legal_moves: list[Move] = None):
        self.screen.fill(PALETTE["bg"])
        self.draw_board()
        if selected and legal_moves:
            dests = [m.destination for m in legal_moves if m.origin == selected]
            self.draw_highlights([selected], "selected")
            self.draw_highlights(dests, "highlight")
        self.draw_pieces()
        pygame.display.flip()

    def show_winner(self, winner: int):
        msg = "Draw!" if winner == 0 else ("Red wins!" if winner == RED else "Black wins!")
        surf = self.font.render(msg, True, PALETTE["text"])
        rect = surf.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
        bg = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        self.screen.blit(bg, (rect.x - 10, rect.y - 10))
        self.screen.blit(surf, rect)
        pygame.display.flip()

    def tick(self, fps: int = 60):
        self.clock.tick(fps)

    def quit(self):
        pygame.quit()
