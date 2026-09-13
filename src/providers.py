"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import re
import time
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()


def sanitize_schema_for_gemini(value: Any) -> Any:
    """Loại keyword JSON Schema mà google-genai Schema chưa hỗ trợ."""
    if isinstance(value, dict):
        return {
            key: sanitize_schema_for_gemini(item)
            for key, item in value.items()
            if key != "additionalProperties"
        }
    if isinstance(value, list):
        return [sanitize_schema_for_gemini(item) for item in value]
    return value

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return (
            "[Mock Chatbot Response]: Tôi có thể giới thiệu hệ thống ghép cặp, "
            "nhưng không thể tra cứu hồ sơ hoặc tạo phân bổ nếu không có Tool."
        )

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        user_query, history = self._parse_react_prompt(prompt)
        query_lower = user_query.lower()
        student_id = self._extract_id(user_query, r"\bSV\d+\b", "SV001")
        advisor_id = self._extract_id(user_query, r"\bGV\d+\b", "GV012")
        completed_types = {
            item.get("arguments", {}).get("query_type")
            for item in history
            if item.get("tool_name") == "query_matching_context"
        }

        failed_observation = next(
            (
                item.get("observation", {})
                for item in history
                if item.get("observation", {}).get("status") not in {"SUCCESS", "PROPOSED", "COMMITTED"}
            ),
            None,
        )
        if failed_observation:
            return {
                "type": "text",
                "content": failed_observation.get(
                    "message",
                    f"Không thể hoàn tất yêu cầu ({failed_observation.get('status')}).",
                ),
                "thought": "Tool trả lỗi; phản hồi đúng Observation và không bịa dữ liệu.",
            }

        is_capability_query = any(
            term in query_lower
            for term in ("hỗ trợ những chức năng", "có thể hỗ trợ gì", "khả năng của")
        )
        if is_capability_query:
            return {
                "type": "text",
                "content": (
                    "Tôi có thể tra cứu kỹ năng sinh viên, kỹ năng và bằng chứng "
                    "của giảng viên, đọc khóa luận được cấp quyền, đánh giá "
                    "compatibility và tạo đề xuất dry-run. Phân bổ chính thức "
                    "cần phê duyệt."
                ),
                "thought": "Câu hỏi về khả năng chung nên trả lời trực tiếp.",
            }

        is_similarity = any(
            term in query_lower
            for term in ("tương đồng", "compatibility", "phù hợp với chuyên môn")
        )
        if is_similarity:
            sequence = [
                ("student_skills", {"student_id": student_id}),
                ("historical_thesis", {"student_id": student_id}),
                ("advisor_skills", {"advisor_id": advisor_id}),
                ("similarity", {"student_id": student_id, "advisor_id": advisor_id}),
            ]
            for query_type, identifiers in sequence:
                if query_type not in completed_types:
                    return self._matching_query_call(query_type, **identifiers)
            return self._summarize_similarity(history)

        if "khóa luận" in query_lower or "tài liệu" in query_lower:
            if "historical_thesis" not in completed_types:
                return self._matching_query_call(
                    "historical_thesis", student_id=student_id
                )
            return self._summarize_thesis(history)

        if "giảng viên" in query_lower and any(
            term in query_lower for term in ("kỹ năng", "skill", "lĩnh vực")
        ):
            if "advisor_skills" not in completed_types:
                return self._matching_query_call(
                    "advisor_skills", advisor_id=advisor_id
                )
            return self._summarize_advisor(history)

        if "sinh viên" in query_lower and any(
            term in query_lower for term in ("kỹ năng", "skill", "tra cứu")
        ):
            if "student_skills" not in completed_types:
                return self._matching_query_call(
                    "student_skills", student_id=student_id
                )
            return self._summarize_student(history)

        return {
            "type": "text",
            "content": "Tôi chưa xác định được nghiệp vụ matching cần thực hiện.",
            "thought": "Yêu cầu chưa đủ rõ để gọi tool an toàn.",
        }

    @staticmethod
    def _parse_react_prompt(prompt: str):
        marker = "\nREACT_CONTEXT_JSON:\n"
        if marker not in prompt:
            return prompt, []
        user_part, history_part = prompt.split(marker, 1)
        user_query = user_part.removeprefix("USER_QUERY:\n")
        try:
            history = json.loads(history_part)
        except json.JSONDecodeError:
            history = []
        return user_query, history if isinstance(history, list) else []

    @staticmethod
    def _extract_id(text: str, pattern: str, default: str) -> str:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return match.group(0).upper() if match else default

    @staticmethod
    def _matching_query_call(query_type: str, **identifiers) -> Dict[str, Any]:
        return {
            "type": "tool_call",
            "tool_name": "query_matching_context",
            "arguments": {"query_type": query_type, **identifiers},
            "thought": f"Cần lấy dữ liệu {query_type} từ MCP Server.",
        }

    @staticmethod
    def _observation(history, query_type):
        for item in reversed(history):
            if item.get("arguments", {}).get("query_type") == query_type:
                return item.get("observation", {})
        return {}

    def _summarize_student(self, history):
        observation = self._observation(history, "student_skills")
        student = observation.get("student", {})
        skills = ", ".join(student.get("skills", []))
        return {
            "type": "text",
            "content": (
                f"Sinh viên {student.get('student_id')} có các kỹ năng: {skills}. "
                f"Nguồn: {student.get('skill_source')}; dữ liệu: "
                f"{observation.get('data_version')}."
            ),
            "thought": "Tổng hợp skill đúng theo Observation.",
        }

    def _summarize_advisor(self, history):
        observation = self._observation(history, "advisor_skills")
        advisor = observation.get("advisor", {})
        skills = ", ".join(advisor.get("skills", []))
        evidence_sources = sorted(
            {item.get("source", "") for item in advisor.get("skill_evidence", [])}
        )
        return {
            "type": "text",
            "content": (
                f"Giảng viên {advisor.get('advisor_id')} có các kỹ năng: {skills}. "
                f"Lĩnh vực: {', '.join(advisor.get('research_fields', []))}. "
                f"Nguồn bằng chứng: {', '.join(evidence_sources)}."
            ),
            "thought": "Tổng hợp skill và evidence đúng theo Observation.",
        }

    def _summarize_thesis(self, history):
        observation = self._observation(history, "historical_thesis")
        thesis = observation.get("thesis", {})
        return {
            "type": "text",
            "content": (
                f"Khóa luận '{thesis.get('title')}' có nội dung: "
                f"{thesis.get('summary')} Nguồn: {thesis.get('source')}."
            ),
            "thought": "Tóm tắt tài liệu được cấp quyền từ Observation.",
        }

    def _summarize_similarity(self, history):
        observation = self._observation(history, "similarity")
        advisor = observation.get("advisor", {})
        return {
            "type": "text",
            "content": (
                f"Điểm compatibility là {advisor.get('compatibility')}; "
                f"giảng viên còn quota {advisor.get('remaining_quota')} và "
                f"quota_valid={advisor.get('quota_valid')}. Khuyến nghị xem xét "
                "cặp ghép này; chưa tạo phân bổ chính thức. "
                f"Nguồn dữ liệu {observation.get('data_version')}, model "
                f"{observation.get('model_version')}."
            ),
            "thought": "Đã đủ dữ liệu; đưa ra khuyến nghị có căn cứ và không commit.",
        }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
        self.min_request_interval = max(
            float(os.getenv("GEMINI_MIN_REQUEST_INTERVAL_SECONDS", "0")), 0.0
        )
        self._last_request_at = 0.0

    def _wait_for_rate_limit(self):
        """Giãn cách request để phù hợp quota Gemini free tier khi được cấu hình."""
        elapsed = time.monotonic() - self._last_request_at
        wait_seconds = self.min_request_interval - elapsed
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        self._last_request_at = time.monotonic()

    @staticmethod
    def _allow_mock_fallback() -> bool:
        return os.getenv("LLM_ALLOW_MOCK_FALLBACK", "true").lower() in {
            "1", "true", "yes", "on"
        }

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            self._wait_for_rate_limit()
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            if not self._allow_mock_fallback():
                raise RuntimeError(f"Gemini API request failed: {e}") from e
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Dùng model types để tránh SDK hiểu dictionary Tool là callable.
            function_declarations = []
            for tool in tools_schema:
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                parameters = sanitize_schema_for_gemini(tool["parameters"])
                function_declarations.append(
                    types.FunctionDeclaration(
                        name=tool["name"],
                        description=tool.get("description", ""),
                        parameters=types.Schema.model_validate(parameters),
                    )
                )

            gemini_tools = (
                [types.Tool(function_declarations=function_declarations)]
                if function_declarations
                else None
            )

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=gemini_tools,
                temperature=0.2
            )

            self._wait_for_rate_limit()
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            if not self._allow_mock_fallback():
                raise RuntimeError(f"Gemini API request failed: {e}") from e
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
