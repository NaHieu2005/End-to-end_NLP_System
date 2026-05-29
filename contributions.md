# Contributions

Nhóm thống nhất chia khối lượng công việc cân bằng giữa bốn thành viên, bảo đảm mỗi người đều tham gia cả ba mảng chính: thu thập và xử lý dữ liệu, biên soạn dữ liệu hỏi đáp, và xây dựng/đánh giá mô hình RAG. Tổng số 279 cặp QA thủ công được chia gần như đều nhau theo dải câu hỏi để thuận tiện theo dõi và rà soát chéo.

## Phân công chi tiết

| Họ và tên | MSV | Data annotation | Data collection and processing | Modeling and evaluation |
| --- | --- | --- | --- | --- |
| Vi Minh Hiển | 23020363 | Phụ trách các instance 1-70: biên soạn và kiểm tra đáp án cho nhóm câu hỏi về thông tin nền UET/VNU, hiệu trưởng, tên tiếng Anh, cơ cấu tổ chức và các fact cốt lõi. | Tham gia thu thập dữ liệu từ các nguồn chính thức của UET/VNU, lọc nội dung HTML thô, hỗ trợ chuẩn hóa văn bản và kiểm tra chất lượng corpus sau làm sạch. | Phối hợp xây dựng bộ rule trả lời nhanh cho các fact trọng tâm, hỗ trợ kiểm thử direct answer layer và đối chiếu đầu ra với đáp án tham chiếu. |
| Lê Vũ Hiếu | 23020365 | Phụ trách các instance 71-140: biên soạn câu hỏi cho nhóm nội dung tuyển sinh, mã ngành, điểm chuẩn, học bổng, Hòa Lạc và các thông tin biến động theo năm. | Viết và tinh chỉnh script crawl dữ liệu từ cổng tuyển sinh, trang chính thức và nguồn bổ sung; hỗ trợ chuyển dữ liệu sang JSONL, tạo corpus text và kiểm tra trùng lặp. | Phụ trách cài đặt và tinh chỉnh retriever TF-IDF, title-aware retrieval và chunking; đánh giá chất lượng truy hồi top-k và phân tích lỗi của retrieval-only baseline. |
| Đàm Lê Minh Quân | 23020416 | Phụ trách các instance 141-210: biên soạn câu hỏi về các trường thành viên, quy chế tuyển sinh, thông tin học thuật và các câu hỏi cần suy luận trên nhiều đoạn văn bản. | Tham gia làm sạch dữ liệu Wikipedia/news, xử lý citation, template và nhiễu định dạng; hỗ trợ chuẩn hóa metadata, chia chunk và kiểm tra tính nhất quán của tập train/test. | Xây dựng luồng hybrid reader, thiết kế prompt cho Qwen2.5-1.5B-Instruct, thiết lập cơ chế fallback extractive và kiểm tra tốc độ suy luận trên CPU. |
| Nguyễn Hoàng Tú | 23020428 | Phụ trách các instance 211-279: rà soát lại toàn bộ tập QA còn lại, hiệu chỉnh các câu khó và kiểm tra chéo đáp án để bảo đảm độ khớp với tài liệu gốc. | Tổng hợp kết quả crawl, hỗ trợ chuẩn hóa thư mục dữ liệu, kiểm tra số lượng tài liệu sau làm sạch, số chunk truy hồi và tách tập train/test. | Thực hiện đánh giá cuối cùng trên 66 câu test, tổng hợp các chỉ số EM/F1/Recall, đối chiếu kết quả giữa retrieval-only, direct baseline và hybrid RAG để hoàn thiện báo cáo. |

## Tóm tắt đóng góp theo hạng mục

- Data annotation: mỗi thành viên phụ trách một dải câu hỏi riêng, tổng khối lượng được chia cân bằng theo mốc 70/70/70/69 instances.
- Data collection and processing: cả bốn thành viên cùng tham gia thu thập nguồn, làm sạch HTML/text, chuẩn hóa corpus và kiểm tra chất lượng dữ liệu.
- Modeling and evaluation: nhóm cùng xây dựng retriever TF-IDF, hybrid reader, tích hợp Qwen2.5-1.5B-Instruct và thực hiện đánh giá trên tập test nội bộ.

