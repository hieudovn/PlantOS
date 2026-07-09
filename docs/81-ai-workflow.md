# PlantOS AI-Assisted Development Workflow

## 1. Purpose

PlantOS sử dụng mô hình multi-agent với phân tách vai trò rõ ràng để đảm bảo:

- Kiến trúc không bị drift qua các session
- Mọi thay đổi đều được review độc lập
- Token được sử dụng hiệu quả (deep reasoning cho design, model nhẹ cho code)
- Tuân thủ constitution (`docs/01-project-constitution.md` §10: "AI output is not accepted without review")

## 2. Role Assignment

```
┌─────────────────────────────────────────────────┐
│  SESSION 1 — DESIGN & PLANNING                   │
│  Model: DeepSeek V4 Pro                          │
│  Vai trò: PM-Designer-Planner                    │
│                                                  │
│  Input: User request, Project docs               │
│  Output: Implementation plan + Coder prompt      │
└────────────────────┬────────────────────────────┘
                     │ prompt file (.md)
                     ▼
┌─────────────────────────────────────────────────┐
│  SESSION 2 — IMPLEMENTATION & TEST               │
│  Model: DeepSeek V4 Flash (hoặc model nhẹ hơn)  │
│  Vai trò: Coder-Executioner + Tester             │
│                                                  │
│  Input: Prompt từ Session 1                      │
│  Output: Code changes + Test results             │
└────────────────────┬────────────────────────────┘
                     │ code + test report
                     ▼
┌─────────────────────────────────────────────────┐
│  SESSION 3 — REVIEW                              │
│  Model: DeepSeek V4 Pro                          │
│  Vai trò: Reviewer-Critic                        │
│                                                  │
│  Input: Code từ Session 2                        │
│  Output: Approval / Rejection / Fixes            │
└─────────────────────────────────────────────────┘
```

## 3. Session Rules

### Session 1 — Designer/Planner (V4 Pro)

**Trách nhiệm:**
- Đọc toàn bộ tài liệu kiến trúc liên quan
- Phân tích yêu cầu, xác định module/files bị ảnh hưởng
- Viết implementation plan chi tiết (từng file, từng function)
- Viết Coder-Executioner prompt, lưu vào `docs/prompts/`
- Duyệt constitution checklist trước khi bàn giao

**Prompt lưu tại:** `docs/prompts/phase1-task<N>-<tên>.md`

**Không làm:**
- Không code trực tiếp (trừ ngoại lệ ở §5)
- Không chạy test
- Không tạo file ngoài `docs/prompts/`

### Session 2 — Coder/Executioner (V4 Flash)

**Trách nhiệm:**
- Đọc prompt từ `docs/prompts/`
- Implement đúng theo kế hoạch, không tự ý mở rộng scope
- Chạy test, báo cáo kết quả
- Ghi lại mọi deviation so với plan

**Không làm:**
- Không tự quyết định kiến trúc
- Không thêm business logic ngoài scope
- **Không sửa docs/reports/runbooks** — chỉ PM-Designer được phép cập nhật tài liệu, báo cáo, runbook. Coder báo cáo kết quả qua file output riêng (test results, CSV, log) hoặc message, không trực tiếp sửa file trong `docs/`.
- Không tạo thư mục/folder mới ngoài plan
- Không tự ý commit thay đổi vào docs/reports/

### Session 3 — Reviewer (V4 Pro)

**Trách nhiệm:**
- Đọc code output từ Session 2
- Kiểm tra constitution compliance
- Xác nhận không bypass UNS/CDM
- Quyết định: Approved / Needs Fix / Rejected
- Nếu lỗi nhỏ → tự sửa (theo §5)
- Nếu lỗi kiến trúc → tạo prompt sửa cho Session 2 mới

## 4. Prompt Template

Mọi Coder-Executioner prompt phải theo format:

```markdown
# [TASK-ID] [Task Name]

## Context
[Tóm tắt task, module liên quan]

## Plan Reference
[Tài liệu thiết kế liên quan]

## Implementation Checklist
- [ ] File 1: [mô tả]
- [ ] File 2: [mô tả]
- [ ] ...

## Exact Files to Create/Modify
| # | File Path | Action | Content Summary |
|---|-----------|--------|-----------------|
| 1 | ...       | CREATE | ...             |
| 2 | ...       | MODIFY | ...             |

## Detailed Instructions
[Code mẫu, logic cần implement]

## Constraints
- [ ] Không bypass UNS/CDM
- [ ] Không UI-to-DB coupling
- [ ] Không hardcode tag/signal
- [ ] Edge/Center tách biệt
- [ ] Không business logic ngoài scope
- [ ] Chỉ tạo file trong plan

## Validation
- [ ] Step 1: ...
- [ ] Step 2: ...

## Expected Output Format
1. Files created/modified
2. Test results
3. Issues/deviation
4. Confirmation: no constitution violation
```

## 5. Exception Rules

Designer (V4 Pro) được phép tự sửa code trực tiếp trong Session 3 (Review) khi:

| Tình huống | Hành động |
|---|---|
| Lỗi typo, format, import sai | Tự sửa |
| Thiếu `__init__.py` hoặc file trống | Tự thêm |
| Config sai (port, host, version) | Tự sửa |
| Test thiếu case đơn giản | Tự thêm |
| Dockerfile sai path nhỏ | Tự sửa |
| Lệch nhẹ so với API contract đã duyệt | Tự sửa |

**KHÔNG được tự sửa khi:**

| Tình huống | Hành động |
|---|---|
| Lệch kiến trúc (sai module boundary) | Tạo prompt sửa mới |
| Thiếu cả module | Tạo prompt bổ sung |
| Vi phạm constitution | Tạo prompt sửa + ghi rõ violation |
| Thêm business logic không có trong plan | Tạo prompt revert |
| Thay đổi data model | Yêu cầu ADR trước |

## 6. Prompt File Naming Convention

```
docs/prompts/phase1-task01-repository-structure.md
docs/prompts/phase1-task02-docker-compose-skeleton.md
docs/prompts/phase1-task03-fastapi-backend-skeleton.md
docs/prompts/phase1-task04-postgresql-models.md
...
```

## 7. Session Handoff Checklist

Khi Designer bàn giao cho Coder:

- [ ] Prompt đã lưu trong `docs/prompts/`
- [ ] Tất cả docs tham chiếu đã được đọc
- [ ] Constitution checklist đã duyệt
- [ ] Plan không có ambiguity
- [ ] Constraints rõ ràng, measurable

Khi Coder bàn giao cho Reviewer:

- [ ] Code đã compile / import được
- [ ] Tests pass
- [ ] Deviation được ghi rõ
- [ ] Output format đúng yêu cầu

## 8. Current Phase 1 Progress

| Task | Status | Designer | Coder | Reviewer |
|---|---|---|---|---|
| Task 1: Repository Structure | ✅ Done | V4 Pro | V4 Pro (ngoại lệ: scaffolding) | V4 Pro |
| Task 2: Docker Compose Skeleton | ✅ Done | V4 Pro | V4 Pro (ngoại lệ: scaffolding) | V4 Pro |
| Task 3: FastAPI Backend Skeleton | ✅ Done | V4 Pro | V4 Pro (ngoại lệ: scaffolding) | V4 Pro |
| Task 4: PostgreSQL Models | 🔜 Next | V4 Pro | V4 Flash | V4 Pro |
| Task 5: TDengine Historian | ⏳ Pending | — | — | — |
| ... | ... | ... | ... | ... |
