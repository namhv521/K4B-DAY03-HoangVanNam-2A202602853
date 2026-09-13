"""Tool schemas và mock execution layer cho Student–Advisor Matching Agent."""

import json
from typing import Any, Dict


# Native Tool Calling schemas (Task 1.2 / checklist 2.3).
TOOLS_SCHEMA = [
    {
        "name": "query_matching_context",
        "description": (
            "Tra cứu skill sinh viên, skill giảng viên, tài liệu khóa luận cũ "
            "hoặc độ tương đồng phục vụ ghép cặp. Tool chỉ đọc dữ liệu."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string",
                    "enum": [
                        "student_skills",
                        "advisor_skills",
                        "historical_thesis",
                        "similarity",
                    ],
                    "description": (
                        "Loại dữ liệu cần tra cứu; similarity cần cả student_id "
                        "và advisor_id."
                    ),
                },
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên, ví dụ SV001.",
                },
                "advisor_id": {
                    "type": "string",
                    "description": "Mã giảng viên, ví dụ GV012.",
                },
                "top_k": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 3,
                    "description": "Số ứng viên trả về, từ 1 đến 10.",
                },
            },
            "required": ["query_type"],
            "additionalProperties": False,
        },
    },
    {
        "name": "assign_student_advisor",
        "description": (
            "Tạo đề xuất dry-run hoặc ghi nhận phân bổ sinh viên–giảng viên sau "
            "khi kiểm tra compatibility, quota và phê duyệt."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần phân bổ, ví dụ SV001.",
                },
                "advisor_id": {
                    "type": "string",
                    "description": "Mã giảng viên được chọn, ví dụ GV012.",
                },
                "mode": {
                    "type": "string",
                    "enum": ["dry_run", "commit"],
                    "description": (
                        "dry_run chỉ mô phỏng; commit ghi nhận và cần approval_id."
                    ),
                },
                "approval_id": {
                    "type": "string",
                    "description": "Mã phê duyệt bắt buộc khi mode=commit.",
                },
            },
            "required": ["student_id", "advisor_id", "mode"],
            "additionalProperties": False,
        },
    },
]


# Mock data chỉ dùng để kiểm thử Lab 3. Production phải gọi matching service.
DATA_VERSION = "mock-curated-2026-09"
MODEL_VERSION = "mock-policy-v1"

STUDENT_PROFILES = {
    "SV001": {
        "student_id": "SV001",
        "student_name": "Nguyễn Minh Anh",
        "skills": ["Python", "Machine Learning", "Data Analysis", "NLP"],
        "primary_role": "Machine Learning",
        "skill_source": "student_profiles.csv",
        "thesis": {
            "title": "Phát hiện gian lận giao dịch bằng học máy",
            "summary": (
                "Nghiên cứu sử dụng đặc trưng giao dịch và mô hình học máy để "
                "nhận diện giao dịch có nguy cơ gian lận."
            ),
            "technologies": ["Python", "scikit-learn", "Pandas"],
            "source": "theses.csv",
            "access_level": "authorized_for_lab",
        },
    }
}

ADVISOR_PROFILES = {
    "GV012": {
        "advisor_id": "GV012",
        "advisor_name": "TS. Lê Minh An",
        "skills": ["Machine Learning", "Data Mining", "Fraud Detection", "Python"],
        "research_fields": ["Artificial Intelligence", "Financial Analytics"],
        "skill_evidence": [
            {
                "skill": "Machine Learning",
                "source": "advisor_skill_evidence.csv",
                "evidence": "Công trình nghiên cứu và học phần về học máy.",
            },
            {
                "skill": "Fraud Detection",
                "source": "advisor_skill_evidence.csv",
                "evidence": "Công trình về phát hiện bất thường giao dịch.",
            },
        ],
        "quota": 5,
        "current_load": 3,
    },
    "GV021": {
        "advisor_id": "GV021",
        "advisor_name": "TS. Trần Thu Hà",
        "skills": ["Natural Language Processing", "Deep Learning", "Python"],
        "research_fields": ["Artificial Intelligence", "Text Mining"],
        "skill_evidence": [
            {
                "skill": "Natural Language Processing",
                "source": "advisor_skill_evidence.csv",
                "evidence": "Công trình nghiên cứu về xử lý văn bản.",
            }
        ],
        "quota": 4,
        "current_load": 4,
    },
}

# Điểm đã tính trước bởi mock matching service; LLM không tự tính lại.
COMPATIBILITY_SCORES = {
    ("SV001", "GV012"): 0.82,
    ("SV001", "GV021"): 0.61,
}
COMMITTED_ASSIGNMENTS: Dict[str, Dict[str, Any]] = {}


def _json_response(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _normalize_id(value: Any) -> str:
    return str(value or "").strip().upper()


def _invalid_input(message: str) -> str:
    return _json_response({"status": "INVALID_INPUT", "message": message})


def _advisor_view(
    advisor: Dict[str, Any], compatibility: float | None = None
) -> Dict[str, Any]:
    quota = advisor["quota"]
    current_load = advisor["current_load"]
    result = {
        **advisor,
        "remaining_quota": max(quota - current_load, 0),
        "quota_valid": current_load < quota,
    }
    if compatibility is not None:
        result["compatibility"] = compatibility
    return result


def execute_query_matching_context(
    query_type: str,
    student_id: str = "",
    advisor_id: str = "",
    top_k: int = 3,
) -> str:
    """Tra cứu ngữ cảnh matching mà không thay đổi trạng thái."""
    valid_types = {
        "student_skills",
        "advisor_skills",
        "historical_thesis",
        "similarity",
    }
    if query_type not in valid_types:
        return _invalid_input(
            "query_type phải là student_skills, advisor_skills, "
            "historical_thesis hoặc similarity."
        )
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 10:
        return _invalid_input("top_k phải là số nguyên từ 1 đến 10.")

    student_id = _normalize_id(student_id)
    advisor_id = _normalize_id(advisor_id)
    student = None
    advisor = None

    if query_type in {"student_skills", "historical_thesis", "similarity"}:
        if not student_id:
            return _invalid_input(f"student_id là bắt buộc với {query_type}.")
        student = STUDENT_PROFILES.get(student_id)
        if not student:
            return _json_response({
                "status": "NOT_FOUND",
                "resource": "student",
                "student_id": student_id,
                "message": f"Không tìm thấy sinh viên '{student_id}'.",
            })

    if query_type in {"advisor_skills", "similarity"}:
        if not advisor_id:
            return _invalid_input(f"advisor_id là bắt buộc với {query_type}.")
        advisor = ADVISOR_PROFILES.get(advisor_id)
        if not advisor:
            return _json_response({
                "status": "NOT_FOUND",
                "resource": "advisor",
                "advisor_id": advisor_id,
                "message": f"Không tìm thấy giảng viên '{advisor_id}'.",
            })

    if query_type == "student_skills":
        candidates = [
            _advisor_view(
                candidate,
                COMPATIBILITY_SCORES.get((student_id, candidate_id), 0.0),
            )
            for candidate_id, candidate in ADVISOR_PROFILES.items()
        ]
        candidates.sort(key=lambda item: item["compatibility"], reverse=True)
        return _json_response({
            "status": "SUCCESS",
            "query_type": query_type,
            "student": {
                key: student[key]
                for key in (
                    "student_id",
                    "student_name",
                    "skills",
                    "primary_role",
                    "skill_source",
                )
            },
            "candidates": candidates[:top_k],
            "data_version": DATA_VERSION,
        })

    if query_type == "advisor_skills":
        return _json_response({
            "status": "SUCCESS",
            "query_type": query_type,
            "advisor": _advisor_view(advisor),
            "data_version": DATA_VERSION,
        })

    if query_type == "historical_thesis":
        thesis = student.get("thesis")
        if not thesis:
            return _json_response({
                "status": "NOT_FOUND",
                "resource": "thesis",
                "student_id": student_id,
                "message": "Không tìm thấy tài liệu khóa luận.",
            })
        if thesis.get("access_level") != "authorized_for_lab":
            return _json_response({
                "status": "ACCESS_DENIED",
                "resource": "thesis",
                "student_id": student_id,
                "message": "Không có quyền truy cập tài liệu khóa luận này.",
            })
        return _json_response({
            "status": "SUCCESS",
            "query_type": query_type,
            "student_id": student_id,
            "thesis": thesis,
            "data_version": DATA_VERSION,
        })

    compatibility = COMPATIBILITY_SCORES.get((student_id, advisor_id))
    if compatibility is None:
        return _json_response({
            "status": "NOT_FOUND",
            "resource": "compatibility",
            "student_id": student_id,
            "advisor_id": advisor_id,
            "message": "Chưa có điểm tương đồng cho cặp được yêu cầu.",
        })
    return _json_response({
        "status": "SUCCESS",
        "query_type": query_type,
        "student": {
            "student_id": student["student_id"],
            "skills": student["skills"],
            "thesis_title": student["thesis"]["title"],
            "thesis_source": student["thesis"]["source"],
        },
        "advisor": _advisor_view(advisor, compatibility),
        "compatibility_method": "precomputed_mock_matching_service",
        "data_version": DATA_VERSION,
        "model_version": MODEL_VERSION,
    })


def execute_assign_student_advisor(
    student_id: str,
    advisor_id: str,
    mode: str,
    approval_id: str = "",
) -> str:
    """Mô phỏng hoặc ghi nhận assignment sau khi kiểm tra ràng buộc."""
    student_id = _normalize_id(student_id)
    advisor_id = _normalize_id(advisor_id)
    approval_id = str(approval_id or "").strip()
    if not student_id or not advisor_id:
        return _invalid_input("student_id và advisor_id không được để trống.")
    if mode not in {"dry_run", "commit"}:
        return _invalid_input("mode phải là dry_run hoặc commit.")

    student = STUDENT_PROFILES.get(student_id)
    advisor = ADVISOR_PROFILES.get(advisor_id)
    if not student or not advisor:
        resource = "student" if not student else "advisor"
        return _json_response({
            "status": "NOT_FOUND",
            "resource": resource,
            "student_id": student_id,
            "advisor_id": advisor_id,
            "message": f"Không tìm thấy {resource} được yêu cầu.",
        })

    compatibility = COMPATIBILITY_SCORES.get((student_id, advisor_id))
    if compatibility is None:
        return _json_response({
            "status": "NOT_FOUND",
            "resource": "compatibility",
            "message": "Chưa có điểm tương đồng cho cặp được yêu cầu.",
        })

    remaining_quota = max(advisor["quota"] - advisor["current_load"], 0)
    if remaining_quota == 0:
        return _json_response({
            "status": "QUOTA_EXCEEDED",
            "student_id": student_id,
            "advisor_id": advisor_id,
            "quota": advisor["quota"],
            "current_load": advisor["current_load"],
            "remaining_quota": 0,
            "message": "Giảng viên đã hết quota; không tạo phân bổ.",
        })
    if mode == "commit" and not approval_id:
        return _json_response({
            "status": "APPROVAL_REQUIRED",
            "student_id": student_id,
            "advisor_id": advisor_id,
            "message": "approval_id là bắt buộc khi mode=commit.",
        })

    result = {
        "status": "PROPOSED" if mode == "dry_run" else "COMMITTED",
        "student_id": student_id,
        "advisor_id": advisor_id,
        "mode": mode,
        "compatibility": compatibility,
        "quota_valid": True,
        "quota": advisor["quota"],
        "load_before": advisor["current_load"],
        "load_after": advisor["current_load"] + 1,
        "remaining_quota_after": remaining_quota - 1,
        "policy": "mock_matching_policy",
        "model_version": MODEL_VERSION,
        "data_version": DATA_VERSION,
        "requires_human_approval": mode == "dry_run",
    }
    if mode == "commit":
        COMMITTED_ASSIGNMENTS[student_id] = {
            "advisor_id": advisor_id,
            "approval_id": approval_id,
        }
        advisor["current_load"] += 1
        result["approval_id"] = approval_id
    return _json_response(result)


TOOL_ROUTER = {
    "query_matching_context": execute_query_matching_context,
    "assign_student_advisor": execute_assign_student_advisor,
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Chuyển yêu cầu tới execution function và chuẩn hóa lỗi."""
    if tool_name not in TOOL_ROUTER:
        return _json_response({
            "status": "UNKNOWN_TOOL",
            "error": f"Tool '{tool_name}' không tồn tại.",
        })
    if not isinstance(arguments, dict):
        return _invalid_input("arguments phải là một JSON object.")
    try:
        return TOOL_ROUTER[tool_name](**arguments)
    except TypeError as exc:
        return _invalid_input(f"Tham số gọi tool không hợp lệ: {exc}")
    except Exception:
        return _json_response({
            "status": "EXECUTION_ERROR",
            "message": "Không thể thực thi tool do lỗi nội bộ.",
        })