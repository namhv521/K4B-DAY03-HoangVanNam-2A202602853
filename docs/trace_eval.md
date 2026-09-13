# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Hoàng Văn Nam
> **Mã Sinh Viên / Mã Học viên:** 2A20260283
> **Chủ đề Lựa chọn:** Đề tài mở — Trợ lý ghép cặp sinh viên thực hiện khóa luận với giảng viên hướng dẫn

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | **4 / 5** | Quy trình gồm nhiều bước: đọc hồ sơ và đề tài, truy xuất kỹ năng giảng viên, tính compatibility, kiểm tra quota/workload rồi đề xuất cặp ghép. Tuy nhiên, phần lớn bước xử lý có cấu trúc và có thể triển khai bằng pipeline hoặc thuật toán tối ưu cố định, nên chưa cần mức suy luận mở cao nhất. |
| **2. Tool Interaction** | **3 / 5** | Tác tử dự kiến dùng `query_matching_context` để tra cứu dữ liệu và `assign_student_advisor` để ghi nhận phân bổ qua MCP Server. Dù vậy, repo tham khảo hiện tập trung vào pipeline dữ liệu và huấn luyện RL; lớp ứng dụng inference/MCP chưa phải thành phần hoàn thiện, nên nhu cầu tương tác tool ở mức khá thay vì bắt buộc xuyên suốt. |
| **3. Dynamic Decision** | **4 / 5** | Lựa chọn giảng viên cho sinh viên hiện tại phụ thuộc vào capacity và workload sau các assignment trước; action masking cũng loại bỏ giảng viên đã đầy quota. Quyết định có tính động rõ ràng nhưng chủ yếu diễn ra trong môi trường và policy RL đã định nghĩa, không phải mọi bước đều cần Agent tự lập kế hoạch lại. |
| **4. Long Horizon Goal** | **3 / 5** | Hệ thống phải duy trì mục tiêu compatibility, fairness và quota trong suốt một cohort, vì lựa chọn hiện tại ảnh hưởng các sinh viên sau. Tuy nhiên, horizon kết thúc trong một episode phân bổ và phiên bản hiện tại chưa có memory, feedback đáng tin cậy hay tự điều chỉnh mục tiêu qua nhiều cohort. |
| **TỔNG ĐIỂM AGENTIC FIT** | **14 / 20** | **14 > 12:** Bài toán phù hợp triển khai Agentic System, nhưng mức phù hợp chỉ ở ngưỡng khá. Agent hữu ích để điều phối tra cứu, giải thích và xác nhận phân bổ; lõi tối ưu vẫn nên do pipeline và policy RL đảm nhiệm. |

### Phạm vi tác tử dự kiến

- **Đầu vào:** hồ sơ/đề tài của sinh viên; chuyên môn, kỹ năng, quota và workload của giảng viên.
- **Tool tra cứu — `query_matching_context`:** lấy hồ sơ liên quan, compatibility và danh sách giảng viên còn capacity.
- **Tool hành động — `assign_student_advisor`:** kiểm tra hard constraint và ghi nhận cặp sinh viên–giảng viên được chọn.
- **Mục tiêu:** tạo phân bổ có compatibility cao, cân bằng workload và không vi phạm quota; kết quả cần được quản trị viên hoặc hội đồng chuyên môn duyệt trước khi áp dụng.

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dưới đây là đoạn trích TC05 từ `docs/trace_waterfall.json`, được sinh bởi
`GeminiProvider` qua Native Tool Calling thật. Matching tool vẫn dùng bộ dữ liệu
mock có version để kiểm thử an toàn; đây không phải kết quả inference từ policy
RL production.

```json
[
  {
    "step": 1,
    "action_type": "TOOL_EXECUTION",
    "query": "Đánh giá mức độ tương đồng giữa SV001 và GV012.",
    "tool_name": "query_matching_context",
    "arguments": {
      "student_id": "SV001",
      "advisor_id": "GV012",
      "query_type": "similarity"
    },
    "observation": {
      "status": "SUCCESS",
      "query_type": "similarity",
      "advisor": {
        "advisor_id": "GV012",
        "compatibility": 0.82,
        "quota": 5,
        "current_load": 3,
        "remaining_quota": 2,
        "quota_valid": true
      },
      "compatibility_method": "precomputed_mock_matching_service",
      "data_version": "mock-curated-2026-09",
      "model_version": "mock-policy-v1"
    },
    "latency_ms": 15240.07
  },
  {
    "step": 2,
    "action_type": "FINAL_ANSWER",
    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
    "output": "Mức độ tương đồng là 0.82; GV012 còn 2 suất. Khuyến nghị xem xét cặp ghép và chưa tạo phân bổ chính thức.",
    "latency_ms": 15991.77
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy trên Gemini API thật, với mock fallback bị vô hiệu hóa khi nghiệm thu.
- **Tổng số Test Cases đã chạy thành công:** **5 / 5** test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** **4 lượt**.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
