"""Run launchers without a shell and incrementally read their file-backed logs."""

import codecs
from dataclasses import dataclass, field
from datetime import datetime
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class Job:
    id: str
    label: str
    command: List[str]
    cwd: Path
    log_path: Path
    state: str = "running"
    returncode: Optional[int] = None
    _process: Any = field(default=None, repr=False)
    _offset: int = field(default=0, repr=False)
    _decoder: Any = field(default_factory=lambda: codecs.getincrementaldecoder("utf-8")("replace"), repr=False)


class Runner:
    """Own process bookkeeping, never process termination or GUI resources."""

    READ_SIZE = 64 * 1024

    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir).resolve()
        self.jobs = {}  # type: Dict[str, Job]

    def start(self, id: str, label: str, command: List[str], cwd: Path) -> Job:
        if id in self.jobs and self.jobs[id].state == "running":
            raise ValueError("{} is already running".format(id))
        if not isinstance(command, list) or not command or any(not isinstance(token, str) for token in command):
            raise ValueError("command must be a nonempty argument list")
        if not command[0].strip() or any("\x00" in token for token in command):
            raise ValueError("command contains an invalid executable or NUL character")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        safe_id = re.sub(r"[^\w.-]", "_", id).strip(".")[:60] or "job"
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        log_path = self.log_dir / "{}-{}-{}.log".format(safe_id, stamp, uuid4().hex[:8])
        env = os.environ.copy()
        env.update(PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONUNBUFFERED="1")
        cwd = Path(cwd).resolve()
        # Popen duplicates this file handle into the child. Closing our handle
        # keeps the GUI independent; no pipe can break when the GUI exits.
        with log_path.open("wb") as output:
            try:
                process = subprocess.Popen(
                    list(command), cwd=str(cwd), shell=False,
                    stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                    env=env, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
                )
            except OSError as exc:
                raise OSError("Cannot start {} ({!r}): {}".format(label, command[0], exc)) from exc
        job = Job(id=id, label=label, command=list(command), cwd=cwd, log_path=log_path, _process=process)
        self.jobs[id] = job
        return job

    def poll(self) -> List[Dict[str, Any]]:
        """Read at most one chunk per job; report completion after the final tail."""
        events = []
        for job in self.jobs.values():
            if job.state != "running":
                continue
            returncode = job._process.poll()
            with job.log_path.open("rb") as stream:
                stream.seek(job._offset)
                chunk = stream.read(self.READ_SIZE)
                job._offset += len(chunk)
                drained = job._offset >= os.fstat(stream.fileno()).st_size
            finished = returncode is not None and drained
            output = job._decoder.decode(chunk, final=finished)
            if output:
                events.append({"id": job.id, "kind": "output", "text": output,
                               "state": job.state, "returncode": job.returncode})
            if finished:
                job.returncode = returncode
                job.state = "succeeded" if returncode == 0 else "failed"
                events.append({"id": job.id, "kind": "status",
                               "text": "{}: {} (exit {})".format(job.label, job.state, returncode),
                               "state": job.state, "returncode": returncode})
        return events
