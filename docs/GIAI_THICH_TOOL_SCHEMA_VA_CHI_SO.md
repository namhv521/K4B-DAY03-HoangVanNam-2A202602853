# Giải thích Tool Schema và các chỉ số của Matching Agent

## 1. Phạm vi

Hai tool trong `src/tools.py` phục vụ chủ đề ghép cặp sinh viên làm khóa luận
với giảng viên hướng dẫn:

1. `query_matching_context`: tra cứu dữ liệu, không thay đổi trạng thái;
2. `assign_student_advisor`: tạo đề xuất hoặc ghi nhận phân bổ có kiểm soát.

Execution layer hiện dùng **mock data cho Lab 3**, chưa gọi trực tiếp model RL.
Vì vậy, kết quả hiện tại chỉ chứng minh schema, MCP routing và guardrail hoạt
động; không chứng minh policy RL đã sẵn sàng triển khai thực tế.

## 2. Cấu trúc chung của Tool Schema

Mỗi phần tử trong `TOOLS_SCHEMA` có ba thành phần:

| Trường | Nhiệm vụ |
| :--- | :--- |
| `name` | Tên duy nhất để LLM yêu cầu gọi tool. |
| `description` | Giúp LLM hiểu khi nào nên và không nên gọi tool. |
| `parameters` | JSON Schema mô tả kiểu dữ liệu, enum, miền giá trị và trường bắt buộc. |

Trong `parameters`:

- `type: object` yêu cầu arguments là JSON object;
- `properties` mô tả từng tham số;
- `required` liệt kê tham số luôn bắt buộc;
- `enum` giới hạn tập giá trị hợp lệ;
- `minimum`/`maximum` giới hạn miền số;
- `additionalProperties: false` không cho phép LLM tự thêm tham số ngoài schema.

Schema hướng dẫn provider tạo arguments đúng, nhưng execution layer vẫn phải
kiểm tra lại vì dữ liệu do LLM tạo ra không được xem là đáng tin cậy.

## 3. Tool `query_matching_context`

### 3.1. Nhiệm vụ

Tool tập hợp ngữ cảnh trước khi Agent giải thích hoặc khuyến nghị. `query_type`
quyết định nghiệp vụ cụ thể:

| `query_type` | Dữ liệu trả về | ID bắt buộc |
| :--- | :--- | :--- |
| `student_skills` | Skill, role, nguồn profile sinh viên và tối đa `top_k` ứng viên. | `student_id` |
| `advisor_skills` | Skill, lĩnh vực nghiên cứu, evidence, quota và workload. | `advisor_id` |
| `historical_thesis` | Tiêu đề, tóm tắt, công nghệ, nguồn và mức truy cập khóa luận. | `student_id` |
| `similarity` | Dữ liệu hai phía, compatibility, quota và phiên bản nguồn. | `student_id`, `advisor_id` |

Tool này là **read-only**: gọi tool không được tăng workload, giảm quota hoặc
ghi assignment.

### 3.2. Tham số

#### `query_type`

- Kiểu: `string`.
- Bắt buộc.
- Chỉ nhận bốn giá trị trong bảng trên.
- Nếu sai, backend trả `INVALID_INPUT`.

#### `student_id`

- Kiểu: `string`.
- Ví dụ mock: `SV001`.
- Bắt buộc khi tra cứu skill sinh viên, khóa luận hoặc similarity.
- Backend bỏ khoảng trắng và chuyển ID thành chữ hoa.

#### `advisor_id`

- Kiểu: `string`.
- Ví dụ mock: `GV012`.
- Bắt buộc khi tra cứu skill giảng viên hoặc similarity.
- Backend cũng chuẩn hóa trước khi tìm kiếm.

#### `top_k`

- Kiểu: `integer`.
- Miền hợp lệ: `1..10`.
- Mặc định: `3`.
- Là số ứng viên tối đa được trả về, không phải điểm chất lượng.

## 4. Tool `assign_student_advisor`

### 4.1. Nhiệm vụ

Tool kiểm tra cặp sinh viên–giảng viên và chạy một trong hai chế độ:

- `dry_run`: mô phỏng, không đổi workload và không ghi assignment;
- `commit`: ghi assignment vào mock store và tăng workload sau khi có
  `approval_id`.

Tool luôn kiểm tra hồ sơ, compatibility và quota. LLM không được phép bỏ qua
những kiểm tra này.

### 4.2. Tham số

| Tham số | Kiểu | Bắt buộc | Ý nghĩa |
| :--- | :---: | :---: | :--- |
| `student_id` | string | Có | Sinh viên cần được phân bổ. |
| `advisor_id` | string | Có | Giảng viên được đề xuất. |
| `mode` | enum | Có | Chỉ nhận `dry_run` hoặc `commit`. |
| `approval_id` | string | Khi commit | Mã phê duyệt của admin/hội đồng. |

`approval_id` là điều kiện phụ thuộc `mode`. Execution layer kiểm tra điều kiện
này để giữ tương thích giữa các provider Native Tool Calling.

## 5. Giải thích các chỉ số và trường đầu ra

### 5.1. `compatibility`

- Miền giá trị: `0.0..1.0`.
- Càng cao thì đề tài/skill sinh viên càng tương đồng với chuyên môn giảng viên
  theo matching service.
- Mock hiện dùng `0.82` cho cặp `SV001`–`GV012`.
- Không phải xác suất thành công và không tự tạo ra quyết định đạt/không đạt.
- Agent phải lấy giá trị từ Observation, không tự tính hay bịa điểm.

Trong hệ thống thật, compatibility có thể đến từ TF-IDF cosine hoặc backend đã
version hóa. Mock chỉ lưu điểm tính sẵn để kiểm thử tool flow.

### 5.2. `quota`

Số sinh viên tối đa giảng viên được phép hướng dẫn trong đợt phân bổ. Đây là
**hard constraint**: tool phải từ chối khi quota đã đầy.

### 5.3. `current_load`

Số sinh viên đang được gán cho giảng viên trước hành động. `dry_run` không làm
thay đổi chỉ số này.

### 5.4. `remaining_quota`

Capacity hiện còn:

```text
remaining_quota = max(quota - current_load, 0)
```

Nếu bằng `0`, không được tạo assignment mới.

### 5.5. `quota_valid`

- `true`: `current_load < quota`;
- `false`: giảng viên không còn capacity.

`true` chỉ chứng minh quota hợp lệ, không chứng minh cặp ghép là tối ưu.

### 5.6. `load_before` và `load_after`

- `load_before`: tải trước assignment;
- `load_after`: tải dự kiến hoặc thực tế sau assignment.

Trong `dry_run`, `load_after` chỉ là mô phỏng. Trong `commit`, backend mới cập
nhật workload.

### 5.7. `remaining_quota_after`

Capacity còn lại nếu áp dụng assignment:

```text
remaining_quota_after = remaining_quota - 1
```

Chỉ số giúp đánh giá ảnh hưởng của lựa chọn hiện tại lên phần còn lại của cohort.

### 5.8. `skills`

Danh sách kỹ năng đã được pipeline trích xuất. Thiếu một skill trong danh sách
không có nghĩa cá nhân chắc chắn không có skill đó; có thể dữ liệu chưa ghi nhận.

### 5.9. `skill_evidence`

Mỗi bằng chứng gồm:

- `skill`: kỹ năng được hỗ trợ;
- `source`: artifact chứa bằng chứng;
- `evidence`: mô tả ngắn về bằng chứng.

Agent chỉ được giải thích dựa trên evidence trả về.

### 5.10. `primary_role`

Vai trò kỹ thuật chính được pipeline gán từ đề tài, framework, công cụ và phương
pháp. Đây là đặc trưng matching, không phải đánh giá toàn diện sinh viên.

### 5.11. `research_fields`

Các lĩnh vực nghiên cứu đã ghi nhận của giảng viên. Trường này bổ sung ngữ cảnh
cho skill nhưng không tự quyết định assignment.

### 5.12. `data_version`

Phiên bản snapshot dữ liệu tạo Observation. Mock hiện trả
`mock-curated-2026-09`; production phải trả phiên bản curated có thể truy vết.

### 5.13. `model_version`

Phiên bản policy/matching service. Mock hiện trả `mock-policy-v1`; đây không
phải PPO production đã vượt evaluation gate.

### 5.14. `compatibility_method`

Phương pháp tạo điểm similarity. Mock dùng
`precomputed_mock_matching_service`; hệ thống thật phải ghi backend/model thực.

### 5.15. `policy`

Tên policy/backend dùng cho hành động. Mock trả `mock_matching_policy`;
production chỉ nên dùng model hoặc fallback đã được phê duyệt.

### 5.16. `requires_human_approval`

- `true` khi `dry_run`: mới là đề xuất;
- `false` sau `commit` hợp lệ: backend đã nhận mã phê duyệt.

Trường này không thay thế authorization thực tế ở backend.

## 6. Các trạng thái phản hồi

| `status` | Ý nghĩa | Agent cần làm gì |
| :--- | :--- | :--- |
| `SUCCESS` | Tra cứu thành công. | Tổng hợp đúng Observation và nêu nguồn. |
| `PROPOSED` | Dry-run hợp lệ, chưa ghi. | Nêu rõ đây là đề xuất và cần phê duyệt. |
| `COMMITTED` | Đã ghi assignment có phê duyệt. | Xác nhận cặp ghép và approval ID. |
| `INVALID_INPUT` | Thiếu/sai tham số. | Yêu cầu sửa đầu vào, không tự đoán. |
| `NOT_FOUND` | Không có hồ sơ/tài liệu/điểm. | Thông báo thiếu dữ liệu, không bịa. |
| `ACCESS_DENIED` | Không có quyền đọc tài liệu. | Từ chối, không tiết lộ nội dung. |
| `QUOTA_EXCEEDED` | Giảng viên đã đầy quota. | Không phân bổ; đề nghị lựa chọn khác. |
| `APPROVAL_REQUIRED` | Commit thiếu mã phê duyệt. | Không ghi và yêu cầu phê duyệt. |
| `UNKNOWN_TOOL` | Tool không có trong router. | Không giả vờ đã thực hiện. |
| `EXECUTION_ERROR` | Lỗi nội bộ. | Báo lỗi an toàn, không lộ stack trace. |

## 7. Ví dụ gọi tool

### Tra cứu skill sinh viên

```json
{
  "tool_name": "query_matching_context",
  "arguments": {
    "query_type": "student_skills",
    "student_id": "SV001",
    "top_k": 3
  }
}
```

### Tra cứu skill giảng viên

```json
{
  "tool_name": "query_matching_context",
  "arguments": {
    "query_type": "advisor_skills",
    "advisor_id": "GV012"
  }
}
```

### Đọc khóa luận cũ

```json
{
  "tool_name": "query_matching_context",
  "arguments": {
    "query_type": "historical_thesis",
    "student_id": "SV001"
  }
}
```

### Lấy điểm similarity

```json
{
  "tool_name": "query_matching_context",
  "arguments": {
    "query_type": "similarity",
    "student_id": "SV001",
    "advisor_id": "GV012"
  }
}
```

### Tạo đề xuất an toàn

```json
{
  "tool_name": "assign_student_advisor",
  "arguments": {
    "student_id": "SV001",
    "advisor_id": "GV012",
    "mode": "dry_run"
  }
}
```

### Commit có phê duyệt

```json
{
  "tool_name": "assign_student_advisor",
  "arguments": {
    "student_id": "SV001",
    "advisor_id": "GV012",
    "mode": "commit",
    "approval_id": "APPROVAL-2026-001"
  }
}
```

## 8. Validation tại execution layer

Ngoài JSON Schema, `src/tools.py` kiểm tra lại:

- `query_type` và `mode` có thuộc enum;
- `top_k` là số nguyên trong `1..10`;
- ID bắt buộc theo từng nghiệp vụ;
- hồ sơ và compatibility có tồn tại;
- quota còn lại;
- `approval_id` khi commit;
- tham số lạ/thiếu và lỗi nội bộ được chuẩn hóa an toàn.

Nguyên tắc: **không tin arguments chỉ vì chúng do LLM tạo ra**.

## 9. Giới hạn hiện tại

- Dữ liệu và compatibility là mock.
- Chưa gọi model RL hoặc inference service thật.
- Mock chỉ kiểm tra `approval_id` có giá trị; production phải xác thực danh tính,
  quyền và audit record.
- Assignment commit chỉ tồn tại trong bộ nhớ tiến trình.
- Prompt, MCP Server và ReAct loop đã được đồng bộ; Gemini Native Tool Calling
  đã nghiệm thu. Inference RL production vẫn chưa được kết nối.

## 10. Liên kết

- [`src/tools.py`](../src/tools.py)
- [`config/test_cases.json`](../config/test_cases.json)
- [`HUONG_DAN_SU_DUNG_RL_MATCHING_AGENT.md`](HUONG_DAN_SU_DUNG_RL_MATCHING_AGENT.md)
- [Repository nguồn](https://github.com/namhv521/Matching_system_ReinforcementLearning)