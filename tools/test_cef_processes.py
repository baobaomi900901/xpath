from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools import cef_processes

SELECTED = Path(r"D:\code\xpath\CEF\dist\133\cef-shooting-range-133.exe")
OTHER_ROOT = Path(r"D:\other\CEF\dist\133\cef-shooting-range-133.exe")
UNSELECTED = Path(r"D:\code\xpath\CEF\dist\125\cef-shooting-range-125.exe")


class FakeClock:
    def __init__(self) -> None:
        self.value = 100.0

    def monotonic(self) -> float:
        return self.value


class FakeBackend:
    def __init__(self, clock: FakeClock, paths: dict[int, Path]) -> None:
        self.clock = clock
        self.paths = dict(paths)
        self.handles = {}
        self.closed = []
        self.terminated = []
        self.waits = []
        self.next_handle = 1
        self.changed_images = {}
        self.exits_on_open = set()
        self.exits_on_terminate = set()
        self.denied_termination = set()
        self.denied_open = set()
        self.wait_timeout = False
        self.spawn_after_first_termination = None
        self.spawn_on_open_race = None
        self.respawn = False

    def snapshot(self) -> list[tuple[int, str]]:
        self.clock.value += 0.01
        return [(pid, path.name) for pid, path in self.paths.items()]

    def open(self, pid: int, terminate: bool = False):
        if pid in self.exits_on_open:
            self.paths.pop(pid, None)
            if self.spawn_on_open_race is not None:
                new_pid, path = self.spawn_on_open_race
                self.paths[new_pid] = path
                self.spawn_on_open_race = None
            return None
        if terminate and pid in self.denied_open:
            raise PermissionError(f"Cannot open PID {pid} for termination")
        if pid not in self.paths:
            return None
        if terminate and pid in self.changed_images:
            self.paths[pid] = self.changed_images.pop(pid)
        handle = self.next_handle
        self.next_handle += 1
        self.handles[handle] = (pid, self.paths[pid], terminate)
        return handle

    def image(self, handle: int):
        return self.handles[handle][1]

    def terminate(self, handle: int, timeout: float) -> bool:
        pid, _, can_terminate = self.handles[handle]
        if not can_terminate:
            raise AssertionError("Termination must use a termination-capable handle")
        if pid in self.denied_termination:
            raise PermissionError(f"Cannot terminate PID {pid}")
        if pid in self.exits_on_terminate:
            self.paths.pop(pid, None)
            return False
        self.terminated.append(pid)
        previous_path = self.paths.pop(pid)
        if self.spawn_after_first_termination is not None:
            new_pid, path = self.spawn_after_first_termination
            self.paths[new_pid] = path
            self.spawn_after_first_termination = None
        if self.respawn:
            self.paths[pid + 1] = previous_path
            self.clock.value += 0.2
        return True

    def wait(self, handle: int, timeout: float) -> bool:
        self.waits.append((self.handles[handle][0], timeout))
        if self.wait_timeout:
            self.clock.value += timeout
            return False
        return True

    def close(self, handle: int) -> None:
        self.closed.append(handle)


class Win32RaceBackend(FakeBackend):
    """Exercise the production Win32 terminate/wait methods without OS kills."""

    def __init__(self, clock: FakeClock, exits_after_wait: bool, error: int = 5) -> None:
        super().__init__(clock, {10: SELECTED})
        self.wait_milliseconds = []
        self.termination_budgets = []
        self.native = cef_processes._WindowsBackend.__new__(cef_processes._WindowsBackend)
        self.native.ctypes = SimpleNamespace(
            get_last_error=lambda: error,
            WinError=lambda code: OSError(code, "access denied" if code == 5 else "invalid handle"),
        )

        def wait_for_single_object(handle: int, milliseconds: int) -> int:
            self.wait_milliseconds.append(milliseconds)
            if milliseconds == 0:
                return 0x102  # Process exiting, but not yet signalled.
            if exits_after_wait and milliseconds >= 20:
                self.clock.value += 0.02
                self.paths.pop(self.handles[handle][0], None)
                return 0  # Exit is now confirmed on the same held HANDLE.
            self.clock.value += milliseconds / 1000
            return 0x102

        self.native.kernel32 = SimpleNamespace(
            TerminateProcess=lambda handle, code: False,
            WaitForSingleObject=wait_for_single_object,
        )

    def terminate(self, handle: int, timeout: float) -> bool:
        self.termination_budgets.append(timeout)
        return self.native.terminate(handle, timeout)


class CleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()

    def run_cleanup(self, backend: FakeBackend, paths=None, timeout: float = 10.0):
        with patch.object(cef_processes, "_create_backend", return_value=backend), patch.object(
            cef_processes.time, "monotonic", side_effect=self.clock.monotonic
        ):
            return cef_processes.cleanup_cef_processes([SELECTED] if paths is None else paths, timeout)

    def assert_all_handles_closed(self, backend: FakeBackend) -> None:
        self.assertEqual(set(backend.handles), set(backend.closed))
        self.assertEqual(len(backend.closed), len(set(backend.closed)))

    def test_exact_paths_stop_browser_and_same_executable_workers(self) -> None:
        backend = FakeBackend(self.clock, {10: SELECTED, 11: SELECTED, 12: SELECTED})
        self.assertEqual([10, 11, 12], self.run_cleanup(backend))
        self.assertEqual([10, 11, 12], backend.terminated)
        self.assertFalse(backend.paths)
        self.assert_all_handles_closed(backend)

    def test_same_filename_other_root_unselected_versions_and_unrelated_children_survive(self) -> None:
        paths = {10: SELECTED, 20: OTHER_ROOT, 30: UNSELECTED, 40: Path(r"D:\unrelated\child.exe")}
        backend = FakeBackend(self.clock, paths)
        self.assertEqual([10], self.run_cleanup(backend))
        self.assertEqual({20, 30, 40}, set(backend.paths))
        self.assertEqual([10], backend.terminated)
        self.assert_all_handles_closed(backend)

    def test_canonical_matching_accepts_case_and_dot_segments(self) -> None:
        backend = FakeBackend(self.clock, {10: Path(str(SELECTED).upper())})
        selected_with_dots = SELECTED.parent / ".." / "133" / SELECTED.name
        self.assertEqual([10], self.run_cleanup(backend, [selected_with_dots]))
        self.assert_all_handles_closed(backend)

    def test_selected_multiple_versions_are_stopped(self) -> None:
        backend = FakeBackend(self.clock, {10: SELECTED, 20: UNSELECTED, 30: OTHER_ROOT})
        self.assertEqual([10, 20], self.run_cleanup(backend, [SELECTED, UNSELECTED]))
        self.assertEqual({30}, set(backend.paths))

    def test_reused_pid_is_revalidated_on_the_termination_handle(self) -> None:
        backend = FakeBackend(self.clock, {10: SELECTED})
        backend.changed_images[10] = OTHER_ROOT
        self.assertEqual([], self.run_cleanup(backend))
        self.assertFalse(backend.terminated)
        self.assertEqual(OTHER_ROOT, backend.paths[10])
        self.assert_all_handles_closed(backend)

    def test_process_exit_before_open_is_a_normal_race(self) -> None:
        backend = FakeBackend(self.clock, {10: SELECTED})
        backend.exits_on_open.add(10)
        self.assertEqual([], self.run_cleanup(backend))
        self.assertFalse(backend.terminated)
        self.assert_all_handles_closed(backend)

    def test_process_exit_before_terminate_is_a_normal_race(self) -> None:
        backend = FakeBackend(self.clock, {10: SELECTED})
        backend.exits_on_terminate.add(10)
        self.assertEqual([10], self.run_cleanup(backend))
        self.assertFalse(backend.terminated)
        self.assert_all_handles_closed(backend)

    def test_access_denied_is_reported_and_handles_are_closed(self) -> None:
        for failure in ("denied_open", "denied_termination"):
            backend = FakeBackend(self.clock, {10: SELECTED})
            getattr(backend, failure).add(10)
            with self.subTest(failure=failure), self.assertRaisesRegex(PermissionError, "10"):
                self.run_cleanup(backend)
            self.assert_all_handles_closed(backend)

    def test_wait_timeout_reports_pid_and_closes_the_handle(self) -> None:
        backend = FakeBackend(self.clock, {10: SELECTED})
        backend.wait_timeout = True
        with self.assertRaisesRegex(RuntimeError, "10"):
            self.run_cleanup(backend, timeout=1.0)
        self.assertLessEqual(backend.waits[0][1], 1.0)
        self.assert_all_handles_closed(backend)

    def test_win32_access_denied_exit_race_waits_until_same_handle_signals(self) -> None:
        backend = Win32RaceBackend(self.clock, exits_after_wait=True)
        try:
            stopped = self.run_cleanup(backend)
        except PermissionError as error:
            self.fail(f"WinError5 during process exit needs a bounded confirming wait: {error}")
        self.assertEqual([10], stopped)
        self.assertFalse(backend.paths)
        self.assertEqual(0, backend.wait_milliseconds[0])
        self.assertGreater(backend.wait_milliseconds[1], 0)
        self.assert_all_handles_closed(backend)

    def test_win32_genuine_access_denied_reports_pid_after_bounded_wait(self) -> None:
        backend = Win32RaceBackend(self.clock, exits_after_wait=False)
        with self.assertRaisesRegex(PermissionError, "PID 10"):
            self.run_cleanup(backend, timeout=0.1)
        self.assertEqual({10}, set(backend.paths))
        self.assertGreater(backend.wait_milliseconds[-1], 0)
        self.assertLessEqual(sum(backend.wait_milliseconds), 90)
        self.assertLessEqual(self.clock.value, 100.1)
        self.assert_all_handles_closed(backend)

    def test_win32_nonpermission_failure_is_not_treated_as_an_exit_race(self) -> None:
        backend = Win32RaceBackend(self.clock, exits_after_wait=True, error=6)
        with self.assertRaisesRegex(RuntimeError, "PID 10"):
            self.run_cleanup(backend)
        self.assertEqual([0], backend.wait_milliseconds)
        self.assertEqual({10}, set(backend.paths))
        self.assert_all_handles_closed(backend)

    def test_win32_exit_race_wait_uses_remaining_overall_deadline(self) -> None:
        backend = Win32RaceBackend(self.clock, exits_after_wait=True)
        try:
            stopped = self.run_cleanup(backend, timeout=0.05)
        except PermissionError as error:
            self.fail(f"A process exiting inside the remaining cleanup budget must succeed: {error}")
        self.assertEqual([10], stopped)
        self.assertLessEqual(backend.termination_budgets[0], 0.04)
        self.assertLessEqual(sum(backend.wait_milliseconds), 40)
        self.assertLess(self.clock.value, 100.05)
        self.assert_all_handles_closed(backend)

    def test_repeated_snapshot_catches_workers_spawned_during_cleanup(self) -> None:
        backend = FakeBackend(self.clock, {10: SELECTED})
        backend.spawn_after_first_termination = (11, SELECTED)
        self.assertEqual([10, 11], self.run_cleanup(backend))
        self.assertFalse(backend.paths)
        self.assert_all_handles_closed(backend)

    def test_repeated_snapshot_catches_workers_after_browser_exit_race(self) -> None:
        backend = FakeBackend(self.clock, {10: SELECTED})
        backend.exits_on_open.add(10)
        backend.spawn_on_open_race = (11, SELECTED)
        self.assertEqual([11], self.run_cleanup(backend))
        self.assertEqual([11], backend.terminated)
        self.assert_all_handles_closed(backend)

    def test_repeated_respawns_cannot_extend_the_overall_deadline(self) -> None:
        backend = FakeBackend(self.clock, {10: SELECTED})
        backend.respawn = True
        with self.assertRaisesRegex(RuntimeError, "timeout|超时"):
            self.run_cleanup(backend, timeout=0.5)
        self.assertLess(self.clock.value, 101.0)
        self.assert_all_handles_closed(backend)

    def test_empty_selection_does_not_initialize_windows_backend(self) -> None:
        with patch.object(cef_processes, "_create_backend", side_effect=AssertionError("backend")):
            self.assertEqual([], cef_processes.cleanup_cef_processes([]))

    def test_invalid_timeout_is_rejected_before_any_process_operations(self) -> None:
        for timeout in (0, -1, float("nan"), float("inf")):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                cef_processes.cleanup_cef_processes([SELECTED], timeout=timeout)


if __name__ == "__main__":
    unittest.main()
