# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for ADK CLI usage telemetry collection."""

import json
import os
import tempfile
import unittest
from unittest import mock

from google.adk.cli._telemetry import _metrics_collector as metrics

# Create a temporary directory for tests to avoid writing to user home.
_TEMP_DIR = tempfile.mkdtemp()
_QUEUE_FILE = os.path.join(_TEMP_DIR, "telemetry_queue.jsonl")
_LOCK_FILE = os.path.join(_TEMP_DIR, "clearcut_lock")
_CONFIG_FILE = os.path.join(_TEMP_DIR, "config.json")


class CliMetricsTest(unittest.TestCase):
  """Tests for ADK CLI usage metrics collection."""

  def setUp(self):
    super().setUp()

    # Patch paths per test to prevent leakage across modules
    self.queue_patcher = mock.patch.object(
        metrics._constants, "QUEUE_FILE", _QUEUE_FILE
    )
    self.lock_patcher = mock.patch.object(
        metrics._constants, "LOCK_FILE", _LOCK_FILE
    )
    self.queue_patcher.start()
    self.lock_patcher.start()

    os.makedirs(_TEMP_DIR, exist_ok=True)
    if os.path.exists(_QUEUE_FILE):
      os.remove(_QUEUE_FILE)
    if os.path.exists(_LOCK_FILE):
      os.remove(_LOCK_FILE)
    if os.path.exists(_CONFIG_FILE):
      os.remove(_CONFIG_FILE)

  def tearDown(self):
    self.queue_patcher.stop()
    self.lock_patcher.stop()
    if os.path.exists(_QUEUE_FILE):
      os.remove(_QUEUE_FILE)
    if os.path.exists(_LOCK_FILE):
      os.remove(_LOCK_FILE)
    if os.path.exists(_CONFIG_FILE):
      os.remove(_CONFIG_FILE)
    try:
      os.rmdir(_TEMP_DIR)
    except OSError:
      pass
    super().tearDown()

  def test_opt_out_by_default(self):
    """Verify that collection is disabled by default if no config exists."""
    with mock.patch.object(
        metrics._telemetry_config,
        "read_telemetry_consent",
        return_value=None,
    ):
      metrics.MetricsCollector._instance = None
      collector = metrics.MetricsCollector.get_collector()
      self.assertIsNone(collector)

  def test_opt_in_when_config_enabled(self):
    """Verify that collection config enablement is correctly respected."""
    with mock.patch.object(
        metrics._telemetry_config,
        "read_telemetry_consent",
        return_value=True,
    ):
      metrics.MetricsCollector._instance = None
      collector = metrics.MetricsCollector.get_collector()
      self.assertIsNotNone(collector)

  def test_rate_limited_defensive_fail_closed_on_exception(self):
    """Verify that reading exceptions in rate limit log defaults to True."""
    # Create the lock file so exists check succeeds
    with open(_LOCK_FILE, "w") as f:
      f.write("invalid-non-float-lock-time")

    # Trigger ValueError during float casting to verify fail closed.
    # Verify it defaults to True (meaning it fails closed and rate limited).
    self.assertTrue(metrics.MetricsCollector._is_rate_limited())

  def test_record_command_run(self):
    """Verify command execution logs are correctly parsed and queued."""
    with mock.patch.object(
        metrics._telemetry_config,
        "read_telemetry_consent",
        return_value=True,
    ):
      metrics.MetricsCollector._instance = None
      collector = metrics.MetricsCollector.get_collector()
      self.assertIsNotNone(collector)

    # Exit the patch block so standard path checks run cleanly.
    with mock.patch.object(
        collector,
        "_gather_flags_from_click",
        return_value=["--debug", "--project", "-v", "--user"],
    ):
      collector.record_command_run(
          command="deploy",
          subcommand="create",
          exit_code=0,
          duration_ms=450,
          exception_type="",
      )

    # Verify it's written in queue file
    self.assertTrue(os.path.exists(_QUEUE_FILE))
    with open(_QUEUE_FILE, "r", encoding="utf-8") as f:
      lines = f.readlines()
      self.assertEqual(len(lines), 1)
      event = json.loads(lines[0])
      self.assertIn("source_extension_json", event)

      source = json.loads(event["source_extension_json"])
      self.assertEqual(source["command_run"]["command"], "deploy")
      self.assertEqual(source["command_run"]["subcommand"], "create")
      self.assertEqual(source["command_run"]["exit_code"], 0)
      self.assertEqual(source["command_run"]["duration_ms"], 450)
      self.assertEqual(
          source["command_run"]["flags"],
          ["--debug", "--project", "-v", "--user"],
      )

  def test_record_command_run_with_click(self):
    """Verify that flags are correctly extracted from Click context."""
    with mock.patch.object(
        metrics._telemetry_config,
        "read_telemetry_consent",
        return_value=True,
    ):
      metrics.MetricsCollector._instance = None
      collector = metrics.MetricsCollector.get_collector()
      self.assertIsNotNone(collector)

    # Mock Click context and parameters
    mock_ctx = mock.MagicMock()

    # 1. Option passed on command line
    opt1 = mock.MagicMock(spec=metrics.click.Option)
    opt1.name = "debug"
    opt1.opts = ["--debug"]

    # 2. Option NOT passed on command line (default)
    opt2 = mock.MagicMock(spec=metrics.click.Option)
    opt2.name = "project"
    opt2.opts = ["--project"]

    # 3. Positional argument passed on command line
    arg1 = mock.MagicMock(spec=metrics.click.Argument)
    arg1.name = "agent_path"

    mock_ctx.command.params = [opt1, opt2, arg1]

    # Setup parameter source lookups
    COMMANDLINE = metrics.click.core.ParameterSource.COMMANDLINE
    DEFAULT = metrics.click.core.ParameterSource.DEFAULT
    mock_ctx.get_parameter_source.side_effect = (
        lambda name: COMMANDLINE if name in ["debug", "agent_path"] else DEFAULT
    )

    with mock.patch.object(
        metrics.click, "get_current_context", return_value=mock_ctx
    ):
      collector.record_command_run(
          command="deploy",
          subcommand="create",
          exit_code=0,
          duration_ms=450,
      )

    # Verify it's written in queue file with click flags
    self.assertTrue(os.path.exists(_QUEUE_FILE))
    with open(_QUEUE_FILE, "r", encoding="utf-8") as f:
      lines = f.readlines()
      self.assertEqual(len(lines), 1)
      event = json.loads(lines[0])
      source = json.loads(event["source_extension_json"])
      self.assertEqual(
          source["command_run"]["flags"],
          ["--debug", "<agent_path>"],
      )


if __name__ == "__main__":
  unittest.main()
