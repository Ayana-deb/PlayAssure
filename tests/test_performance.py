"""Tests for the performance module (statistics maths and benchmark behaviour)."""

import time

import pytest

from qa.performance import benchmark, load_benchmarks, run_game_benchmarks, save_benchmarks, summarize


def test_summarize_calculates_correct_statistics():
    """Known timings (1s, 2s, 3s) give avg 2000ms, min 1000ms, max 3000ms, total 6000ms."""
    result = summarize("demo", [1.0, 2.0, 3.0])
    assert result["executions"] == 3
    assert result["average_ms"] == pytest.approx(2000)
    assert result["min_ms"] == pytest.approx(1000)
    assert result["max_ms"] == pytest.approx(3000)
    assert result["total_ms"] == pytest.approx(6000)


def test_summarize_rejects_empty_list():
    """No timings means nothing to summarize."""
    with pytest.raises(ValueError):
        summarize("demo", [])


def test_benchmark_runs_requested_number_of_times():
    """The operation is called exactly `runs` times."""
    calls = []
    result = benchmark("count", lambda _: calls.append(1), runs=25)
    assert len(calls) == 25
    assert result["executions"] == 25


def test_benchmark_measures_real_time():
    """A function that sleeps 2ms must show an average of at least 0.5ms."""
    result = benchmark("sleepy", lambda _: time.sleep(0.002), runs=5)
    assert result["average_ms"] >= 0.5


def test_benchmark_values_are_consistent():
    """min <= average <= max and total is about average * executions."""
    result = benchmark("consistent", lambda _: sum(range(100)), runs=50)
    assert result["min_ms"] <= result["average_ms"] <= result["max_ms"]
    assert result["total_ms"] == pytest.approx(result["average_ms"] * result["executions"], rel=0.01)


def test_benchmark_rejects_zero_runs():
    """runs=0 is invalid."""
    with pytest.raises(ValueError):
        benchmark("none", lambda _: None, runs=0)


def test_game_benchmarks_cover_expected_operations():
    """Game benchmark reports start_game, update_score and full_session."""
    data = run_game_benchmarks(runs=20)
    names = [r["operation"] for r in data["results"]]
    assert names == ["start_game", "update_score", "full_session"]
    assert all(r["executions"] == 20 for r in data["results"])
    assert "Not cloud" in data["note"]


def test_save_and_load_roundtrip(tmp_path):
    """Saved benchmark data can be loaded back unchanged."""
    data = run_game_benchmarks(runs=5)
    path = save_benchmarks(data, tmp_path / "perf.json")
    assert load_benchmarks(path) == data


def test_load_missing_file_returns_none(tmp_path):
    """A missing benchmark file is not an error."""
    assert load_benchmarks(tmp_path / "nope.json") is None
