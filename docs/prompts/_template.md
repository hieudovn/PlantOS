# [TASK-ID] [Task Name]

## Context

[Tóm tắt 2-3 câu về task này làm gì, thuộc module nào]

## Plan Reference

- `docs/[tài liệu liên quan].md`
- `docs/adr/ADR-XXXX-...md` (nếu có)

## Implementation Checklist

- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Exact Files to Create/Modify

| # | File Path | Action | Content Summary |
|---|-----------|--------|-----------------|
| 1 | `path/to/file1.py` | CREATE | [mô tả ngắn] |
| 2 | `path/to/file2.py` | MODIFY | [mô tả ngắn] |

## Detailed Instructions

<!-- Mô tả chi tiết logic, code mẫu, schema, API contract -->

### File: `path/to/file1.py`

```python
# Code mẫu nếu cần
```

### File: `path/to/file2.py`

```python
# Code mẫu nếu cần
```

## Constraints

- [ ] Không bypass UNS/CDM
- [ ] Không UI-to-DB coupling (UI không query trực tiếp PostgreSQL, TDengine, MQTT, Kafka)
- [ ] Không hardcode raw tag/signal names
- [ ] Edge/Center responsibilities tách biệt
- [ ] Không business logic ngoài scope task này
- [ ] Chỉ tạo file được liệt kê trong bảng trên
- [ ] Không tạo thư mục mới ngoài plan
- [ ] Chỉ TDengineHistorianAdapter mới biết TDengine schema/connector

## Validation

1. Run: `[lệnh kiểm tra]`
2. Expected: `[kết quả mong đợi]`
3. Run tests: `[lệnh test]`

## Expected Output Format

Sau khi hoàn thành, báo cáo:

```
1. Files created/modified:
   - [file] — [action] — [status]

2. Test results:
   - [test name]: PASSED/FAILED
   - ...

3. Issues / Deviations:
   - [mô tả vấn đề nếu có]

4. Confirmation:
   - [x] No constitution rule violated
   - [x] No UNS/CDM bypass
   - [x] No UI-to-DB coupling
   - [x] Edge/Center separation maintained
```
