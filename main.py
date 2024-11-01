import os
import json
import hashlib
from datetime import datetime
import time
from pathlib import Path


class EditChecker:
    def __init__(self, path_to_watch, file_types=None, history_file='history.json'):
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

    def _load_history(self):
        # Load history from file
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
                if not isinstance(self.history, list):
                    self.history = []
        else:
            print('bad with history')
            self.history = []

    def _save_history(self):
        # Save history to file
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2)

    def _get_file_hash(self, file_path):
        """Отримує хеш файлу"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            print(f"Помилка при читанні файлу {file_path}: {e}")
            return None

    def _get_directory_state(self):
        """Отримує стан всіх файлів у директорії"""
        states = {}

        if not self.path_to_watch.exists():
            return states

        if self.path_to_watch.is_file():
            if self._should_watch_file(self.path_to_watch):
                file_state = self._get_file_state(self.path_to_watch)
                if file_state:
                    states[str(self.path_to_watch)] = file_state
        else:
            try:
                for file_path in self.path_to_watch.rglob('*'):
                    if file_path.is_file() and self._should_watch_file(file_path):
                        file_state = self._get_file_state(file_path)
                        if file_state:
                            states[str(file_path)] = file_state
            except Exception as e:
                print(f"Помилка при скануванні директорії: {e}")

        return states

    def _should_watch_file(self, file_path):
        if self.file_types is None:
            return True
        return file_path.suffix.lower() in self.file_types

    def _get_file_hash(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            print(f"Помилка при читанні файлу {file_path}: {e}")
            return None

    def _get_file_state(self, file_path):
        # Get file state
        try:
            if not os.path.exists(file_path):
                return None

            stats = os.stat(file_path)
            return {
                'size': stats.st_size,
                'hash': self._get_file_hash(file_path),
                'mtime': stats.st_mtime,
                'file': str(file_path).split("\\")[-1]
            }
        except Exception as e:
            print(f"Помилка при отриманні стану файлу {file_path}: {e}")
            return None

    def _get_initial_state(self):
        states = {}
        if self.path_to_watch.is_file():
            if self._should_watch_file(self.path_to_watch):
                states[self.path_to_watch] = self._get_file_state(self.path_to_watch)
        else:
            for file_path in self.path_to_watch.rglob('*'):
                if file_path.is_file() and self._should_watch_file(file_path):
                    states[file_path] = self._get_file_state(file_path)
        return states

    def _detect_change_type(self, old_stage, current_state):

        changes = []
        for file_path, new_state in current_state.items():
            if file_path not in old_stage:
                changes.append((file_path, "created", new_state['size']))
            elif new_state['hash'] != old_stage[file_path]['hash']:
                old_size = old_stage[file_path]['size']
                new_size = new_state['size']
                if new_size > old_size:
                    change_type = "added"
                elif new_size < old_size:
                    change_type = "removed"
                else:
                    change_type = "modified"
                changes.append((file_path, change_type, new_size))

            # Перевіряємо видалені файли
        for file_path in old_stage:
            if file_path not in current_state:
                changes.append((file_path, "removed", None))

        return changes

    def watch(self, interval=1):
        print(f"Починаю відстеження файлу: {self.path_to_watch}")
        if self.file_types:
            print(f"Відстежую файли з розширеннями: {', '.join(self.file_types)}")
        print("Натисніть Ctrl+C для завершення")

        try:
            while True:
                try:
                    current_states = self._get_directory_state()
                    changes = self._detect_change_type(self.last_states, current_states)

                    for file_path, change_type, size in changes:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        if change_type:
                            change_record = {
                                "file": str(file_path).split("\\")[-1],
                                "type": change_type,
                                "time": timestamp
                            }

                            if size is not None:
                                change_record["size"] = size

                            self.history.append(change_record)
                            self._save_history()

                            print(f"[{timestamp}] {file_path}: {change_type}")

                    self.last_states = current_states
                    time.sleep(interval)


                except Exception as e:
                    print(f"Помилка під час відстеження: {e}")
                    time.sleep(interval)

        except KeyboardInterrupt:
            print("\nЗавершую відстеження...")


if __name__ == '__main__':
    checker = EditChecker("./test_files",  # шлях до папки
                          file_types=['.txt', '.doc', '.docx', '.pdf'])  # список розширень файлів
    checker.watch()
