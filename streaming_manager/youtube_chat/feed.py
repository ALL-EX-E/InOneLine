"""Bounded session state; IDs, not text, determine message identity."""

from collections import OrderedDict
import time


class Feed:
    def __init__(self, *, started_at, show_history=False, limit=300, memory_limit=5000, clock=time.time):
        if limit < 1 or memory_limit < limit:
            raise ValueError("Invalid feed bounds")
        self.started_at = started_at
        self.show_history = show_history
        self.limit = limit
        self.memory_limit = memory_limit
        self.clock = clock
        self._messages = OrderedDict()
        self._seen = OrderedDict()
        self._deleted = OrderedDict()
        self._deleted_authors = OrderedDict()
        self.duplicates = 0
        self.history_skipped = 0
        self.received = 0
        self.deleted = 0

    @property
    def messages(self):
        return tuple(self._messages.values())

    @property
    def memory_size(self):
        return len(self._seen)

    @property
    def tombstone_size(self):
        return len(self._deleted)

    def _remember(self, collection, key):
        collection[key] = None
        collection.move_to_end(key)
        while len(collection) > self.memory_limit:
            collection.popitem(last=False)

    def _delete(self, mid):
        self._remember(self._deleted, mid)
        if mid in self._messages:
            del self._messages[mid]
            self.deleted += 1

    def apply(self, events, *, initializing=False):
        for event in events:
            if event.kind == "delete":
                self._delete(event.target)
                continue
            if event.kind == "delete_author":
                self._deleted_authors[event.target] = self.clock()
                self._deleted_authors.move_to_end(event.target)
                while len(self._deleted_authors) > self.memory_limit:
                    self._deleted_authors.popitem(last=False)
                for mid, msg in list(self._messages.items()):
                    if msg.author_id == event.target:
                        self._delete(mid)
                continue
            msg = event.message
            if msg is None or event.kind not in {"add", "replace"}:
                continue
            if msg.id in self._deleted or (event.kind == "replace" and event.target in self._deleted):
                continue
            cutoff = self._deleted_authors.get(msg.author_id)
            if cutoff is not None and (msg.sent_at is None or msg.sent_at <= cutoff):
                self._remember(self._deleted, msg.id)
                continue
            if event.kind == "replace" and event.target in self._messages:
                if event.target == msg.id:
                    self._messages[msg.id] = msg
                    continue
                self._delete(event.target)
            if msg.id in self._seen:
                self.duplicates += 1
                continue
            self._remember(self._seen, msg.id)
            if initializing and not self.show_history and (msg.sent_at is None or msg.sent_at < self.started_at):
                self.history_skipped += 1
                continue
            self._messages[msg.id] = msg
            self.received += 1
            while len(self._messages) > self.limit:
                self._messages.popitem(last=False)

    def counters(self):
        return {"received": self.received, "visible": len(self._messages), "deleted": self.deleted,
                "duplicates": self.duplicates, "history_skipped": self.history_skipped,
                "seen_ids": len(self._seen), "tombstones": len(self._deleted),
                "author_tombstones": len(self._deleted_authors)}
