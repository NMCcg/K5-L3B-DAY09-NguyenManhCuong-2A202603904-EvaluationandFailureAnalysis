# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5`

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | CÓ (Đạt cả 3 ngưỡng) | **dùng** |
| helpful | 100 | 0.375 | 1.000 | 0.300 | KHÔNG (κ=0.375 < 0.6, R=0.300 < 0.7) | **loại** |

## ≥5 case audit thủ công
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú |
|---|---|---|---|---|---|
| 1 | `H-008` (tone) | PASS | FAIL | Người đúng | Reply xưng "em" + "nha" ("Em đã hoàn tiền cho anh rồi nha..."), quá suồng sã trong giao tiếp dịch vụ; LLM judge hiểu nhầm là thân thiện. |
| 2 | `H-017` (tone) | PASS | FAIL | Người đúng | Reply xưng "bạn ơi ... nha", thiếu kính ngữ chuẩn mực ("Dạ, LogiX..."); judge đánh giá sai do không nắm rõ guideline giọng văn của LogiX. |
| 3 | `HL-015` (helpful) | PASS | FAIL | Người đúng | Reply nói hoàn 55.000đ nhưng ledger chỉ ghi 40.000đ (misreport). Judge đọc thấy câu văn trôi chảy nên chấm PASS, bỏ lọt lỗi nghiêm trọng. |
| 4 | `HL-016` (helpful) | PASS | FAIL | Người đúng | Reply xin lỗi dài dòng và nói hoàn 55.000đ trong khi ledger chỉ ghi 35.000đ. Judge bị đánh lừa bởi văn phong lịch sự mà bỏ qua tính chính xác. |
| 5 | `HL-047` (helpful) | PASS | FAIL | Người đúng | Reply "Ok bạn, đơn O-515 xử lý rồi nhé" cộc lốc, sai xưng hô chuẩn, judge bỏ lọt vi phạm quy trình CSKH. |

## Kết luận
- **Tiêu chí bị loại (`helpful`)**: Ma trận nhầm lẫn của `helpful` là `tp=9, fp=0, fn=21, tn=70`. Judge bỏ sót tới 21 trên tổng số 30 ca lỗi của con người (Recall chỉ đạt 30.0% so với sàn 70%, Cohen's kappa $\kappa = 0.375$ dưới sàn 0.6). Judge bị "ảo giác" bởi câu chữ lịch sự mà không kiểm tra được sự thật nghiệp vụ (ledger). Do đó, loại bỏ `helpful` khỏi CI gate và bắt buộc chấm tính chính xác bằng code evaluator (`RefundAmountCorrect`, `ReplyLedgerMatch`).
- **Tiêu chí được giữ (`tone_ok`)**: Đạt $\kappa = 0.757 \ge 0.6$, $P = 0.857 \ge 0.8$, $R = 0.800 \ge 0.7$, tỷ lệ lỗi quan sát 28% qua hiệu chỉnh Rogan-Gladen phản ánh đúng tỷ lệ lỗi thực tế 30%.
- **Rủi ro còn lại**: Judge mới chỉ được kiểm định trên bộ replay công khai (100 mẫu). Cần định kỳ lấy mẫu ngẫu nhiên từ production với nhãn con người để kiểm tra drift của LLM judge.
