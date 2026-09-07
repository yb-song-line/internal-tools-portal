import os
import unittest


os.environ.setdefault("PORTAL_DEV_BYPASS", "1")

import server  # noqa: E402


class PortalTests(unittest.TestCase):
    def test_config_has_unique_valid_content_ids(self) -> None:
        content_ids = [
            item["id"]
            for collection in (server.CONFIG["tools"], server.CONFIG["references"])
            for item in collection
        ]
        self.assertEqual(len(content_ids), len(set(content_ids)))
        self.assertTrue(all(server.ID_PATTERN.fullmatch(item_id) for item_id in content_ids))

    def test_enterprise_pages_reports_are_in_repository(self) -> None:
        pages_prefix = "https://git.linecorp.com/pages/yb-song/internal-tools-portal/"
        for item in server.CONFIG["references"]:
            if item["url"].startswith(pages_prefix):
                relative_path = item["url"][len(pages_prefix):]
                self.assertTrue((server.ROOT / relative_path).is_file(), item["id"])

    def test_signed_session_rejects_tampering(self) -> None:
        token = server.create_session(server.PORTAL_USERNAME)
        self.assertTrue(server.validate_session(token))
        replacement = "A" if token[-1] != "A" else "B"
        self.assertFalse(server.validate_session(token[:-1] + replacement))


if __name__ == "__main__":
    unittest.main()
