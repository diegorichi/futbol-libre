import glob
import os
import shutil
import signal
import subprocess
import tempfile
import threading
import time


class ProcessRunner:
    def __init__(self, project_root, status, log_location=None):
        self.project_root = project_root
        self.status = status
        self.pid_file = os.path.join(project_root, "data", ".update-futbollibre.pid")
        self.log_file = os.path.join(log_location or project_root, "log_scrap.log")
        os.makedirs(os.path.dirname(self.pid_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        self._start_lock = threading.Lock()

    def start(self, script_name, arguments=None):
        with self._start_lock:
            if self.is_running():
                return False
            self._clear_log()
            if not self.status.start(f"Ejecutando {script_name}..."):
                return False
            thread = threading.Thread(
                target=self._run,
                args=(script_name, list(arguments or [])),
                daemon=True,
            )
            thread.start()
            return True

    def recover(self):
        if self.is_running():
            self.status.restore(self.tail_output(), "Actualización detectada en curso.")

    def stop(self):
        with self._start_lock:
            pids = set(self._find_process_pids())
            pid_file_pid = self._read_pid()
            if pid_file_pid is not None:
                pids.add(pid_file_pid)
            pids = {pid for pid in pids if self._is_update_process(pid)}
            if not pids:
                return False

            own_session_id = os.getsid(0)
            session_ids = {
                session_id
                for pid in pids
                if (session_id := self._session_id(pid)) not in {None, own_session_id}
            }
            for session_id in session_ids:
                self._terminate_session(session_id)
            for pid in pids:
                if self._session_id(pid) not in session_ids:
                    self._stop_pid(pid, signal.SIGTERM)

            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and any(self._pid_exists(pid) for pid in pids):
                time.sleep(0.1)
            for pid in pids:
                if self._pid_exists(pid):
                    self._stop_pid(pid, signal.SIGKILL)
                self._remove_pid(pid)
            self.status.append("--- Proceso detenido por el usuario ---")
            self.status.finish(False, "Proceso detenido por el usuario.")
            return True

    def tail_output(self, max_lines=300):
        try:
            with open(self.log_file, encoding="utf-8", errors="replace") as log_file:
                return log_file.readlines()[-max_lines:]
        except FileNotFoundError:
            return []

    def is_running(self):
        pid = self._read_pid()
        if pid is None:
            pid = self._find_process_pid()
            if pid is None:
                return False
            self._write_pid(pid)
            return True
        try:
            os.kill(pid, 0)
        except (ProcessLookupError, PermissionError, OSError):
            self._remove_pid(pid)
            return False

        command = self._process_command(pid)
        if command and "update-futbollibre.sh" in command:
            return True
        self._remove_pid(pid)
        pid = self._find_process_pid()
        if pid is None:
            return False
        self._write_pid(pid)
        return True

    def _run(self, script_name, arguments):
        script_path = os.path.join(self.project_root, script_name)
        process = None
        try:
            process = subprocess.Popen(
                ["bash", script_path, *arguments],
                stdout=open(self.log_file, "a", encoding="utf-8", buffering=1),
                stderr=subprocess.STDOUT,
                cwd=self.project_root,
                start_new_session=True,
            )
            self._write_pid(process.pid)
            return_code = process.wait()
            success = return_code == 0
            message = "Terminado." if success else f"Falló con código {return_code}."
            self.status.append(
                "--- Proceso finalizado con éxito ---" if success
                else f"--- El script reportó un fallo (Código {return_code}) ---"
            )
            self.status.finish(success, message)
        except Exception as error:
            self.status.append(f"Error interno: {error}")
            self.status.finish(False, str(error))
        finally:
            if process is not None:
                self._terminate_session(process.pid)
                self._remove_pid(process.pid)

    def _read_pid(self):
        try:
            with open(self.pid_file, encoding="utf-8") as pid_file:
                return int(pid_file.read().strip())
        except (FileNotFoundError, ValueError, OSError):
            return None

    def _is_update_process(self, pid):
        return "update-futbollibre.sh" in self._process_command(pid)

    def _stop_pid(self, pid, signal_number):
        try:
            process_group = os.getpgid(pid)
            if process_group == pid and process_group != os.getpgrp():
                os.killpg(process_group, signal_number)
            else:
                self._signal_process_tree(pid, signal_number)
        except (ProcessLookupError, OSError):
            pass

    def _terminate_session(self, session_id, grace_seconds=5):
        if session_id == os.getsid(0):
            return
        self._signal_session(session_id, signal.SIGTERM)
        deadline = time.monotonic() + grace_seconds
        while time.monotonic() < deadline and self._session_pids(session_id):
            time.sleep(0.1)
        if self._session_pids(session_id):
            self._signal_session(session_id, signal.SIGKILL)
        self._cleanup_browser_profiles(session_id)

    @staticmethod
    def _cleanup_browser_profiles(session_id):
        pattern = os.path.join(
            tempfile.gettempdir(),
            f"futbol-chrome-{session_id}-*",
        )
        for profile_dir in glob.glob(pattern):
            if os.path.isdir(profile_dir):
                shutil.rmtree(profile_dir, ignore_errors=True)

    @staticmethod
    def _session_id(pid):
        try:
            return os.getsid(pid)
        except (ProcessLookupError, PermissionError, OSError):
            return None

    @staticmethod
    def _session_pids(session_id):
        try:
            result = subprocess.run(
                ["ps", "-axo", "pid=,sid="],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return []
        pids = []
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) != 2:
                continue
            try:
                pid, current_session_id = int(fields[0]), int(fields[1])
            except ValueError:
                continue
            if current_session_id == session_id:
                pids.append(pid)
        return pids

    @classmethod
    def _signal_session(cls, session_id, signal_number):
        for pid in reversed(cls._session_pids(session_id)):
            try:
                os.kill(pid, signal_number)
            except ProcessLookupError:
                pass

    @staticmethod
    def _pid_exists(pid):
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError, OSError):
            return False

    def _clear_log(self):
        with open(self.log_file, "w", encoding="utf-8"):
            pass

    def _signal_process_tree(self, root_pid, signal_number):
        descendants = self._descendant_pids(root_pid)
        for pid in reversed(descendants):
            try:
                os.kill(pid, signal_number)
            except ProcessLookupError:
                pass
        try:
            os.kill(root_pid, signal_number)
        except ProcessLookupError:
            pass

    @staticmethod
    def _descendant_pids(root_pid):
        children = {}
        try:
            result = subprocess.run(
                ["ps", "-axo", "pid=,ppid="],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return []
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) != 2:
                continue
            try:
                pid, parent_pid = int(fields[0]), int(fields[1])
            except ValueError:
                continue
            children.setdefault(parent_pid, []).append(pid)

        descendants = []
        pending = list(children.get(root_pid, []))
        while pending:
            pid = pending.pop()
            descendants.append(pid)
            pending.extend(children.get(pid, []))
        return descendants

    def _write_pid(self, pid):
        with open(self.pid_file, "w", encoding="utf-8") as pid_file:
            pid_file.write(str(pid))

    def _remove_pid(self, pid):
        try:
            if self._read_pid() == pid:
                os.remove(self.pid_file)
        except FileNotFoundError:
            pass

    @staticmethod
    def _process_command(pid):
        try:
            result = subprocess.run(
                ["ps", "-p", str(pid), "-o", "command="],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return ""
        return result.stdout.strip()

    @staticmethod
    def _find_process_pid():
        pids = ProcessRunner._find_process_pids()
        return pids[0] if pids else None

    @staticmethod
    def _find_process_pids():
        try:
            result = subprocess.run(
                ["ps", "-axo", "pid=,command="],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return []
        pids = []
        for line in result.stdout.splitlines():
            fields = line.strip().split(None, 1)
            if len(fields) == 2 and "update-futbollibre.sh" in fields[1]:
                try:
                    pids.append(int(fields[0]))
                except ValueError:
                    continue
        return pids
