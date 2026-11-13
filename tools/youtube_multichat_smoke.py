import unittest
from unittest.mock import patch

from streaming_manager.multichat import ChatMessage, MultichatState
from streaming_manager.youtube_runtime import YouTubeChatRuntime


class YouTubeMultichatSmoke(unittest.TestCase):
    def test_mixed_zero_delay_keeps_arrival_order(self):
        state = MultichatState(clock=lambda: 10, wall_clock=lambda: 100)
        state.ingest(ChatMessage('twitch', 't', '1', 'T', 'first', sent_at=100))
        state.ingest(ChatMessage('youtube', 'y', '2', 'Y', 'second', sent_at=50))
        self.assertEqual([x['external_id'] for x in state.snapshot()['messages']], ['1', '2'])
        self.assertEqual([x['platform'] for x in state.operator_feed_snapshot()['messages']], ['twitch', 'youtube'])

    def test_youtube_events_share_state_and_delete(self):
        state = MultichatState()
        runtime = YouTubeChatRuntime(state)
        runtime.source = '4cC65h_Tecc'
        worker = object()
        runtime.worker = worker
        row = {'kind': 'add', 'id': '1', 'author': 'Y', 'author_id': 'ch', 'text': '🙂',
               'sent_at': 42, 'received_at': 45, 'avatar_url': 'https://yt4.ggpht.com/a',
               'fragments': [{'kind': 'image', 'text': '🙂', 'url': 'https://www.youtube.com/e.png'}]}
        runtime._receive(worker, 'multichat', (row,))
        self.assertEqual(state.snapshot()['messages'][0]['avatar_url'], row['avatar_url'])
        self.assertEqual(state.snapshot(for_obs=True)['messages'][0]['sent_at'], 42)
        runtime._receive(worker, 'multichat', ({'kind': 'delete', 'target': '1'},))
        self.assertFalse(state.snapshot()['messages'])
        self.assertFalse(state.snapshot(for_obs=True)['messages'])


if __name__ == '__main__':
    unittest.main()
