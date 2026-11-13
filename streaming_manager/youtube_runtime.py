"""Bridge the YouTube worker into the application's single chat state."""
from threading import RLock, Thread

from .multichat import ChatMessage
from .youtube_chat.protocol import parse_video_id
from .youtube_chat.worker import Worker


class YouTubeChatRuntime:
    def __init__(self, state):
        self.state = state
        self._lock = RLock()
        self.worker = None
        self.thread = None
        self.source = ''
        self.status = 'YouTube: отключён.'

    @property
    def is_connected(self):
        with self._lock:
            return bool(
                self.worker is not None
                and getattr(getattr(self.worker, "status", None), "code", None)
                == "connected"
            )

    def connect(self, url):
        source = parse_video_id(url)
        self.stop()
        with self._lock:
            if source != self.source:
                self.state.change_source('youtube')
            self.source = source
            worker = Worker(source, lambda kind, value: self._receive(worker, kind, value))
            self.worker = worker
            self.status = 'YouTube: подключение…'
            self.thread = Thread(target=worker.run, daemon=True, name='youtube-chat')
            self.thread.start()

    def _receive(self, worker, kind, value):
        with self._lock:
            if worker is not self.worker:
                return
            if kind == 'status':
                self.status = 'YouTube: ' + value.text
            elif kind == 'multichat':
                for event in value:
                    if event['kind'] == 'delete':
                        self.state.delete_message('youtube', self.source, event['target'])
                    elif event['kind'] == 'delete_author':
                        self.state.clear_chat('youtube', self.source, author_id=event['target'])
                    else:
                        if event['kind'] == 'replace' and event.get('target'):
                            self.state.delete_message('youtube', self.source, event['target'])
                        self.state.ingest(ChatMessage(
                            platform='youtube', source_id=self.source, external_id=event['id'],
                            author=event['author'], author_id=event['author_id'], text=event['text'],
                            sent_at=event['sent_at'], received_at=event['received_at'],
                            avatar_url=event['avatar_url'], fragments=tuple(event['fragments']),
                        ))

    def stop(self):
        with self._lock:
            if self.worker:
                self.worker.stop()
            self.worker = None
            self.state.disconnect('youtube')
            self.status = 'YouTube: отключён.'
