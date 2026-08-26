import os
import unittest


os.environ.setdefault("PORTAL_DEV_BYPASS", "1")

import server  # noqa: E402


class PortalTests(unittest.TestCase):
    def test_config_has_unique_valid_tool_ids(self) -> None:
        tool_ids = [tool["id"] for tool in server.CONFIG["tools"]]
        self.assertEqual(len(tool_ids), len(set(tool_ids)))
        self.assertTrue(all(server.ID_PATTERN.fullmatch(tool_id) for tool_id in tool_ids))

    def test_signed_session_rejects_tampering(self) -> None:
        token = server.create_session(server.PORTAL_USERNAME)
        self.assertTrue(server.validate_session(token))
        replacement = "A" if token[-1] != "A" else "B"
        self.assertFalse(server.validate_session(token[:-1] + replacement))


if __name__ == "__main__":
    unittest.main()

