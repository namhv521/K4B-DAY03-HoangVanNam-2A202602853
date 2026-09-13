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
        [TASK 2.1] HỌC VIÊN HOÀN THIỆN HÀM THỰC THI TOOL TRÊN MCP SERVER
        Thực thi request gọi Tool theo chuẩn MCP JSON-RPC
        """
        # --------------------------------------------------------------------------
        # TODO 2.1: HỌC VIÊN HOÀN THIỆN HÀM GỌI TOOL CHUẨN MCP JSON-RPC
        # 🎯 YÊU CẦU THỰC THI THUẬT TOÁN:
        # 1. Gọi hàm dispatch_tool_call(tool_name, arguments) để lấy chuỗi JSON kết quả từ Tool Router.
        # 2. Chuyển đổi chuỗi JSON kết quả thành Python Dictionary (dùng json.loads).
        # 3. Đóng gói phản hồi và trả về Dict theo đúng chuẩn giao thức MCP JSON-RPC 2.0:
        #    - Các trường bắt buộc: "jsonrpc": "2.0", "server": self.server_name, "tool": tool_name, "result": content
        # --------------------------------------------------------------------------
        return {}


if __name__ == "__main__":
    print("==========================================================")
    print("🔌 KIỂM THỬ ĐỘC LẬP MCP SERVER (vinuni-academic-mcp-server)")
    print("==========================================================")
    
    server = MCPAcademicServer()
    tools = server.list_tools()
    print(f"✅ Khởi tạo thành công MCP Server: {server.server_name} (Version: {server.version})")
    print(f"📦 Số lượng Tools công bố: {len(tools)}")
    
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

    # Kiểm tra trạng thái TODO 2.1 (call_tool)
    test_result = server.call_tool(
        "query_matching_context",
        {"query_type": "student_skills", "student_id": "SV001"},
    )
    if not test_result:
        print("⏳ [TODO 2.1]: Hàm call_tool() đang trả về rỗng. Học viên hãy hoàn thiện TODO 2.1 trong 'src/mcp_server.py'!")
    else:
        print("✅ [TODO 2.1]: Test dispatch tool 'query_matching_context' thành công:")
        print(f"   Phản hồi JSON-RPC: {json.dumps(test_result, ensure_ascii=False)}")
