"""A tiny, text-only game simulation used as the system under test (SUT).

This file knows NOTHING about the QA framework. It only uses the standard
`logging` module, so the QA code can capture its application events.
"""

import logging

logger = logging.getLogger("gametestpro.game")


class GameStateError(Exception):
    """Raised when an operation is not allowed in the current game state."""


class InvalidScoreError(ValueError):
    """Raised when a score update has an invalid value."""


class GameEngine:
    MAX_SCORE = 1_000_000  # upper limit, used for boundary testing

    NOT_STARTED = "not_started"
    RUNNING = "running"
    ENDED = "ended"

    def __init__(self):
        self._status = self.NOT_STARTED
        self._score = 0
        self._game_over = False
        self._sessions_played = 0
        self._high_score = 0

    # ---- public API -------------------------------------------------
    def start_game(self):
        if self._status == self.RUNNING:
            raise GameStateError("Game is already running")
        if self._status == self.ENDED:
            raise GameStateError("Game has ended; call reset_game() before starting again")
        self._status = self.RUNNING
        self._sessions_played += 1
        logger.info("Game started (session #%d)", self._sessions_played)

    def update_score(self, points):
        self._require_running()
        self._validate_points(points)
        new_score = self._score + points
        if new_score > self.MAX_SCORE:
            raise InvalidScoreError(f"Score would exceed maximum of {self.MAX_SCORE}")
        self._score = new_score
        logger.debug("Score updated to %d", self._score)

    def end_game(self):
        if self._status != self.RUNNING:
            raise GameStateError("Cannot end a game that is not running")
        self._status = self.ENDED
        self._game_over = True
        self._high_score = max(self._high_score, self._score)
        logger.info("Game ended with score %d", self._score)

    def reset_game(self):
        """Back to a fresh state. Session count and high score are kept."""
        self._status = self.NOT_STARTED
        self._score = 0
        self._game_over = False
        logger.info("Game reset")

    def get_game_status(self):
        return {
            "status": self._status,
            "score": self._score,
            "game_over": self._game_over,
            "sessions_played": self._sessions_played,
            "high_score": self._high_score,
        }

    # ---- internal checks (small methods so they are easy to explain) --
    def _require_running(self):
        if self._status != self.RUNNING:
            raise GameStateError(f"Cannot update score while game is '{self._status}'")

    def _validate_points(self, points):
        # bool is a subclass of int in Python, so reject it explicitly
        if isinstance(points, bool) or not isinstance(points, int):
            raise InvalidScoreError(f"Points must be an integer, got {type(points).__name__}")
        if points < 0:
            raise InvalidScoreError("Points cannot be negative")
