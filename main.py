import os
import json
import hashlib
from datetime import datetime
import time
import getpass
from pathlib import Path
import threading


def _get_file_hash(file_path):
    """Отримує хеш файлу"""
    try:
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        print(f"Помилка при читанні файлу {file_path}: {e}")
        return None


class FileWatcher:
    def __init__(self, path_to_watch, file_types=None, history_file="history.json"):
        """
        path_to_watch: шлях до файлу або папки
        file_types: список розширень файлів для відстеження (наприклад: ['.txt', '.doc', '.pdf'])
        """
        self.path_to_watch = Path(path_to_watch)
        self.file_types = file_types
        self.history_file = history_file
        self.last_states = self._get_directory_state()
        self.history = []
        self._load_history()
        self.stop_event = threading.Event()  # Add stop_event

    def _load_history(self):
        # Load history from file
        if os.path.exists(self.history_file):
            with open(self.history_file, "r", encoding="utf-8") as f:
                self.history = json.load(f)
                if not isinstance(self.history, list):
                    self.history = []
        else:
            print("bad with history")
            self.history = []

    def _save_history(self):
        # Save history to file
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def _get_directory_state(self):
        """Отримує стан всіх файлів у директорії"""
        states = {}

        if not self.path_to_watch.exists():
            return states

        files_to_check = [self.path_to_watch] if self.path_to_watch.is_file() else self.path_to_watch.rglob("*")
        try:
            for file_path in files_to_check:
                if file_path.is_file() and self._should_watch_file(file_path):
                    if file_state := self._get_file_state(file_path):
                        states[str(file_path)] = file_state
        except Exception as e:
            print(f"Помилка при скануванні директорії: {e}")

        return states

    def _should_watch_file(self, file_path):
        if self.file_types is None:
            return True
        return file_path.suffix.lower() in self.file_types

    def _get_file_state(self, file_path):
        # Get file state
        try:
            if not os.path.exists(file_path):
                return None

            return {
                "hash": _get_file_hash(file_path),
                "file": str(file_path).split("\\")[-1],
            }
        except Exception as e:
            print(f"Помилка при отриманні стану файлу {file_path}: {e}")
            return None

    def _print_startup_info(self):
        """Виводить початкову інформацію про відстеження"""
        print(f"Починаю відстеження файлу: {self.path_to_watch}")
        if self.file_types:
            print(f"Відстежую файли з розширеннями: {', '.join(self.file_types)}")
        print("Натисніть Ctrl+C для завершення")

    def _process_change(self, file_path):
        """Обробляє окрему зміну файлу"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        change_record = {
            "file": str(file_path).split("\\")[-1],
            "time": timestamp,
            "user": getpass.getuser(),
        }

        self.history.append(change_record)
        self._save_history()
        print(f"[{timestamp}] {file_path}")

    def watch(self, interval=1):
        """Основна функція відстеження змін"""
        self._print_startup_info()

        try:
            while not self.stop_event.is_set():
                try:
                    self._check_changes()
                    time.sleep(interval)
                except Exception as e:
                    print(f"Помилка під час відстеження: {e}")
                    time.sleep(interval)
        except KeyboardInterrupt:
            print("\nЗавершую відстеження...")

    def _detect_change_type(self, old_stage, current_state):
        changes = []

        # Detect new or modified files
        for file_path, new_state in current_state.items():
            if file_path not in old_stage:
                changes.append((file_path, "added", None))  # Add placeholder size if unavailable
            elif new_state["hash"] != old_stage[file_path]["hash"]:
                changes.append((file_path, "modified", None))  # Adjust as needed

        # Detect deleted files
        for removed_path in set(old_stage) - set(current_state):
            changes.append((removed_path, "deleted", None))

        return changes

    def _check_changes(self):
        """Перевіряє зміни в файловій системі"""
        current_states = self._get_directory_state()
        changes = self._detect_change_type(self.last_states, current_states)

        for change in changes:
            file_path, *rest = change
            self._process_change(file_path)

        self.last_states = current_states


    def stop(self):
        self.stop_event.set()  # Set stop_event

    def edit_file(self, file_path, content):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user = getpass.getuser()
            change_record = {
                "file": str(file_path).split("\\")[-1],
                "type": "modified",
                "time": timestamp,
                "user": user,
            }
            self.history.append(change_record)
            self._save_history()
            print(f"[{timestamp}] {file_path}: modified")
        except Exception as e:
            print(f"Помилка при редагуванні файлу {file_path}: {e}")


if __name__ == "__main__":
    checker = FileWatcher(
        "./test_files", file_types=[".txt", ".doc", ".docx", ".pdf"]  # шлях до папки
    )  # список розширень файлів
    checker.watch()
