import os
import json
import hashlib
from datetime import datetime
import time

class EditChecker:
    def __init__(self, path_to_watch, history_file='history.json'):
        self.path_to_watch = path_to_watch
        self.history_file = history_file
        self.last_state = self._get_file_state()
        self.load_history()

    def _load_hostory(self):
        # Load history from file
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
        else:
            self.history = {}

    def _save_history(self):
        # Save history to file
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2)

    def _get_file_state(self):
        # Get file state
        if not os.path.exists(self.path_to_watch):
            raise FileNotFoundError(f"Path {self.path_to_watch} not found")

        with open(self.path_to_watch, 'rb') as f:
            content = f.read()
            return {
                'size': len(content),
                'hash': hashlib.md5(content).hexdigest(),
                'mtime': os.path.getmtime(self.path_to_watch)
            }

    def _detect_change_type(self, current_state):
        if self.last_state is None:
            if current_state is None:
                return None
            return 'created'

        if current_state is None:
            return 'deleted'

        if self.last_state['hash'] != current_state['hash']:
            if self.last_state['size'] < current_state['size']:
                return 'added'
            elif self.last_state['size'] > current_state['size']:
                return 'removed'
            else:
                return 'modified'

        return None

    def watch(self, interval=1):
        print(f"Починаю відстеження файлу: {self.path_to_watch}")
        print("Натисніть Ctrl+C для завершення")

        try:
            while True:
                current_state = self._get_file_state()
                change_type = self._detect_change_type(current_state)

                if change_type:
                    print(f"Зміни в файлі: {change_type}")
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    change_record = {
                        'type': change_type,
                        'timestamp': timestamp
                    }

                    if current_state:
                        change_record['size'] = current_state['size']

                    self.history.append(change_record)
                    self._save_history()

                    print(f"[{timestamp}] {change_type}")

                self.last_state = current_state
                time.sleep(interval)

        except KeyboardInterrupt:
            print("Відстеження завершено")

if __name__ == '__main__':
    checker = EditChecker('test.txt')
    checker.watch()