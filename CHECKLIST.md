# Checklist hoàn thành Lab 3

> Tổng hợp từ toàn bộ 6 file Markdown trong repository: `README.md`,
> `docs/CODELAB.md`, `docs/DANH_SACH_DE_TAI.md`,
> `docs/SO_TAY_THUC_HANH.md`, `docs/trace_eval.md` và
> `src/ai_levels/README.md`.
>
> **Quy ước:** `[x]` là trạng thái đã kiểm chứng trực tiếp trong repository;
> `[ ]` là việc chưa hoàn thành hoặc chưa có đủ bằng chứng để xác nhận.
> Trạng thái được rà soát ngày **13/09/2026**.

## 0. Phạm vi bài làm

- [x] Làm bài cá nhân trên repository đã fork về GitHub cá nhân.
- [x] Repository hiện dùng đúng định dạng theo ca học:
      `K4B-DAY03-HoangVanNam-2A202602853`.
- [ ] Không chỉnh sửa/debug mã nguồn trong `src/ai_levels/` vì đây chỉ là code
      tham khảo kiến trúc.
- [ ] Chỉ tập trung hoàn thiện các artifact bắt buộc:
  - `src/tools.py`
  - `src/mcp_server.py`
  - `src/app.py`
  - `config/test_cases.json`
  - `docs/trace_waterfall.json`
  - `docs/trace_eval.md`

## 1. Chuẩn bị môi trường

- [x] Dùng Python thuộc dải hỗ trợ 3.10–3.12 (đã phát hiện Python 3.12.9).
- [ ] Tạo môi trường ảo `.venv` bằng `python -m venv .venv`.
- [ ] Kích hoạt `.venv` và cài thư viện bằng
      `pip install -r requirements.txt`.
- [x] Tạo file `.env` từ `.env.example`.
- [x] Tạo `config/test_cases.json` từ `config/test_cases.example.json`.
- [x] Đã cấu hình ít nhất một API key thật trong `.env`.
- [ ] Chạy baseline `python src/app.py --all` và xác nhận môi trường hoạt động.

## 2. Phần 1 — Agentic Fit & Tool Schemas (45 phút)

### 2.1. Chọn và đánh giá đề tài

- [x] Chọn một đề tài trong `docs/DANH_SACH_DE_TAI.md` hoặc đề tài mở.
- [x] Bảo đảm đề tài có tối thiểu hai công cụ:
  - một công cụ tra cứu thông tin;
  - một công cụ hành động/đặt lịch/cập nhật.
- [x] Điền họ tên học viên trong `docs/trace_eval.md`.
- [x] Điền MSSV/mã học viên trong `docs/trace_eval.md`.
- [x] Điền tên chủ đề đã chọn trong `docs/trace_eval.md`.
- [x] Chấm điểm từ 1–5 và giải trình cho đủ bốn tiêu chí Agentic Fit:
  - Multi-step Reasoning;
  - Tool Interaction;
  - Dynamic Decision;
  - Long Horizon Goal.
- [x] Tính tổng điểm Agentic Fit trên thang 20; mục tiêu phù hợp Agent là
      trên 12/20.

### 2.2. Hoàn thiện bộ test

- [x] `config/test_cases.json` có đủ năm mục TC01–TC05.
- [x] TC01 kiểm tra khả năng giới thiệu đúng phạm vi hỗ trợ mà không gọi tool.
- [x] TC02 và TC03 kiểm tra tra cứu skill sinh viên/giảng viên kèm bằng chứng.
- [x] TC04 kiểm tra đọc tài liệu khóa luận cũ, nguồn dữ liệu và quyền truy cập.
- [x] TC05 kiểm tra đánh giá tương đồng đa bước, compatibility và quota.
- [x] Xác nhận `config/test_cases.json` không còn chuỗi `TODO`.

### 2.3. Khai báo Tool Schema

- [x] Khai báo JSON Schema cho tool tra cứu `query_matching_context`.
- [x] Khai báo bốn nghiệp vụ: skill sinh viên, skill giảng viên, khóa luận cũ
      và similarity.
- [x] Khai báo JSON Schema cho tool hành động `assign_student_advisor`.
- [x] Khai báo đủ `student_id`, `advisor_id`, `mode`, `approval_id` và trường
      bắt buộc phù hợp.
- [x] Đồng bộ execution layer và `TOOL_ROUTER` với hai schema mới.
- [x] Xóa/giải quyết toàn bộ marker `TODO 1.2` trong `src/tools.py`.

### Checkpoint 1

- [x] `docs/trace_eval.md` có Scoring Matrix đầy đủ điểm và giải trình.
- [x] `config/test_cases.json` không còn `TODO`.
- [x] `TOOLS_SCHEMA` công bố đủ hai tool với schema hợp lệ.

## 3. Phần 2 — ReAct Loop & MCP Integration (60 phút)

### 3.1. MCP Server

- [x] Hoàn thiện `MCPAcademicServer.call_tool()` trong `src/mcp_server.py`:
  - gọi `dispatch_tool_call(tool_name, arguments)`;
  - dùng `json.loads()` chuyển kết quả thành dictionary;
  - trả phản hồi có `jsonrpc: "2.0"`, `server`, `tool` và `result`.
- [x] Xóa/giải quyết marker `TODO 2.1`; hàm không còn trả `{}` mặc định.
- [x] Chạy `python src/mcp_server.py`.
- [x] Xác nhận MCP Server khởi tạo thành công và công bố đúng hai tools.
- [x] Xác nhận `query_matching_context` trả phản hồi JSON-RPC có dữ liệu.

### 3.2. ReAct Agent

- [x] Rà soát/hoàn thiện `run_react_agent()` trong `src/app.py`.
- [x] Xác nhận vòng lặp giới hạn bởi `MAX_ITERATIONS`.
- [x] Xử lý đúng phản hồi `type == "text"` để tạo Final Answer và dừng.
- [x] Xử lý đúng phản hồi `type == "tool_call"`:
  - lấy tên tool và arguments;
  - gọi MCP Server;
  - ghi Observation;
  - dùng kết quả tool để tạo Final Answer.
- [x] Xác nhận trace có đủ chuỗi
      Thought → Action → Observation → Final Answer.
- [x] Xác nhận Agent không bịa dữ liệu khi tool trả `NOT_FOUND` hoặc lỗi.

### Checkpoint 2

- [x] `python src/mcp_server.py` chạy không lỗi.
- [x] `python src/app.py --all` chạy không gặp lỗi code ở chế độ mock offline.
- [x] Observation từ MCP không còn là object rỗng `{}`.

## 4. Phần 3 — Test Execution & Waterfall Trace (45 phút)

- [x] `.env` có API key thật và log nghiệm thu xác nhận dùng `GeminiProvider`.
- [x] Chạy đủ năm test case bằng LLM API thật với
      `python src/app.py --all`.
- [x] Thử chế độ tương tác bằng `python src/app.py --interactive`, sau đó gõ
      `exit` hoặc `quit` để thoát.
- [x] File `docs/trace_waterfall.json` đã tồn tại.
- [x] Tạo lại `docs/trace_waterfall.json` sau khi hoàn thiện code và test cases.
- [x] Xác nhận trace mới đến từ LLM API thật, không phải
      `MockOfflineProvider`/`Mock Agent Response`.
- [x] Xác nhận trace chứa đủ:
  - số bước (`step`);
  - câu hỏi (`query`);
  - suy luận (`thought`);
  - loại hành động (`action_type`);
  - tên tool và arguments khi có gọi tool;
  - Observation có dữ liệu;
  - Final Answer;
  - độ trễ `latency_ms`.
- [x] Xác nhận cả 5/5 test case thành công và hành vi khớp
      `expected_behavior`.

## 5. Hoàn thiện báo cáo `docs/trace_eval.md`

- [x] Thay toàn bộ placeholder `[Điền ...]` bằng thông tin thật.
- [x] Hoàn thiện Agentic Fit Scoring Matrix và tổng điểm.
- [x] Thay đoạn JSON mẫu bằng một trace tiêu biểu lấy từ lần chạy API thật.
- [x] Đánh dấu đã dùng API thật sau khi kiểm chứng.
- [x] Điền tổng số test case chạy thành công trên tổng số 5.
- [x] Điền số lượt gọi tool chính xác qua MCP Server.
- [ ] Ghi nhận trạng thái Commit/Push sau khi đã thực hiện thật.

## 6. Self-audit theo rubric 100%

- [x] **Agentic Fit & Tool Specs (25%):** có Scoring Matrix đầy đủ, năm test
      case tùy biến và hai Tool Schema hợp lệ.
- [x] **ReAct Loop & MCP Integration (35%):** ReAct Loop và Native Tool
      Calling chạy qua MCP Server bằng Gemini/OpenAI API thật.
- [x] **Waterfall Trace & Observation (25%):** trace có đầy đủ Thought,
      Action, Observation, Final Answer và `latency_ms`.
- [ ] **Git Repository & Submission (15%):** repository sạch, đủ artifact,
      commit/push và nộp đúng hạn.

## 7. Đóng gói và nộp bài (30 phút)

- [ ] Kiểm tra `git status`; không bỏ sót file cần nộp.
- [ ] Không commit `.env`, API key, secret hoặc dữ liệu nhạy cảm.
- [ ] Xác nhận trên GitHub có đủ `src/`, `config/test_cases.json`,
      `docs/trace_waterfall.json` và `docs/trace_eval.md`.
- [ ] Commit thay đổi, ví dụ:
      `git commit -m "feat: complete Day 03 Lab Chatbot vs ReAct Agent"`.
- [ ] Push nhánh `main` lên GitHub cá nhân.
- [ ] Mở repository GitHub và kiểm tra lại file sau khi push.
- [ ] Dán URL repository GitHub cá nhân vào LMS VLearn.
- [ ] Xác nhận VLearn đã ghi nhận bài nộp.

## 8. Các vấn đề đang chặn nghiệm thu

- [ ] `.venv` chưa tồn tại trong máy tại thời điểm rà soát.

## 9. Lệnh kiểm tra cuối

```powershell
python src/mcp_server.py
python src/app.py --all
git status
```

Kết quả tối thiểu trước khi nộp:

- [x] MCP Server công bố hai tools và gọi tool thành công.
- [x] Test suite báo 5/5 test case đã thực thi, 0 test case còn `TODO`.
- [x] Trace được tạo từ LLM thật, Observation không rỗng.
- [x] Báo cáo không còn placeholder.
- [ ] GitHub có đầy đủ artifact và link đã được nộp trên VLearn.