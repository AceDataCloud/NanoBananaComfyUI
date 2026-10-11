"""Submission safety, task semantics, and media boundary tests."""

import os
import unittest
from unittest.mock import Mock, patch

import client


class NanoBananaClientTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {"ACEDATACLOUD_API_KEY": "test-key"})
        env.start()
        self.addCleanup(env.stop)

    @patch("client.requests.post")
    def test_generate_submits_once_with_supported_model(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {"success": True, "task_id": "task-123", "trace_id": "trace-123"}
        self.assertEqual(
            client.generate("a yellow bird", "nano-banana-2.1", "1:1", "4K", 2),
            ("pending", "task-123", [], "trace-123"),
        )
        post.assert_called_once()
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://api.acedata.cloud/nano-banana/images")
        self.assertEqual(kwargs["json"]["action"], "generate")
        self.assertEqual(kwargs["json"]["model"], "nano-banana-2.1")
        self.assertEqual(kwargs["json"]["count"], 2)
        self.assertIs(kwargs["json"]["async"], True)
        self.assertFalse(kwargs["allow_redirects"])

    @patch("client.requests.post")
    def test_paid_submit_network_error_never_retries_or_leaks_key(self, post):
        post.side_effect = client.requests.Timeout("Authorization: Bearer test-key")
        with self.assertRaises(client.NanoBananaError) as caught:
            client.generate("bird", "nano-banana-2-lite", "1:1", "1K", 1)
        self.assertEqual(post.call_count, 1)
        self.assertNotIn("test-key", str(caught.exception))

    @patch("client.requests.post")
    def test_edit_sends_reference_array_and_rejects_local_urls(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {"task_id": "edit-task"}
        result = client.edit("change color", "nano-banana-pro:official", "16:9", "2K", 1,
                             '["https://example.org/a.png","https://example.org/b.png"]')
        self.assertEqual(result[1], "edit-task")
        self.assertEqual(post.call_args.kwargs["json"]["image_urls"],
                         ["https://example.org/a.png", "https://example.org/b.png"])
        with self.assertRaises(ValueError):
            client.edit("change color", "nano-banana", "1:1", "1K", 1,
                        "https://127.0.0.1/private.png")
        self.assertEqual(post.call_count, 1)

    @patch("client.requests.post")
    def test_retrieve_same_task_pending_then_terminal_image(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.side_effect = [
            {"id": "task-123", "finished_at": None, "response": None},
            {"id": "task-123", "finished_at": "2026-10-12T00:00:00Z",
             "response": {"success": True, "data": [{"image_url": "https://cdn.acedata2.cloud/nano/a.jpg"}]}},
        ]
        self.assertEqual(client.retrieve_once("task-123")[0], "pending")
        status, task_id, urls, _ = client.retrieve_once("task-123")
        self.assertEqual((status, task_id), ("succeeded", "task-123"))
        self.assertEqual(urls, ["https://cdn.acedata2.cloud/nano/a.jpg"])
        self.assertEqual([x.kwargs["json"]["id"] for x in post.call_args_list],
                         ["task-123", "task-123"])

    @patch("client.requests.post")
    def test_query_retries_but_never_submits_generation(self, post):
        ok = Mock(status_code=200)
        ok.json.return_value = {"id": "task-123", "finished_at": None, "response": None}
        post.side_effect = [client.requests.Timeout(), ok]
        with patch("client.time.sleep"):
            self.assertEqual(client.retrieve_once("task-123")[0], "pending")
        self.assertEqual(post.call_count, 2)
        for call in post.call_args_list:
            self.assertEqual(call.args[0], "https://api.acedata.cloud/nano-banana/tasks")
            self.assertEqual(call.kwargs["json"]["action"], "retrieve")

    @patch("client.requests.post")
    def test_failed_task_does_not_claim_success_or_reveal_upstream(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {
            "id": "task-123", "finished_at": "2026-10-12T00:00:00Z",
            "response": {"success": False, "error": "private upstream detail"},
        }
        with self.assertRaises(client.NanoBananaError) as caught:
            client.retrieve_once("task-123")
        self.assertNotIn("private upstream", str(caught.exception))

    @patch("client.requests.post")
    def test_batch_readback_preserves_each_task_status(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {"items": [
            {"id": "a", "finished_at": None, "response": None},
            {"id": "b", "finished_at": "2026-10-12T00:00:00Z",
             "response": {"data": {"image_urls": ["https://cdn.acedata2.cloud/b.jpg"]}}},
        ]}
        self.assertEqual(
            [(x["task_id"], x["status"]) for x in client.retrieve_batch('["a","b"]')],
            [("a", "pending"), ("b", "succeeded")],
        )
        self.assertEqual(post.call_args.kwargs["json"],
                         {"action": "retrieve_batch", "ids": ["a", "b"]})

    @patch("client.requests.get")
    def test_image_loader_rejects_arbitrary_host_before_network(self, get):
        for url in ("http://cdn.acedata2.cloud/a.png", "https://127.0.0.1/a.png",
                    "https://cdn.acedata2.cloud.evil.test/a.png"):
            with self.assertRaises(client.NanoBananaError):
                client.download_image(url)
        get.assert_not_called()

    @patch("client.requests.get")
    def test_image_download_retries_read_only_connection(self, get):
        ok = Mock(status_code=200, headers={"Content-Length": "3"})
        ok.__enter__ = Mock(return_value=ok)
        ok.__exit__ = Mock(return_value=False)
        ok.iter_content.return_value = [b"png"]
        get.side_effect = [client.requests.exceptions.SSLError(), ok]
        with patch("client.time.sleep"):
            self.assertEqual(client.download_image("https://cdn.acedata2.cloud/a.png"), b"png")
        self.assertEqual(get.call_count, 2)


if __name__ == "__main__":
    unittest.main()
