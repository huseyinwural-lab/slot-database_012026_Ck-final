import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import json
import os
import sys

# Add scripts to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../scripts")
from runner_utils import sanitize_log, get_env_config, login_admin_with_retry

class TestRunnerUtils(unittest.TestCase):

    def test_sanitize_log_masks_tokens(self):
        data = {"access_token": "secret123", "public": "visible"}
        masked = sanitize_log(data)
        self.assertEqual(masked["access_token"], "***REDACTED***")
        self.assertEqual(masked["public"], "visible")

    def test_sanitize_log_nested(self):
        data = {"data": {"password": "pwd", "info": "ok"}}
        masked = sanitize_log(data)
        self.assertEqual(masked["data"]["password"], "***REDACTED***")

    def test_sanitize_log_string_json(self):
        data = '{"token": "abcd", "id": 1}'
        masked_str = sanitize_log(data)
        masked_obj = json.loads(masked_str)
        self.assertEqual(masked_obj["token"], "***REDACTED***")

    def test_get_env_config_defaults(self):
        config = get_env_config()
        self.assertEqual(config["BASE_URL"], "http://localhost:8001/api/v1")

    @patch("os.environ.get")
    def test_strict_mode_fail(self, mock_env):
        def side_effect(key, default=None):
            if key == "CI_STRICT": return "1"
            if key == "API_BASE_URL": return None # Missing
            return default
        mock_env.side_effect = side_effect
        
        with self.assertRaises(SystemExit) as cm:
            get_env_config()
        self.assertEqual(cm.exception.code, 2)

    @patch("httpx.AsyncClient.post")
    async def test_login_retry_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"access_token": "valid"}
        mock_post.return_value = mock_resp
        
        token = await login_admin_with_retry(AsyncMock())
        self.assertEqual(token, "valid")

if __name__ == '__main__':
    unittest.main()
