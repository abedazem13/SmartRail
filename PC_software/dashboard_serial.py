"""One serial reader for all browser tabs; bounded framing and reconnects."""

import threading
import time
from collections.abc import Callable

import serial

from dashboard_model import DemoModel


class LineBuffer:
    """Discard overlong lines, including their tail; preserve partial reads."""
    def __init__(self, limit: int = 4096):
        self.limit = limit
        self.buffer = bytearray()
        self.dropping = False

    def feed(self, data: bytes) -> list[str]:
        lines = []
        for byte in data:
            if byte == 10:
                if not self.dropping:
                    lines.append(self.buffer.decode("utf-8", errors="replace").rstrip("\r"))
                self.buffer.clear()
                self.dropping = False
            elif not self.dropping:
                self.buffer.append(byte)
                if len(self.buffer) > self.limit:
                    self.buffer.clear()
                    self.dropping = True
        return lines


class SerialWorker(threading.Thread):
    def __init__(self, model: DemoModel, factory: Callable = serial.Serial, retry_s: float = 1.0):
        super().__init__(name="smartrail-serial", daemon=True)
        self.model = model
        self.factory = factory
        self.retry_s = retry_s
        self._stop_requested = threading.Event()

    def stop(self) -> None:
        self._stop_requested.set()
        if self.is_alive():
            self.join(timeout=3)

    @staticmethod
    def _close(handle) -> None:
        if handle is not None:
            try:
                handle.close()
            except (OSError, serial.SerialException):
                pass

    def run(self) -> None:
        handle = None
        generation = -1
        retry_at = 0.0
        frames = LineBuffer()
        try:
            while not self._stop_requested.is_set():
                current, mode, port = self.model.serial_config()
                if current != generation:
                    self._close(handle)
                    handle, frames, retry_at = None, LineBuffer(), 0.0
                    generation = current
                if mode != "hybrid":
                    self._stop_requested.wait(0.05)
                    continue
                try:
                    if handle is None and time.monotonic() >= retry_at:
                        handle = self.factory(port, 115200, timeout=0.1)
                        if not self.model.transport(generation, True):
                            self._close(handle)
                            handle = None
                            continue
                    if handle is not None:
                        data = handle.read(min(max(handle.in_waiting, 1), 4096))
                        for line in frames.feed(data):
                            self.model.feed(generation, line)
                except (serial.SerialException, OSError, ValueError) as exc:
                    self._close(handle)
                    handle, frames = None, LineBuffer()
                    retry_at = time.monotonic() + self.retry_s
                    self.model.transport(generation, False,
                                         f"Cannot read {port}: {exc}. Retrying. Close other serial monitors.")
                self._stop_requested.wait(0.02)
        finally:
            self._close(handle)