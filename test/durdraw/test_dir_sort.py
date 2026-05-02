import os
from types import SimpleNamespace

from durdraw.durdraw_ui_curses import UserInterface


def make_ui(sort_mode):
    ui = UserInterface.__new__(UserInterface)
    ui.appState = SimpleNamespace(usingDirMode=True, dirSort=sort_mode)
    return ui


def test_sort_local_names_by_name(tmp_path):
    assert make_ui("name").sortLocalNames(str(tmp_path), ["beta.ans", "Alpha.ans"]) == [
        "Alpha.ans",
        "beta.ans",
    ]


def test_sort_local_names_by_size_largest_first(tmp_path):
    small = tmp_path / "small.ans"
    large = tmp_path / "large.ans"
    small.write_text("x")
    large.write_text("xxxx")

    assert make_ui("size").sortLocalNames(str(tmp_path), ["small.ans", "large.ans"]) == [
        "large.ans",
        "small.ans",
    ]


def test_sort_local_names_by_mtime_newest_first(tmp_path):
    old = tmp_path / "old.ans"
    new = tmp_path / "new.ans"
    old.write_text("old")
    new.write_text("new")
    old_time = 1_700_000_000
    new_time = old_time + 60
    os.utime(old, (old_time, old_time))
    os.utime(new, (new_time, new_time))

    assert make_ui("mtime").sortLocalNames(str(tmp_path), ["old.ans", "new.ans"]) == [
        "new.ans",
        "old.ans",
    ]


def test_get_local_folders_keeps_parent_first_and_sorts_dirs(tmp_path):
    zed = tmp_path / "zed"
    alpha = tmp_path / "alpha"
    zed.mkdir()
    alpha.mkdir()

    assert make_ui("name").getLocalFolders(str(tmp_path)) == ["../", "alpha/", "zed/"]


def test_set_local_play_queue_tracks_selected_file_and_skips_dirs(tmp_path):
    folder = tmp_path / "folder"
    one = tmp_path / "one.ans"
    two = tmp_path / "two.ans"
    folder.mkdir()
    one.write_text("one")
    two.write_text("two")
    ui = make_ui("name")

    ui.setLocalPlayQueue(str(tmp_path), ["../", "folder/", "one.ans", "two.ans"], ["../", "folder/"], "two.ans")

    assert ui.appState.play_queue == [str(one), str(two)]
    assert ui.appState.play_queue_position == 1
    assert ui.appState.play_queue_direction == 0
    assert ui.appState.play_queue_auto_advance is False


def test_request_viewer_file_change_sets_direction_and_stops_viewer():
    ui = make_ui("name")
    ui.appState.play_queue = ["one.ans", "two.ans"]
    ui.appState.play_queue_position = 0
    ui.appState.play_queue_direction = 0
    ui.appState.topLine = 7
    ui.appState.firstCol = 4
    ui.playing = True

    assert ui.requestViewerFileChange(1) is True
    assert ui.appState.play_queue_direction == 1
    assert ui.playing is False
    assert ui.appState.topLine == 0
    assert ui.appState.firstCol == 0


def test_request_viewer_file_change_ignores_out_of_range_move():
    ui = make_ui("name")
    ui.appState.play_queue = ["one.ans", "two.ans"]
    ui.appState.play_queue_position = 0
    ui.appState.play_queue_direction = 0
    ui.appState.topLine = 7
    ui.appState.firstCol = 4
    ui.playing = True

    assert ui.requestViewerFileChange(-1) is False
    assert ui.appState.play_queue_direction == 0
    assert ui.playing is True
    assert ui.appState.topLine == 7
    assert ui.appState.firstCol == 4


def test_run_play_queue_loads_requested_next_file():
    ui = make_ui("name")
    ui.appState.play_queue = ["one.ans", "two.ans"]
    ui.appState.play_queue_position = 0
    ui.appState.play_queue_direction = 0
    ui.appState.play_queue_auto_advance = False
    ui.appState.durview_running = True
    loaded_positions = []

    def load_position():
        loaded_positions.append(ui.appState.play_queue_position)
        return True

    def enter_view_mode():
        if loaded_positions == [0]:
            ui.appState.play_queue_direction = 1
        else:
            ui.appState.durview_running = False

    ui.loadPlayQueuePosition = load_position
    ui.enterViewMode = enter_view_mode

    ui.runPlayQueue()

    assert loaded_positions == [0, 1]
