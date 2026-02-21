import numpy as np
from copy import deepcopy
from typing import Optional

RED   = 1
BLACK = -1
EMPTY = 0
RED_KING   = 2
BLACK_KING = -2
BOARD_SIZE = 10


class Move:
    def __init__(self, path: list[tuple[int, int]], captures: list[tuple[int, int]] = None):
        self.path     = path
        self.captures = captures or []

    @property
    def origin(self) -> tuple[int, int]:
        return self.path[0]

    @property
    def destination(self) -> tuple[int, int]:
        return self.path[-1]

    def __repr__(self):
        return f"Move({self.path}, captures={self.captures})"

    def __eq__(self, other):
        return self.path == other.path and self.captures == other.captures

    def __hash__(self):
        return hash((tuple(self.path), tuple(self.captures)))


class CheckersGame:
    def __init__(self):
        self.board  = self._init_board()
        self.turn   = RED
        self.winner = None
        self.done   = False
        self._no_capture_count = 0

    def _init_board(self) -> np.ndarray:
        board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.int8)
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if (row + col) % 2 == 1:
                    if row < (BOARD_SIZE-1) // 2:
                        board[row][col] = BLACK if row != 1 else BLACK_KING
                    elif row > (BOARD_SIZE+1) // 2:
                        board[row][col] = RED if row != BOARD_SIZE - 2 else RED_KING
        return board

    def reset(self) -> np.ndarray:
        self.__init__()
        return self.get_observation()

    def get_observation(self) -> np.ndarray:
        obs = np.zeros((4, BOARD_SIZE, BOARD_SIZE), dtype=np.float32)
        obs[0] = (self.board == RED).astype(np.float32)
        obs[1] = (self.board == BLACK).astype(np.float32)
        obs[2] = (self.board == RED_KING).astype(np.float32)
        obs[3] = (self.board == BLACK_KING).astype(np.float32)
        return obs

    def get_canonical_observation(self) -> np.ndarray:
        if self.turn == RED:
            return self.get_observation()
        flipped_board = -np.flip(self.board, axis=0)
        obs = np.zeros((4, BOARD_SIZE, BOARD_SIZE), dtype=np.float32)
        obs[0] = (flipped_board == RED).astype(np.float32)
        obs[1] = (flipped_board == BLACK).astype(np.float32)
        obs[2] = (flipped_board == RED_KING).astype(np.float32)
        obs[3] = (flipped_board == BLACK_KING).astype(np.float32)
        return obs

    def _is_king(self, piece: int) -> bool:
        return abs(piece) == 2

    def _get_directions(self, piece: int) -> list[tuple[int, int]]:
        if piece == RED:
            return [(-1, -1), (-1, 1)]
        if piece == BLACK:
            return [(1, -1), (1, 1)]
        return [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    def _in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def _get_capture_moves(self, board: np.ndarray, r: int, c: int, piece: int, visited: set) -> list[Move]:
        moves = []
        dirs  = self._get_directions(piece)
        for dr, dc in dirs:
            mid_r, mid_c = r + dr, c + dc
            end_r, end_c = r + 2 * dr, c + 2 * dc
            if not self._in_bounds(end_r, end_c):
                continue
            mid_piece = board[mid_r][mid_c]
            if mid_piece == EMPTY or np.sign(mid_piece) == np.sign(piece):
                continue
            if board[end_r][end_c] != EMPTY:
                continue
            cap_key = (mid_r, mid_c)
            if cap_key in visited:
                continue
            new_board     = board.copy()
            new_board[end_r][end_c]   = piece
            new_board[r][c]           = EMPTY
            new_board[mid_r][mid_c]   = EMPTY
            promoted = piece
            if piece == RED and end_r == 0:
                promoted = RED_KING
                new_board[end_r][end_c] = RED_KING
            elif piece == BLACK and end_r == BOARD_SIZE - 1:
                promoted = BLACK_KING
                new_board[end_r][end_c] = BLACK_KING
            further = self._get_capture_moves(new_board, end_r, end_c, promoted, visited | {cap_key})
            if further:
                for m in further:
                    moves.append(Move([(r, c)] + m.path, [(mid_r, mid_c)] + m.captures))
            else:
                moves.append(Move([(r, c), (end_r, end_c)], [(mid_r, mid_c)]))
        return moves

    def _get_moves_for_piece(self, board: np.ndarray, r: int, c: int) -> list[Move]:
        piece   = board[r][c]
        caps    = self._get_capture_moves(board, r, c, piece, set())
        if caps:
            return caps
        moves = []
        for dr, dc in self._get_directions(piece):
            nr, nc = r + dr, c + dc
            if self._in_bounds(nr, nc) and board[nr][nc] == EMPTY:
                moves.append(Move([(r, c), (nr, nc)]))
        return moves

    def get_legal_moves(self, board: Optional[np.ndarray] = None, turn: Optional[int] = None) -> list[Move]:
        board = board if board is not None else self.board
        turn  = turn  if turn  is not None else self.turn
        captures, non_captures = [], []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if np.sign(board[r][c]) != np.sign(turn) or board[r][c] == EMPTY:
                    continue
                for m in self._get_moves_for_piece(board, r, c):
                    (captures if m.captures else non_captures).append(m)
        return captures if captures else non_captures

    def apply_move(self, move: Move) -> tuple[np.ndarray, float, bool]:
        if self.done:
            raise RuntimeError("Game is over")
        had_capture = bool(move.captures)
        for cap in move.captures:
            self.board[cap[0]][cap[1]] = EMPTY
        piece = self.board[move.origin[0]][move.origin[1]]
        self.board[move.origin[0]][move.origin[1]] = EMPTY
        dr, dc = move.destination
        if piece == RED   and dr == 0:
            piece = RED_KING
        if piece == BLACK and dr == BOARD_SIZE - 1:
            piece = BLACK_KING
        self.board[dr][dc] = piece
        self._no_capture_count = 0 if had_capture else self._no_capture_count + 1
        reward = self._check_terminal()
        self.turn = -self.turn
        return self.get_observation(), reward, self.done

    def _check_terminal(self) -> float:
        opponent = -self.turn
        opp_pieces = np.sum(np.sign(self.board) == np.sign(opponent))
        if opp_pieces == 0 or not self.get_legal_moves(self.board, opponent):
            self.done   = True
            self.winner = self.turn
            return 1.0
        if self._no_capture_count >= 80:
            self.done   = True
            self.winner = 0
            return 0.0
        return 0.0

    def clone(self) -> "CheckersGame":
        return deepcopy(self)

    def action_to_move(self, action_idx: int, legal_moves: list[Move]) -> Move:
        return legal_moves[action_idx]

    def encode_move(self, move: Move) -> int:
        r, c   = move.origin
        dr, dc = move.destination
        return r * BOARD_SIZE ** 3 + c * BOARD_SIZE ** 2 + dr * BOARD_SIZE + dc

    def move_to_policy_index(self, move: Move, legal_moves: list[Move]) -> int:
        return legal_moves.index(move)

    def get_result(self, perspective: int) -> float:
        if self.winner is None or self.winner == 0:
            return 0.0
        return 1.0 if self.winner == perspective else -1.0

    def __repr__(self):
        symbols = {RED: "r", BLACK: "b", RED_KING: "R", BLACK_KING: "B", EMPTY: "."}
        rows = []
        for r in range(BOARD_SIZE):
            rows.append(" ".join(symbols[int(self.board[r][c])] for c in range(BOARD_SIZE)))
        return "\n".join(rows)