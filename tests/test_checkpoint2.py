"""Offline tests for Checkpoint 2 MCP and ReAct integration."""

import json
import sys
import unittest
import os
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from app import load_test_cases, run_react_agent  # noqa: E402
from mcp_server import MCPAcademicServer  # noqa: E402
from prompts import MAX_ITERATIONS  # noqa: E402
from providers import MockOfflineProvider, sanitize_schema_for_gemini  # noqa: E402
from tools import TOOLS_SCHEMA  # noqa: E402


class MCPServerTests(unittest.TestCase):
    def setUp(self):
        self.server = MCPAcademicServer()

    def test_call_tool_wraps_result_as_json_rpc(self):
        response = self.server.call_tool(
            "query_matching_context",
            {"query_type": "student_skills", "student_id": "SV001"},
        )

        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["server"], self.server.server_name)
        self.assertEqual(response["tool"], "query_matching_context")
        self.assertEqual(response["result"]["status"], "SUCCESS")
        self.assertIn("skills", response["result"]["student"])

    def test_call_tool_preserves_structured_tool_errors(self):
        response = self.server.call_tool("missing_tool", {})

        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["result"]["status"], "UNKNOWN_TOOL")

    def test_call_action_tool_returns_safe_dry_run(self):
        response = self.server.call_tool(
            "assign_student_advisor",
            {"student_id": "SV001", "advisor_id": "GV012", "mode": "dry_run"},
        )

        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["result"]["status"], "PROPOSED")
        self.assertTrue(response["result"]["requires_human_approval"])

    def test_call_tool_handles_invalid_backend_json(self):
        with patch("mcp_server.dispatch_tool_call", return_value="not-json"):
            response = self.server.call_tool("query_matching_context", {})

        self.assertEqual(response["result"]["status"], "INVALID_TOOL_RESPONSE")


class GeminiAdapterTests(unittest.TestCase):
    def test_tool_schemas_build_a_valid_google_genai_config(self):
        from google.genai import types

        declarations = []
        for tool in TOOLS_SCHEMA:
            parameters = sanitize_schema_for_gemini(tool["parameters"])
            self.assertNotIn("additionalProperties", parameters)
            declarations.append(
                types.FunctionDeclaration(
                    name=tool["name"],
                    description=tool["description"],
                    parameters=types.Schema.model_validate(parameters),
                )
            )

        config = types.GenerateContentConfig(
            tools=[types.Tool(function_declarations=declarations)]
        )
        self.assertEqual(len(config.tools), 1)
        self.assertEqual(len(config.tools[0].function_declarations), 2)

    def test_gemini_can_disable_mock_fallback_for_real_api_acceptance(self):
        with patch.dict(os.environ, {"LLM_ALLOW_MOCK_FALLBACK": "false"}):
            from providers import GeminiProvider

            self.assertFalse(GeminiProvider._allow_mock_fallback())


class ReActLoopTests(unittest.TestCase):
    def setUp(self):
        self.server = MCPAcademicServer()
        self.provider = MockOfflineProvider()
        self.cases = load_test_cases()

    def _run_case(self, case_index):
        return run_react_agent(
            self.cases[case_index]["question"], self.provider, self.server
        )

    def test_capability_query_returns_direct_answer(self):
        trace = self._run_case(0)

        self.assertEqual(len(trace), 1)
        self.assertEqual(trace[0]["action_type"], "FINAL_ANSWER")
        self.assertIn("kỹ năng", trace[0]["output"])

    def test_student_skill_query_uses_observation_then_answers(self):
        trace = self._run_case(1)

        self.assertEqual(
            [event["action_type"] for event in trace],
            ["TOOL_EXECUTION", "FINAL_ANSWER"],
        )
        self.assertEqual(trace[0]["tool_name"], "query_matching_context")
        self.assertEqual(trace[0]["observation"]["status"], "SUCCESS")
        self.assertIn("thought", trace[0])
        self.assertEqual(trace[0]["provider"], "MockOfflineProvider")
        self.assertEqual(trace[0]["model"], "Offline-Mock-Model-2026")
        self.assertIn("Python", trace[-1]["output"])
        self.assertIn("student_profiles.csv", trace[-1]["output"])

    def test_advisor_skill_query_is_grounded_in_evidence(self):
        trace = self._run_case(2)

        self.assertEqual(trace[0]["observation"]["status"], "SUCCESS")
        self.assertIn("Machine Learning", trace[-1]["output"])
        self.assertIn("advisor_skill_evidence.csv", trace[-1]["output"])

    def test_historical_thesis_query_reports_source(self):
        trace = self._run_case(3)

        self.assertEqual(trace[0]["observation"]["status"], "SUCCESS")
        self.assertIn("Phát hiện gian lận", trace[-1]["output"])
        self.assertIn("theses.csv", trace[-1]["output"])

    def test_similarity_query_executes_multiple_tools_before_final_answer(self):
        trace = self._run_case(4)
        tool_events = [e for e in trace if e["action_type"] == "TOOL_EXECUTION"]

        self.assertEqual(len(tool_events), 4)
        self.assertEqual(
            [e["arguments"]["query_type"] for e in tool_events],
            [
                "student_skills",
                "historical_thesis",
                "advisor_skills",
                "similarity",
            ],
        )
        self.assertTrue(all(e["observation"] for e in tool_events))
        self.assertTrue(all(e["observation"]["status"] == "SUCCESS" for e in tool_events))
        self.assertEqual(trace[-1]["action_type"], "FINAL_ANSWER")
        self.assertIn("0.82", trace[-1]["output"])
        self.assertIn("quota", trace[-1]["output"].lower())
        self.assertIn("khuyến nghị", trace[-1]["output"].lower())

    def test_not_found_observation_is_not_replaced_with_invented_data(self):
        question = "Tra cứu kỹ năng của sinh viên SV999."
        trace = run_react_agent(question, self.provider, self.server)

        self.assertEqual(trace[0]["observation"]["status"], "NOT_FOUND")
        self.assertIn("không tìm thấy", trace[-1]["output"].lower())
        self.assertNotIn("Python", trace[-1]["output"])

    def test_loop_stops_at_max_iterations(self):
        class EndlessToolProvider:
            def generate_with_tools(self, prompt, tools_schema, system_prompt=""):
                return {
                    "type": "tool_call",
                    "tool_name": "query_matching_context",
                    "arguments": {
                        "query_type": "student_skills",
                        "student_id": "SV001",
                    },
                    "thought": "Tiếp tục gọi tool để kiểm tra giới hạn.",
                }

        trace = run_react_agent("Kiểm tra giới hạn", EndlessToolProvider(), self.server)

        tool_events = [e for e in trace if e["action_type"] == "TOOL_EXECUTION"]
        self.assertEqual(len(tool_events), MAX_ITERATIONS)
        self.assertEqual(trace[-1]["action_type"], "MAX_ITERATIONS_REACHED")


if __name__ == "__main__":
    unittest.main()