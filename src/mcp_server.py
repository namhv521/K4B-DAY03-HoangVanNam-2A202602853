"""
🔌 MODEL CONTEXT PROTOCOL (MCP) SERVER MODULE
Mô phỏng kiến trúc MCP Server (Client-Server Architecture) cung cấp công cụ chuẩn hóa.
"""

import json
import sys
from typing import Dict, Any, List
from tools import TOOLS_SCHEMA, dispatch_tool_call

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class MCPAcademicServer:
    """
    Giả lập MCP Server tuân thủ chuẩn giao thức Model Context Protocol
    """
    def __init__(self, server_name: str = "vinuni-academic-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"
        
    def list_tools(self) -> List[Dict[str, Any]]:
        """Trả về danh sách các Tools chuẩn giao thức MCP"""
        return TOOLS_SCHEMA
        
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Thực thi tool và đóng gói kết quả theo JSON-RPC 2.0.

        Tool backend luôn trả JSON string. MCP Server chịu trách nhiệm parse
        chuỗi đó thành object để Agent nhận Observation có cấu trúc.
        """
        try:
            raw_result = dispatch_tool_call(tool_name, arguments)
            content = json.loads(raw_result)
            if not isinstance(content, dict):
                raise ValueError("Tool response must be a JSON object")
        except (json.JSONDecodeError, TypeError, ValueError):
            content = {
                "status": "INVALID_TOOL_RESPONSE",
                "message": "Tool backend không trả về JSON object hợp lệ.",
            }

        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content,
        }


if __name__ == "__main__":
    print("==========================================================")
    print("🔌 KIỂM THỬ ĐỘC LẬP MCP SERVER (vinuni-academic-mcp-server)")
    print("==========================================================")
    
    server = MCPAcademicServer()
    tools = server.list_tools()
    print(
        f"✅ [MCP SERVER] Đã khởi tạo thành công {server.server_name} "
        f"(Version: {server.version})"
    )
    print(f"📦 Số lượng Tools công bố qua MCP: {len(tools)}")
    
    # Kiểm tra trạng thái Task 1.2 (Tool Schemas)
    required_tools = {"query_matching_context", "assign_student_advisor"}
    published_tools = {tool.get("name") for tool in tools}
    schemas_complete = all(
        tool.get("parameters", {}).get("properties")
        and tool.get("parameters", {}).get("required")
        for tool in tools
    )
    if required_tools.issubset(published_tools) and schemas_complete:
        print("✅ [TASK 1.2]: Hai Matching Tool Schemas đã được khai báo đầy đủ.")
    else:
        print("⏳ [TASK 1.2]: Matching Tool Schemas chưa đầy đủ trong 'src/tools.py'.")

    # Kiểm tra Task 2.1 (call_tool)
    test_result = server.call_tool(
        "query_matching_context",
        {"query_type": "student_skills", "student_id": "SV001"},
    )
    if not test_result.get("result"):
        print("⏳ [TASK 2.1]: MCP Server chưa trả Observation có dữ liệu.")
    else:
        print("✅ [TASK 2.1]: Dispatch tool 'query_matching_context' thành công:")
        print(f"   Phản hồi JSON-RPC: {json.dumps(test_result, ensure_ascii=False)}")
