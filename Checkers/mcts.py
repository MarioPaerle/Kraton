import math
import random
import time
import pygame
from checkers import CheckersGame, Move, RED, BLACK, EMPTY
from renderer import CheckersRenderer


class MCTSNode:
    __slots__ = ("game", "move", "parent", "children", "wins", "visits", "untried_moves")

    def __init__(self, game: CheckersGame, move: Move = None, parent: "MCTSNode" = None):
        self.game          = game
        self.move          = move
        self.parent        = parent
        self.children:  list["MCTSNode"] = []
        self.wins:   float = 0.0
        self.visits: int   = 0
        self.untried_moves = game.get_legal_moves()

    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0

    def is_terminal(self) -> bool:
        return self.game.done

    def uct_score(self, c: float) -> float:
        return (self.wins / self.visits) + c * math.sqrt(math.log(self.parent.visits) / self.visits)

    def best_child(self, c: float) -> "MCTSNode":
        return max(self.children, key=lambda n: n.uct_score(c))

    def expand(self) -> "MCTSNode":
        move      = self.untried_moves.pop(random.randrange(len(self.untried_moves)))
        child_game = self.game.clone()
        child_game.apply_move(move)
        child     = MCTSNode(child_game, move, parent=self)
        self.children.append(child)
        return child

    def rollout(self, max_depth: int = 80) -> float:
        sim = self.game.clone()
        depth = 0
        while not sim.done and depth < max_depth:
            moves = sim.get_legal_moves()
            if not moves:
                break
            sim.apply_move(random.choice(moves))
            depth += 1
        return sim.get_result(BLACK)

    def backpropagate(self, result: float):
        self.visits += 1
        self.wins   += result
        if self.parent:
            self.parent.backpropagate(result)


class MCTS:
    def __init__(self, iterations: int = 800, c: float = 1.414, time_limit: float = None):
        self.iterations = iterations
        self.c          = c
        self.time_limit = time_limit

    def search(self, game: CheckersGame) -> Move:
        root      = MCTSNode(game.clone())
        deadline  = time.time() + self.time_limit if self.time_limit else None
        iters     = 0

        while True:
            if deadline and time.time() >= deadline:
                break
            if not deadline and iters >= self.iterations:
                break

            node = self._select(root)
            if not node.is_terminal():
                node = node.expand()
            result = node.rollout()
            node.backpropagate(result)
            iters += 1

        best = max(root.children, key=lambda n: n.visits)
        return best.move

    def _select(self, node: MCTSNode) -> MCTSNode:
        while not node.is_terminal():
            if not node.is_fully_expanded():
                return node
            node = node.best_child(self.c)
        return node


def run(mcts_iterations: int = 800, cpu_color: int = BLACK):
    game     = CheckersGame()
    renderer = CheckersRenderer(game)
    mcts     = MCTS(iterations=mcts_iterations)
    human    = RED if cpu_color == BLACK else BLACK

    selected    = None
    legal       = game.get_legal_moves()
    cpu_thinking = False
    status_font  = pygame.font.SysFont("arial", 18)

    def draw_status(text: str):
        surf = status_font.render(text, True, (255, 255, 255))
        renderer.screen.blit(surf, (8, 8))
        pygame.display.flip()

    running = True
    while running:
        renderer.render(selected, legal)

        if game.done:
            renderer.show_winner(game.winner)
            pygame.time.wait(3000)
            break

        turn_label = "Your turn (Red)" if game.turn == human else f"CPU thinking… ({mcts_iterations} iters)"
        draw_status(turn_label)

        if game.turn == cpu_color and not game.done:
            pygame.event.pump()
            move = mcts.search(game)
            game.apply_move(move)
            selected = None
            legal    = game.get_legal_moves()
            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset()
                    selected = None
                    legal    = game.get_legal_moves()
                if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    mcts_iterations = min(mcts_iterations + 200, 5000)
                    mcts = MCTS(iterations=mcts_iterations)
                if event.key == pygame.K_MINUS:
                    mcts_iterations = max(mcts_iterations - 200, 100)
                    mcts = MCTS(iterations=mcts_iterations)

            if event.type == pygame.MOUSEBUTTONDOWN and game.turn == human:
                r, c  = renderer.pixel_to_cell(*event.pos)
                piece = game.board[r][c]

                if selected is None:
                    if piece != EMPTY and (
                        (human == RED   and piece > 0) or
                        (human == BLACK and piece < 0)
                    ):
                        piece_moves = [m for m in legal if m.origin == (r, c)]
                        if piece_moves:
                            selected = (r, c)
                else:
                    move_made = next((m for m in legal if m.origin == selected and m.destination == (r, c)), None)

                    if move_made:
                        game.apply_move(move_made)
                        selected = None
                        legal    = game.get_legal_moves()
                    elif piece != EMPTY and (
                        (human == RED   and piece > 0) or
                        (human == BLACK and piece < 0)
                    ):
                        piece_moves = [m for m in legal if m.origin == (r, c)]
                        selected = (r, c) if piece_moves else None
                    else:
                        selected = None

        renderer.tick(60)

    renderer.quit()


if __name__ == "__main__":
    run(mcts_iterations=100)