from agents.agents_cli import main as agents_main


def test_cli_run_once():
    rc = agents_main(["scheduler", "run-once"])
    assert rc == 0


def test_cli_start_and_stop():
    # start should return 0 quickly (background thread) and stop should succeed
    rc_start = agents_main(["scheduler", "start"])
    assert rc_start == 0
    rc_stop = agents_main(["scheduler", "stop"])
    assert rc_stop == 0
