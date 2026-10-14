"""Functional tests for GameEngine. Each docstring states the expected behaviour."""

import pytest

from game.game_engine import GameEngine, GameStateError, InvalidScoreError


# ---------- starting a game ----------
def test_new_engine_is_not_started(game):
    """A new engine has not started and is not game over."""
    status = game.get_game_status()
    assert status["status"] == "not_started"
    assert status["game_over"] is False


def test_start_game_sets_running_state(game):
    """start_game() moves the game to the running state."""
    game.start_game()
    assert game.get_game_status()["status"] == "running"


def test_initial_score_is_zero(running_game):
    """Score is 0 right after a game starts."""
    assert running_game.get_game_status()["score"] == 0


def test_start_twice_is_rejected(running_game):
    """Starting a game that is already running raises GameStateError."""
    with pytest.raises(GameStateError):
        running_game.start_game()


# ---------- updating the score ----------
def test_update_score_adds_points(running_game):
    """update_score(50) makes the score 50."""
    running_game.update_score(50)
    assert running_game.get_game_status()["score"] == 50


def test_update_score_accumulates(running_game):
    """Several updates add up to the correct total."""
    for points in (10, 20, 30):
        running_game.update_score(points)
    assert running_game.get_game_status()["score"] == 60


def test_zero_points_is_allowed(running_game):
    """Boundary: 0 points is valid and leaves the score unchanged."""
    running_game.update_score(0)
    assert running_game.get_game_status()["score"] == 0


@pytest.mark.severity("High")
def test_negative_score_is_rejected(running_game):
    """Negative points raise InvalidScoreError."""
    with pytest.raises(InvalidScoreError):
        running_game.update_score(-5)


@pytest.mark.parametrize("bad_value", [None, "10", 1.5, True, [5]])
def test_non_integer_points_are_rejected(running_game, bad_value):
    """Points that are not plain integers raise InvalidScoreError."""
    with pytest.raises(InvalidScoreError):
        running_game.update_score(bad_value)


def test_rejected_update_does_not_change_score(running_game):
    """A rejected score update leaves the existing score untouched."""
    running_game.update_score(40)
    with pytest.raises(InvalidScoreError):
        running_game.update_score("abc")
    assert running_game.get_game_status()["score"] == 40


def test_maximum_score_boundary(running_game):
    """Boundary: MAX_SCORE is accepted, one more point is rejected."""
    running_game.update_score(GameEngine.MAX_SCORE)
    assert running_game.get_game_status()["score"] == GameEngine.MAX_SCORE
    with pytest.raises(InvalidScoreError):
        running_game.update_score(1)


# ---------- invalid state transitions ----------
@pytest.mark.severity("High")
def test_update_score_before_start_is_rejected(game):
    """Scoring before the game has started raises GameStateError."""
    with pytest.raises(GameStateError):
        game.update_score(10)


@pytest.mark.severity("High")
def test_update_score_after_end_is_rejected(running_game):
    """Scoring after the game has ended raises GameStateError and keeps the score."""
    running_game.update_score(100)
    running_game.end_game()
    with pytest.raises(GameStateError):
        running_game.update_score(5)
    assert running_game.get_game_status()["score"] == 100


def test_end_game_before_start_is_rejected(game):
    """Ending a game that never started raises GameStateError."""
    with pytest.raises(GameStateError):
        game.end_game()


def test_end_game_twice_is_rejected(running_game):
    """Ending an already-ended game raises GameStateError."""
    running_game.end_game()
    with pytest.raises(GameStateError):
        running_game.end_game()


def test_start_after_end_requires_reset(running_game):
    """A finished game cannot be restarted until reset_game() is called."""
    running_game.end_game()
    with pytest.raises(GameStateError):
        running_game.start_game()


# ---------- ending and resetting ----------
def test_end_game_sets_game_over(running_game):
    """end_game() marks the game as ended and game_over True."""
    running_game.update_score(25)
    running_game.end_game()
    status = running_game.get_game_status()
    assert status["status"] == "ended"
    assert status["game_over"] is True
    assert status["score"] == 25


def test_reset_clears_score_and_state(running_game):
    """reset_game() returns score to 0 and clears game over."""
    running_game.update_score(70)
    running_game.end_game()
    running_game.reset_game()
    status = running_game.get_game_status()
    assert status["status"] == "not_started"
    assert status["score"] == 0
    assert status["game_over"] is False


def test_reset_on_fresh_engine_is_safe(game):
    """Resetting an engine that never started does not raise."""
    game.reset_game()
    assert game.get_game_status()["status"] == "not_started"


# ---------- repeated sessions ----------
def test_repeated_sessions_work_after_reset(game):
    """Three start/score/end/reset cycles each begin at 0 and finish correctly."""
    for session in range(1, 4):
        game.start_game()
        assert game.get_game_status()["score"] == 0
        game.update_score(10 * session)
        game.end_game()
        assert game.get_game_status()["score"] == 10 * session
        game.reset_game()
    status = game.get_game_status()
    assert status["sessions_played"] == 3
    assert status["high_score"] == 30


def test_high_score_survives_reset(game):
    """High score is kept after reset_game()."""
    game.start_game()
    game.update_score(99)
    game.end_game()
    game.reset_game()
    assert game.get_game_status()["high_score"] == 99


def test_status_is_a_copy(running_game):
    """Changing the dict returned by get_game_status() must not change the engine."""
    status = running_game.get_game_status()
    status["score"] = 999
    assert running_game.get_game_status()["score"] == 0
