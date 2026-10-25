"""D41-03 read-only local capture; isolated deterministic regression.

No Twitch/Google account, no stream or external network is required.
"""
import os
import unittest
from unittest.mock import Mock

from streaming_manager.browser_chat import (
    BrowserChatRuntime, BrowserChatSource, _BROWSER_OBSERVER,
    normalize_browser_chat_source,
)
from streaming_manager.multichat import MultichatState


class Urls(unittest.TestCase):
    def test_youtube_studio_popout_from_user_screenshot(self):
        source = normalize_browser_chat_source(
            'youtube', 'https://studio.youtube.com/live_chat?is_popout=1&v=4cC65h_Tecc',
        )
        self.assertEqual(source.source_id, '4cC65h_Tecc')
        self.assertEqual(source.channel, '4cC65h_Tecc')
        self.assertTrue(source.url.startswith('https://studio.youtube.com/live_chat?'))

    def test_youtube_regular_popout(self):
        source = normalize_browser_chat_source(
            'youtube', 'https://www.youtube.com/live_chat?v=AaBbCcDd123&is_popout=1',
        )
        self.assertEqual(source.source_id, 'AaBbCcDd123')
        self.assertNotIn('token', source.url)

    def test_twitch_dashboard_popout_from_user_screenshot(self):
        source = normalize_browser_chat_source(
            'twitch', 'https://dashboard.twitch.tv/popout/u/alex_say62/stream-manager/chat',
        )
        self.assertEqual(source.source_id, 'alex_say62')
        self.assertEqual(source.channel, 'alex_say62')

    def test_twitch_public_popout(self):
        source = normalize_browser_chat_source('twitch', 'https://www.twitch.tv/popout/alex_say62/chat?popout=')
        self.assertEqual(source.source_id, 'alex_say62')

    def test_no_arbitrary_or_insecure_urls(self):
        invalid = [
            ('youtube','http://studio.youtube.com/live_chat?v=AaBbCcDd123'),
            ('youtube','https://studio.youtube.com.evil.test/live_chat?v=AaBbCcDd123'),
            ('youtube','https://studio.youtube.com/live_chat?v=bad'),
            ('youtube','https://studio.youtube.com/live_chat?is_popout=1&v=AaBbCcDd123#x'),
            ('youtube','https://www.youtube.com/watch?v=AaBbCcDd123'),
            ('twitch','https://www.twitch.tv/alex_say62'),
            ('twitch','https://dashboard.twitch.tv/popout/u/alex_say62/stream-manager/chat?token=x#x'),
            ('twitch','https://dashboard.twitch.tv@evil.test/popout/u/alex_say62/stream-manager/chat'),
            ('twitch','https://www.twitch.tv/popout/a/chat?popout='),
        ]
        for platform,url in invalid:
            with self.subTest(platform=platform,url=url):
                with self.assertRaises(ValueError):
                    normalize_browser_chat_source(platform,url)

    def test_known_query_is_whitelisted(self):
        source = normalize_browser_chat_source('youtube',
                    'https://www.youtube.com/live_chat?v=AaBbCcDd123&track=secret')
        self.assertNotIn('track', source.url)

    def test_observer_is_read_only_bounded_and_skips_history(self):
        self.assertIn('MutationObserver', _BROWSER_OBSERVER)
        self.assertIn('document.querySelectorAll(selectors).forEach(n => observed.add(n))', _BROWSER_OBSERVER)
        self.assertIn('baseline = true', _BROWSER_OBSERVER)
        self.assertIn('events.length >= 512', _BROWSER_OBSERVER)
        self.assertIn('events.splice(0, 100)', _BROWSER_OBSERVER)
        self.assertNotIn('fetch(', _BROWSER_OBSERVER)
        self.assertNotIn('click()', _BROWSER_OBSERVER)
        self.assertNotIn('localStorage', _BROWSER_OBSERVER)

    def test_multiple_copies_dedupe_at_shared_state(self):
        from streaming_manager.multichat import ChatMessage
        state=MultichatState()
        item=ChatMessage('twitch','chan','one','Viewer','text')
        self.assertTrue(state.ingest(item))
        self.assertFalse(state.ingest(item))
        self.assertEqual(len(state.snapshot()['messages']),1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
