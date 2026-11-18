# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (Case C-006@11)

| Trường | Nội dung |
|---|---|
| Trial | `stale_clause C-006@11`, run ID `run-stale_clause-C-006-11` |
| Triệu chứng | Grader `RefundAmountCorrect` và `TrialPass` báo FAIL; Reply thông báo đã hoàn 300.000đ cho đơn O-606 trong khi nhãn kỳ vọng là từ chối (`status: denied`, `refund_vnd: 0`). |
| Bước sai đầu tiên | Event 5: `quote` `{"amount_vnd": 300000, "clause_ids": ["SHIP-LATE-OLD"], "parts": {"full_paid": 300000}}` |
| Vì sao là bước *đầu tiên* | Các event trước đó (Event 1 `handoff`, Event 2 `investigator`) thực hiện tra cứu hoàn toàn chính xác thông tin đơn hàng O-606 từ DB (`delay_days: 2`, `paid_vnd: 300000`). Đến Event 5, agent mới bị bẫy bởi ticket để trích xuất điều khoản cũ `SHIP-LATE-OLD` thay vì áp dụng chính sách hiện hành. |
| Failure mode | `FM-06` (`stale_clause — dùng điều khoản cũ`) |
| Đối chứng | Cùng `C-006@11` trên shape `fixed`: Agent chỉ xét chính sách hiện hành `POL-2026-11` (`SHIP-LATE-03`, yêu cầu trễ ≥ 3 ngày). Đơn trễ 2 ngày không đủ điều kiện nên quote trả về 0đ; agent từ chối bồi thường (`status: denied`, `refund_vnd: 0`). |
| Regression test | `test_stale_clause_rejected` (kiểm tra `RefundAmountCorrect`): Assert `snapshot["refund_vnd"] == 0` và `result["status"] == "denied"`. Variant lỗi ra `refund_vnd: 300000` (FAIL), shape `fixed` ra 0đ (PASS). |
| Chưa chắc chắn | Trace chỉ ghi nhận agent lấy điều khoản cũ và tính ra 300.000đ; không chứng minh được MockLLM/agent có đọc trường `is_current: false` và cố tình lờ đi hay do cơ chế trích xuất regex ưu tiên clause có trong ticket. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
