import pygame
from checkers import CheckersGame, RED, BLACK, EMPTY
from renderer import CheckersRenderer


def run():
    game     = CheckersGame()
    renderer = CheckersRenderer(game)
    selected = None
    legal    = game.get_legal_moves()

    running = True
    while running:
        renderer.render(selected, legal)
        renderer.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game.reset()
                selected = None
                legal    = game.get_legal_moves()

            if event.type == pygame.MOUSEBUTTONDOWN and not game.done:
                r, c = renderer.pixel_to_cell(*event.pos)
                piece = game.board[r][c]

                if selected is None:
                    if piece != EMPTY and (
                        (game.turn == RED   and piece > 0) or
                        (game.turn == BLACK and piece < 0)
                    ):
                        piece_moves = [m for m in legal if m.origin == (r, c)]
                        if piece_moves:
                            selected = (r, c)
                else:
                    move_made = None
                    for m in legal:
                        if m.origin == selected and m.destination == (r, c):
                            move_made = m
                            break

                    if move_made:
                        game.apply_move(move_made)
                        selected = None
                        legal    = game.get_legal_moves()
                        if game.done:
                            renderer.render()
                            renderer.show_winner(game.winner)
                            pygame.time.wait(3000)
                            running = False
                    elif piece != EMPTY and (
                        (game.turn == RED   and piece > 0) or
                        (game.turn == BLACK and piece < 0)
                    ):
                        piece_moves = [m for m in legal if m.origin == (r, c)]
                        selected = (r, c) if piece_moves else None
                    else:
                        selected = None

    renderer.quit()


if __name__ == "__main__":
    run()