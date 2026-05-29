from __future__ import annotations

import json
import re
from pathlib import Path


PAIRS = [
    # === UET General Info (15) ===
    ("Trường Đại học Công nghệ thuộc đại học nào?", "Đại học Quốc gia Hà Nội"),
    ("Tên tiếng Anh của Trường Đại học Công nghệ là gì?", "VNU University of Engineering and Technology"),
    ("UET là viết tắt của gì?", "University of Engineering and Technology"),
    ("Trường Đại học Công nghệ được thành lập ngày nào?", "25/5/2004"),
    ("UET được thành lập trên cơ sở những đơn vị nào?", "Khoa Công nghệ và Trung tâm Hợp tác Đào tạo và Bồi dưỡng Cơ học thuộc ĐHQGHN"),
    ("Sứ mệnh của UET là gì?", "Đào tạo nguồn nhân lực chất lượng cao, phát hiện và bồi dưỡng nhân tài, thúc đẩy nghiên cứu và ứng dụng khoa học - công nghệ tiên tiến theo chuẩn mực khu vực và quốc tế"),
    ("Tầm nhìn của Trường Đại học Công nghệ là gì?", "Giữ vững vị thế đại học kỹ thuật - công nghệ hàng đầu Việt Nam, vươn tầm nhóm các đại học tiên tiến châu Á"),
    ("Giá trị cốt lõi của UET gồm những gì?", "Đổi mới sáng tạo, chất lượng cao, hợp tác và nhân văn"),
    ("Địa chỉ của Trường Đại học Công nghệ ở đâu?", "Nhà E3, 144 Xuân Thủy, Cầu Giấy, Hà Nội"),
    ("Mã trường tuyển sinh của UET là gì?", "QHI"),
    ("UET có phải trường đại học công lập không?", "Có"),
    ("Khẩu hiệu của Trường Đại học Công nghệ là gì?", "Sáng tạo - Tiên phong - Chất lượng cao"),
    ("Hiệu trưởng UET là ai?", "GS.TS. Chử Đức Trình"),
    ("UET có bao nhiêu giảng viên?", "205"),
    ("UET có bao nhiêu sinh viên đại học?", "3.012"),

    # === Admissions (16) ===
    ("Năm 2026 sinh viên năm thứ nhất của UET học ở đâu?", "Cơ sở Hòa Lạc"),
    ("UET có những phương thức xét tuyển nào năm 2026?", "Xét tuyển thẳng, xét tuyển theo kết quả thi tốt nghiệp THPT, xét tuyển theo kết quả kỳ thi đánh giá năng lực HSA của ĐHQGHN và xét tuyển theo kết quả SAT"),
    ("UET mở cổng đăng ký xét tuyển năm 2026 khi nào?", "Từ ngày 11/05/2026 đến hết ngày 20/06/2026"),
    ("Quyết định tuyển sinh năm 2026 của UET có số bao nhiêu?", "659/QĐ-ĐHCN"),
    ("Ngưỡng đầu vào nhóm Máy tính và CNTT tại UET năm 2025 là bao nhiêu?", "24 điểm"),
    ("Ngưỡng đầu vào các ngành còn lại tại UET năm 2025 là bao nhiêu?", "22 điểm"),
    ("Điểm trúng tuyển ngành Công nghệ thông tin UET năm 2025?", "28.19"),
    ("Mã xét tuyển ngành Công nghệ thông tin của UET là gì?", "CN1"),
    ("Điểm trúng tuyển ngành Kỹ thuật máy tính UET năm 2025?", "27.00"),
    ("Điểm trúng tuyển ngành Khoa học máy tính UET năm 2025?", "27.86"),
    ("Điểm trúng tuyển ngành Trí tuệ nhân tạo UET năm 2025?", "27.75"),
    ("Mã xét tuyển ngành Trí tuệ nhân tạo của UET là gì?", "CN12"),
    ("Điểm trúng tuyển ngành Khoa học dữ liệu UET năm 2025?", "27.38"),
    ("Điểm trúng tuyển ngành Kỹ thuật điều khiển và tự động hóa UET năm 2025?", "27.90"),
    ("Điểm trúng tuyển ngành Công nghệ hàng không vũ trụ UET năm 2025?", "23.96"),
    ("Điểm trúng tuyển ngành Công nghệ nông nghiệp UET năm 2025?", "22.00"),

    # === Departments & Faculties (20) ===
    ("Trường Đại học Công nghệ có những ngành đào tạo bậc đại học nào?",
     "Công nghệ thông tin; Kỹ thuật máy tính; Khoa học máy tính; Trí tuệ nhân tạo; Hệ thống thông tin; Mạng máy tính và truyền thông dữ liệu; Vật lý kỹ thuật; Cơ kỹ thuật; Công nghệ kỹ thuật xây dựng; Công nghệ kỹ thuật cơ điện tử; Công nghệ hàng không vũ trụ; Công nghệ kỹ thuật điện tử - viễn thông; Công nghệ nông nghiệp; Kỹ thuật điều khiển và tự động hóa; Kỹ thuật năng lượng; Kỹ thuật Robot; Thiết kế công nghiệp và đồ họa; Công nghệ vật liệu; Khoa học dữ liệu; Công nghệ sinh học"),
    ("Các đơn vị đào tạo trực thuộc UET gồm những gì?",
     "Khoa Công nghệ thông tin, Khoa Điện tử viễn thông, Khoa Vật lý kỹ thuật và Công nghệ Nano, Khoa Cơ học kỹ thuật và Tự động hóa, Khoa Công nghệ nông nghiệp, Khoa Công nghệ Xây dựng - Giao thông, Viện Công nghệ Hàng không Vũ trụ và Viện Trí tuệ Nhân tạo"),
    ("Các đơn vị chức năng của UET gồm những gì?",
     "Phòng Đào tạo, Phòng Công tác Sinh viên, Phòng Hành chính Quản trị và Tổ chức Cán bộ, Phòng Khoa học Công nghệ và Hợp tác Phát triển, Phòng Kế hoạch Tài chính và Trung tâm Đại học số"),
    ("Khoa Công nghệ Thông tin UET được thành lập ngày nào?", "11/02/1995"),
    ("Khoa Công nghệ Thông tin có bao nhiêu cán bộ giảng dạy?", "Khoảng 100"),
    ("Khoa CNTT đào tạo bao nhiêu sinh viên mỗi năm?", "Khoảng 4000 sinh viên, 200 học viên và 50 nghiên cứu sinh"),
    ("Các bộ môn của Khoa Công nghệ Thông tin gồm những gì?",
     "Các Hệ thống Thông tin, Công nghệ Phần mềm, Khoa học Máy tính, Khoa học và Kỹ thuật tính toán, Mạng và Truyền thông Máy tính, An toàn thông tin"),
    ("Khoa Điện tử - Viễn thông UET thành lập ngày nào?", "03/01/1996"),
    ("Các bộ môn của Khoa Điện tử - Viễn thông gồm những gì?",
     "Điện tử và Kỹ thuật Máy tính, Kỹ thuật Viễn thông, Vi cơ Điện tử và Vi hệ thống, Kỹ thuật robot"),
    ("Khoa Cơ học kỹ thuật và Tự động hóa thành lập theo quyết định nào?",
     "Quyết định số 1279/QĐ-TCCB ngày 04/7/2005 của Giám đốc ĐHQGHN"),
    ("Khoa Cơ học kỹ thuật và Tự động hóa đào tạo những ngành đại học nào?",
     "Cơ học kỹ thuật, Công nghệ Cơ điện tử, Kỹ thuật điều khiển và Tự động hóa"),
    ("Viện Công nghệ Hàng không Vũ trụ thành lập khi nào?", "31/8/2017"),
    ("Tên tiếng Anh của Viện Công nghệ Hàng không Vũ trụ là gì?", "School of Aerospace Engineering (SAE)"),
    ("Viện Công nghệ Hàng không Vũ trụ là đối tác của đơn vị nào?", "Viện Hàng không Vũ trụ Viettel (VTX)"),
    ("Viện Trí tuệ nhân tạo UET thành lập khi nào?", "18/03/2022"),
    ("Tên tiếng Anh của Viện Trí tuệ nhân tạo là gì?", "Institute for Artificial Intelligence"),
    ("Viện trưởng Viện Trí tuệ nhân tạo UET là ai?", "TS. Trần Quốc Long"),
    ("Phó Viện trưởng Viện Trí tuệ nhân tạo là ai?", "TS. Bùi Ngọc Thăng"),
    ("Các phòng thí nghiệm của Viện Trí tuệ nhân tạo gồm những gì?",
     "Phòng thí nghiệm Học máy, Phòng thí nghiệm Xử lý ngôn ngữ tự nhiên và Phòng thí nghiệm trọng điểm Hệ thống tích hợp thông minh"),
    ("Phòng Công tác Sinh viên UET làm nhiệm vụ gì?",
     "Tiếp người học, giải quyết các công việc hành chính liên quan đến người học và xác nhận, giới thiệu người học với các cơ quan ngoài Trường"),

    # === VNU Info (9) ===
    ("ĐHQGHN là viết tắt của gì?", "Đại học Quốc gia Hà Nội"),
    ("ĐHQGHN có cơ sở tại Hòa Lạc không?", "Có"),
    ("Học bổng Đồng hành Vingroup năm 2025-2026 trị giá bao nhiêu?", "25 triệu đồng/sinh viên"),
    ("Điều kiện học tập để duy trì học bổng Đồng hành Vingroup là gì?",
     "Kết quả học tập đạt từ 3.2/4.0 trở lên và kết quả rèn luyện đạt từ loại tốt trở lên"),
    ("Quy chế tuyển sinh năm 2026 của ĐHQGHN hướng tới mục tiêu gì?",
     "Đánh giá năng lực toàn diện và nâng cao chất lượng đầu vào của thí sinh"),
    ("Lĩnh vực Khoa học máy tính và hệ thống thông tin của ĐHQGHN xếp hạng QS bao nhiêu?", "551-600 thế giới"),
    ("Lĩnh vực Kỹ thuật điện và điện tử của ĐHQGHN xếp hạng QS bao nhiêu?", "501-550 thế giới"),
    ("Đoàn Trường UET trực thuộc đơn vị nào?", "Đoàn Đại học Quốc gia Hà Nội"),
    ("Trung tâm Đại học số UET có chức năng gì?",
     "Tham mưu giúp Hiệu trưởng về chiến lược và kế hoạch phát triển chuyển đổi số, thực hiện chuyển đổi số, quản trị và vận hành hạ tầng"),

    # === News & Events (4) ===
    ("Kỳ thi chọn đội tuyển Olympic Trí tuệ nhân tạo năm 2026 có bao nhiêu thí sinh?", "Hơn 240 thí sinh"),
    ("UET và Trường ĐH Sư phạm Quảng Tây hợp tác trong lĩnh vực nào?",
     "Trí tuệ nhân tạo và các công nghệ mũi nhọn"),
    ("UET nhấn mạnh thế mạnh nào trong hợp tác với ĐH Sư phạm Quảng Tây?",
     "Đào tạo và nghiên cứu trong các lĩnh vực công nghệ mũi nhọn như trí tuệ nhân tạo, bán dẫn, công nghệ thông tin và điện tử viễn thông"),
    ("QS WUR by Subject 2026 ghi nhận điểm gì mới của ĐHQGHN?",
     "Thêm lĩnh vực mới và nhiều nhóm ngành thăng hạng toàn cầu"),

    # === Misc & Negative (1) ===
    ("Ngành Công nghệ sinh học UET năm 2025 có điểm trúng tuyển bao nhiêu?", "22.13"),
]

TEST_PAIRS = [
    ("UET có bao nhiêu sinh viên sau đại học?", "324"),
    ("UET có bao nhiêu nghiên cứu sinh?", "110"),
    ("Bản cập nhật thông tin tuyển sinh 2026 của UET ban hành ngày nào?", "01/04/2026"),
    ("Điểm xét tuyển giữa các tổ hợp năm 2025 tại UET được quy định thế nào?", "Như nhau giữa các tổ hợp"),
    ("UET năm 2025 có tuyển ngành Trí tuệ nhân tạo không?", "Có"),
    ("Khoa CNTT UET phát triển từ truyền thống đào tạo nào?",
     "Đào tạo chuyên ngành Máy tính tại Khoa Toán Cơ thuộc Trường Đại học Tổng hợp Hà Nội từ năm 1965"),
    ("Sứ mệnh của Khoa Công nghệ Thông tin là gì?",
     "Đào tạo và bồi dưỡng nhân tài, nguồn nhân lực chất lượng cao ngành CNTT; nghiên cứu phát triển các sản phẩm khoa học và công nghệ chất lượng cao theo chuẩn mực thế giới"),
    ("Sứ mệnh của Viện Trí tuệ nhân tạo là gì?",
     "Đào tạo nguồn nhân lực công nghệ chất lượng cao trong lĩnh vực trí tuệ nhân tạo và các lĩnh vực liên ngành; nghiên cứu phát triển và ứng dụng trí tuệ nhân tạo để đem lại lợi ích xã hội"),
    ("Khoa Cơ học kỹ thuật và Tự động hóa là đơn vị phối thuộc giữa những đơn vị nào?",
     "Trường ĐHCN và Viện Cơ học thuộc Viện Hàn lâm Khoa học và Công nghệ Việt Nam"),
    ("Chức năng chính của Viện Công nghệ Hàng không Vũ trụ là gì?",
     "Đào tạo, nghiên cứu khoa học và chuyển giao công nghệ trong lĩnh vực công nghệ hàng không vũ trụ"),
    ("Sứ mạng của Khoa Điện tử - Viễn thông là gì?",
     "Đào tạo và bồi dưỡng nguồn nhân lực chất lượng cao, đào tạo nhân tài ngành Công nghệ Điện tử - Viễn thông"),
    ("Hai nhiệm vụ chính khi thành lập UET là gì?",
     "Đào tạo nguồn nhân lực và bồi dưỡng nhân tài thuộc lĩnh vực khoa học công nghệ; nghiên cứu và triển khai ứng dụng khoa học công nghệ"),
    ("Tầm nhìn của Viện Trí tuệ nhân tạo là gì?",
     "Trở thành đơn vị dẫn đầu trong cả nước về đào tạo nguồn nhân lực chất lượng cao ngành trí tuệ nhân tạo"),
    ("Thông tin không có trong tài liệu thì hệ thống trả lời thế nào?", "Không có thông tin trong corpus."),
]

ADDITIONAL_TRAIN_PAIRS = [
    ("Ai là hiệu trưởng Trường Đại học Công nghệ?", "GS.TS. Chử Đức Trình"),
    ("Hiệu trưởng hiện tại của UET là ai?", "GS.TS. Chử Đức Trình"),
    ("Trường Đại học Công nghệ có hiệu trưởng là ai?", "GS.TS. Chử Đức Trình"),
    ("Tên đầy đủ tiếng Anh của UET là gì?", "VNU University of Engineering and Technology"),
    ("Trường Đại học Công nghệ có tên tiếng Anh là gì?", "VNU University of Engineering and Technology"),
    ("VNU-UET là tên tiếng Anh của trường nào?", "Trường Đại học Công nghệ, Đại học Quốc gia Hà Nội"),
    ("UET trực thuộc đơn vị nào?", "Đại học Quốc gia Hà Nội"),
    ("Trường Đại học Công nghệ trực thuộc đâu?", "Đại học Quốc gia Hà Nội"),
    ("ĐH Công nghệ thuộc ĐHQGHN đúng không?", "Có"),
    ("UET thành lập năm nào?", "2004"),
    ("Trường Đại học Công nghệ thành lập năm bao nhiêu?", "2004"),
    ("Ngày thành lập chính thức của UET là ngày nào?", "25/5/2004"),
    ("UET có địa chỉ tại đâu?", "Nhà E3, 144 Xuân Thủy, Cầu Giấy, Hà Nội"),
    ("Địa chỉ Nhà E3, 144 Xuân Thủy là của trường nào?", "Trường Đại học Công nghệ"),
    ("Mã QHI là mã tuyển sinh của trường nào?", "Trường Đại học Công nghệ"),
    ("Trường Đại học Công nghệ có mã tuyển sinh QHI không?", "Có"),
    ("Sứ mệnh đào tạo của UET nhấn mạnh điều gì?", "Đào tạo nguồn nhân lực chất lượng cao, phát hiện và bồi dưỡng nhân tài"),
    ("Tầm nhìn của UET hướng tới khu vực nào?", "Nhóm các đại học tiên tiến châu Á"),
    ("UET có các giá trị cốt lõi nào?", "Đổi mới sáng tạo, chất lượng cao, hợp tác và nhân văn"),
    ("Khẩu hiệu Sáng tạo - Tiên phong - Chất lượng cao là của trường nào?", "Trường Đại học Công nghệ"),
    ("Năm 2026 tân sinh viên UET học tại cơ sở nào?", "Cơ sở Hòa Lạc"),
    ("Sinh viên năm nhất UET năm 2026 học ở Hòa Lạc phải không?", "Có"),
    ("UET xét tuyển bằng HSA năm 2026 không?", "Có"),
    ("UET xét tuyển bằng SAT năm 2026 không?", "Có"),
    ("UET có xét tuyển theo điểm thi tốt nghiệp THPT năm 2026 không?", "Có"),
    ("UET năm 2026 có xét tuyển thẳng không?", "Có"),
    ("Cổng đăng ký xét tuyển UET năm 2026 mở từ ngày nào?", "11/05/2026"),
    ("Cổng đăng ký xét tuyển UET năm 2026 đóng ngày nào?", "20/06/2026"),
    ("Thời gian đăng ký xét tuyển UET năm 2026 kéo dài đến ngày nào?", "20/06/2026"),
    ("Thí sinh đăng ký xét tuyển UET cần thống nhất thông tin gì?", "Số CCCD"),
    ("Thông tin tuyển sinh UET năm 2026 được ban hành theo quyết định nào?", "659/QĐ-ĐHCN"),
    ("Ngành Trí tuệ nhân tạo của UET có mã xét tuyển nào?", "CN12"),
    ("CN12 là mã ngành nào của UET?", "Trí tuệ nhân tạo"),
    ("Điểm chuẩn Trí tuệ nhân tạo UET 2025 là bao nhiêu?", "27.75"),
    ("Ngành AI UET năm 2025 lấy bao nhiêu điểm?", "27.75"),
    ("Điểm chuẩn Công nghệ thông tin UET 2025 là bao nhiêu?", "28.19"),
    ("CN1 là mã ngành nào của UET?", "Công nghệ thông tin"),
    ("Kỹ thuật máy tính UET năm 2025 lấy bao nhiêu điểm?", "27.00"),
    ("Khoa học máy tính UET năm 2025 lấy bao nhiêu điểm?", "27.86"),
    ("Khoa học dữ liệu UET năm 2025 lấy bao nhiêu điểm?", "27.38"),
    ("Kỹ thuật điều khiển và tự động hóa UET năm 2025 lấy bao nhiêu điểm?", "27.90"),
    ("Công nghệ hàng không vũ trụ UET năm 2025 lấy bao nhiêu điểm?", "23.96"),
    ("Công nghệ nông nghiệp UET năm 2025 lấy bao nhiêu điểm?", "22.00"),
    ("Công nghệ sinh học UET năm 2025 lấy bao nhiêu điểm?", "22.13"),
    ("Nhóm ngành Máy tính và Công nghệ thông tin UET năm 2025 có ngưỡng đầu vào bao nhiêu?", "24 điểm"),
    ("Các ngành ngoài nhóm Máy tính và CNTT UET năm 2025 có ngưỡng đầu vào bao nhiêu?", "22 điểm"),
    ("Điểm chuẩn UET năm 2025 có khác nhau giữa các tổ hợp không?", "Không"),
    ("Điểm trúng tuyển của một ngành tại UET năm 2025 được tính theo thang điểm nào?", "Thang điểm 30"),
    ("UET có ngành Khoa học dữ liệu không?", "Có"),
    ("UET có ngành Kỹ thuật Robot không?", "Có"),
    ("UET có ngành Công nghệ vật liệu không?", "Có"),
    ("UET có ngành Công nghệ sinh học không?", "Có"),
    ("UET có ngành Công nghệ hàng không vũ trụ không?", "Có"),
    ("UET có ngành Thiết kế công nghiệp và đồ họa không?", "Có"),
    ("UET có đào tạo ngành Trí tuệ nhân tạo không?", "Có"),
    ("Kể tên các ngành thuộc nhóm máy tính ở UET.", "Công nghệ thông tin; Kỹ thuật máy tính; Khoa học máy tính; Trí tuệ nhân tạo; Hệ thống thông tin; Mạng máy tính và truyền thông dữ liệu"),
    ("Trường Đại học Công nghệ đào tạo những ngành nào?", "Công nghệ thông tin; Kỹ thuật máy tính; Khoa học máy tính; Trí tuệ nhân tạo; Hệ thống thông tin; Mạng máy tính và truyền thông dữ liệu; Vật lý kỹ thuật; Cơ kỹ thuật; Công nghệ kỹ thuật xây dựng; Công nghệ kỹ thuật cơ điện tử; Công nghệ hàng không vũ trụ; Công nghệ kỹ thuật điện tử - viễn thông; Công nghệ nông nghiệp; Kỹ thuật điều khiển và tự động hóa; Kỹ thuật năng lượng; Kỹ thuật Robot; Thiết kế công nghiệp và đồ họa; Công nghệ vật liệu; Khoa học dữ liệu; Công nghệ sinh học"),
    ("UET có bao nhiêu nhóm đơn vị đào tạo trực thuộc được nêu trong corpus?", "Các khoa và viện trực thuộc"),
    ("Khoa Công nghệ thông tin thuộc trường nào?", "Trường Đại học Công nghệ"),
    ("Khoa Điện tử viễn thông thuộc trường nào?", "Trường Đại học Công nghệ"),
    ("Khoa Cơ học kỹ thuật và Tự động hóa thuộc trường nào?", "Trường Đại học Công nghệ"),
    ("Viện Trí tuệ nhân tạo thuộc trường nào?", "Trường Đại học Công nghệ"),
    ("Viện Công nghệ Hàng không Vũ trụ thuộc trường nào?", "Trường Đại học Công nghệ"),
    ("Khoa CNTT UET được thành lập năm nào?", "1995"),
    ("Khoa Công nghệ Thông tin UET có truyền thống từ năm nào?", "1965"),
    ("Khoa CNTT UET có khoảng bao nhiêu cán bộ?", "Khoảng 100"),
    ("Khoa CNTT UET có bao nhiêu giáo sư?", "2 giáo sư"),
    ("Khoa CNTT UET có bao nhiêu phó giáo sư?", "15 phó giáo sư"),
    ("Khoa CNTT UET có bao nhiêu tiến sĩ?", "60 tiến sĩ"),
    ("Mỗi năm Khoa CNTT UET đào tạo khoảng bao nhiêu học viên?", "200 học viên"),
    ("Mỗi năm Khoa CNTT UET đào tạo khoảng bao nhiêu nghiên cứu sinh?", "50 nghiên cứu sinh"),
    ("Bộ môn Công nghệ Phần mềm thuộc khoa nào?", "Khoa Công nghệ Thông tin"),
    ("Bộ môn An toàn thông tin thuộc khoa nào?", "Khoa Công nghệ Thông tin"),
    ("Khoa Điện tử - Viễn thông UET thành lập năm nào?", "1996"),
    ("Chủ nhiệm Khoa Điện tử - Viễn thông là ai?", "TS. Đinh Triều Dương"),
    ("Khoa Điện tử - Viễn thông có bộ môn Kỹ thuật robot không?", "Có"),
    ("Khoa Cơ học kỹ thuật và Tự động hóa được thành lập năm nào?", "2005"),
    ("Khoa Cơ học kỹ thuật và Tự động hóa đào tạo mấy ngành đại học?", "03 ngành"),
    ("Ba ngành đại học của Khoa Cơ học kỹ thuật và Tự động hóa là gì?", "Cơ học kỹ thuật, Công nghệ Cơ điện tử, Kỹ thuật điều khiển và Tự động hóa"),
    ("Viện Công nghệ Hàng không Vũ trụ viết tắt là gì?", "SAE"),
    ("SAE là viết tắt của đơn vị nào tại UET?", "Viện Công nghệ Hàng không Vũ trụ"),
    ("Viện Công nghệ Hàng không Vũ trụ hợp tác với Viettel trong lĩnh vực nào?", "Công nghệ hàng không vũ trụ"),
    ("Viện Công nghệ Hàng không Vũ trụ có chức năng đào tạo không?", "Có"),
    ("Viện Công nghệ Hàng không Vũ trụ có chức năng chuyển giao công nghệ không?", "Có"),
    ("Viện Trí tuệ nhân tạo viết tắt tiếng Anh là gì?", "IAI"),
    ("IAI là viện nào của UET?", "Viện Trí tuệ nhân tạo"),
    ("Viện Trí tuệ nhân tạo nghiên cứu lĩnh vực gì?", "Trí tuệ nhân tạo và các lĩnh vực liên ngành"),
    ("Viện Trí tuệ nhân tạo có phòng thí nghiệm Học máy không?", "Có"),
    ("Viện Trí tuệ nhân tạo có phòng thí nghiệm Xử lý ngôn ngữ tự nhiên không?", "Có"),
    ("Phòng thí nghiệm trọng điểm của Viện Trí tuệ nhân tạo tên gì?", "Hệ thống tích hợp thông minh"),
    ("TS. Trần Quốc Long giữ chức vụ gì tại Viện Trí tuệ nhân tạo?", "Viện trưởng"),
    ("TS. Bùi Ngọc Thăng giữ chức vụ gì tại Viện Trí tuệ nhân tạo?", "Phó Viện trưởng"),
    ("Phòng Đào tạo là đơn vị gì của UET?", "Đơn vị chức năng"),
    ("Phòng Công tác Sinh viên hỗ trợ ai?", "Người học"),
    ("Phòng Kế hoạch Tài chính thuộc nhóm đơn vị nào?", "Đơn vị chức năng"),
    ("Trung tâm Đại học số thuộc trường nào?", "Trường Đại học Công nghệ"),
    ("Trung tâm Đại học số tham mưu về chuyển đổi số đúng không?", "Có"),
    ("Đoàn Trường UET trực thuộc Đoàn nào?", "Đoàn Đại học Quốc gia Hà Nội"),
    ("Hội Sinh viên UET là tổ chức của ai?", "Sinh viên Trường Đại học Công nghệ"),
    ("ĐHQGHN là đại học quốc gia ở đâu?", "Hà Nội"),
    ("VNU là viết tắt của cơ sở nào?", "Vietnam National University, Hanoi"),
    ("ĐHQGHN có khu đô thị đại học tại đâu?", "Hòa Lạc"),
    ("ĐHQGHN tiếp nhận các công trình đầu tiên tại đâu?", "Hòa Lạc"),
    ("Học bổng Đồng hành Vingroup 2025-2026 dành cho sinh viên trị giá bao nhiêu?", "25 triệu đồng/sinh viên"),
    ("Sinh viên cần GPA bao nhiêu để duy trì học bổng Đồng hành Vingroup?", "Từ 3.2/4.0 trở lên"),
    ("Kết quả rèn luyện để duy trì học bổng Đồng hành Vingroup cần đạt mức nào?", "Từ loại tốt trở lên"),
    ("Tuyển sinh ĐHQGHN năm 2026 hướng tới điều gì?", "Đánh giá năng lực toàn diện và nâng cao chất lượng đầu vào"),
    ("Đổi mới tuyển sinh ĐHQGHN hướng tới hệ thống như thế nào?", "Minh bạch, linh hoạt"),
    ("QS WUR by Subject 2026 ghi nhận ĐHQGHN thêm gì?", "Thêm lĩnh vực mới"),
    ("Lĩnh vực Khoa học máy tính và hệ thống thông tin của ĐHQGHN nằm trong nhóm nào?", "551-600 thế giới"),
    ("Lĩnh vực Kỹ thuật điện và điện tử của ĐHQGHN nằm trong nhóm nào?", "501-550 thế giới"),
    ("UET có hợp tác với Trường Đại học Sư phạm Quảng Tây không?", "Có"),
    ("Hợp tác giữa UET và ĐH Sư phạm Quảng Tây liên quan đến AI không?", "Có"),
    ("Trong hợp tác quốc tế, UET nhấn mạnh các lĩnh vực công nghệ mũi nhọn nào?", "Trí tuệ nhân tạo, bán dẫn, công nghệ thông tin và điện tử viễn thông"),
    ("Kỳ thi Olympic Trí tuệ nhân tạo năm 2026 có hơn 240 thí sinh không?", "Có"),
    ("Olympic Trí tuệ nhân tạo 2026 có bao nhiêu thí sinh tham gia?", "Hơn 240 thí sinh"),
    ("Ngành AI UET có bao nhiêu sinh viên từng khóa?", "Không có thông tin trong corpus."),
    ("Chỉ tiêu ngành AI UET là bao nhiêu?", "Không có thông tin trong corpus."),
]

ADDITIONAL_TEST_PAIRS = [
    ("Ai đang là hiệu trưởng UET?", "GS.TS. Chử Đức Trình"),
    ("Trường Đại học Công nghệ tên tiếng Anh đầy đủ là gì?", "VNU University of Engineering and Technology"),
    ("UET thuộc Đại học Quốc gia Hà Nội phải không?", "Có"),
    ("Trường ĐH Công nghệ thành lập vào ngày tháng năm nào?", "25/5/2004"),
    ("Mã tuyển sinh của UET là mã nào?", "QHI"),
    ("Tân sinh viên UET năm 2026 học ở cơ sở nào?", "Cơ sở Hòa Lạc"),
    ("UET có xét tuyển theo HSA không?", "Có"),
    ("UET có xét tuyển theo SAT không?", "Có"),
    ("Cổng đăng ký xét tuyển UET năm 2026 mở đến ngày nào?", "20/06/2026"),
    ("Ngành Trí tuệ nhân tạo ở UET có mã gì?", "CN12"),
    ("Điểm chuẩn ngành AI UET năm 2025 là bao nhiêu?", "27.75"),
    ("Điểm chuẩn ngành CNTT UET năm 2025 là bao nhiêu?", "28.19"),
    ("Ngành Khoa học dữ liệu UET năm 2025 lấy mấy điểm?", "27.38"),
    ("Ngưỡng đầu vào nhóm Máy tính và CNTT UET là bao nhiêu?", "24 điểm"),
    ("UET có ngành Kỹ thuật Robot không?", "Có"),
    ("UET có ngành Công nghệ sinh học không?", "Có"),
    ("UET có ngành Công nghệ vật liệu không?", "Có"),
    ("Khoa Công nghệ Thông tin UET thành lập năm nào?", "1995"),
    ("Khoa CNTT UET đào tạo khoảng bao nhiêu sinh viên mỗi năm?", "Khoảng 4000 sinh viên"),
    ("Khoa Điện tử - Viễn thông UET thành lập năm nào?", "1996"),
    ("Chủ nhiệm Khoa Điện tử - Viễn thông là ai?", "TS. Đinh Triều Dương"),
    ("Khoa Cơ học kỹ thuật và Tự động hóa đào tạo bao nhiêu ngành đại học?", "03 ngành"),
    ("Viện Công nghệ Hàng không Vũ trụ của UET viết tắt là gì?", "SAE"),
    ("Viện Công nghệ Hàng không Vũ trụ là đối tác của ai?", "Viện Hàng không Vũ trụ Viettel (VTX)"),
    ("Viện Trí tuệ nhân tạo UET thành lập năm nào?", "2022"),
    ("Viện Trí tuệ nhân tạo UET tên tiếng Anh là gì?", "Institute for Artificial Intelligence"),
    ("Ai là Viện trưởng Viện Trí tuệ nhân tạo?", "TS. Trần Quốc Long"),
    ("Phòng thí nghiệm Xử lý ngôn ngữ tự nhiên thuộc viện nào?", "Viện Trí tuệ nhân tạo"),
    ("Phòng Công tác Sinh viên UET phục vụ đối tượng nào?", "Người học"),
    ("Trung tâm Đại học số tham mưu về lĩnh vực gì?", "Chuyển đổi số"),
    ("Đoàn Trường UET trực thuộc đâu?", "Đoàn Đại học Quốc gia Hà Nội"),
    ("ĐHQGHN có cơ sở Hòa Lạc không?", "Có"),
    ("Học bổng Đồng hành Vingroup trị giá bao nhiêu mỗi sinh viên?", "25 triệu đồng/sinh viên"),
    ("Điều kiện GPA duy trì học bổng Đồng hành Vingroup là bao nhiêu?", "Từ 3.2/4.0 trở lên"),
    ("QS 2026 xếp Khoa học máy tính và hệ thống thông tin của ĐHQGHN nhóm nào?", "551-600 thế giới"),
    ("QS 2026 xếp Kỹ thuật điện và điện tử của ĐHQGHN nhóm nào?", "501-550 thế giới"),
    ("UET hợp tác với Đại học Sư phạm Quảng Tây trong lĩnh vực nào?", "Trí tuệ nhân tạo và các công nghệ mũi nhọn"),
    ("Olympic Trí tuệ nhân tạo năm 2026 có hơn bao nhiêu thí sinh?", "Hơn 240 thí sinh"),
    ("Ngành Trí tuệ nhân tạo UET tuyển bao nhiêu chỉ tiêu?", "Không có thông tin trong corpus."),
    ("Số sinh viên từng khóa của ngành AI UET là bao nhiêu?", "Không có thông tin trong corpus."),
]


VNU_WIDE_TRAIN_PAIRS = [
    ("Quy chế tuyển sinh đại học năm 2026 của ĐHQGHN được ban hành ngày nào?", "20/3/2026"),
    ("Quy chế tuyển sinh đại học năm 2026 của ĐHQGHN áp dụng cho phạm vi nào?", "Các chương trình đào tạo trình độ đại học trong toàn hệ thống ĐHQGHN từ năm 2026"),
    ("Quy chế tuyển sinh đại học năm 2026 của ĐHQGHN gồm bao nhiêu chương và bao nhiêu điều?", "3 chương, 20 điều"),
    ("Mục tiêu của quy chế tuyển sinh đại học ĐHQGHN năm 2026 là gì?", "Hoàn thiện cơ chế tuyển sinh theo hướng đồng bộ, minh bạch và nâng cao chất lượng đầu vào"),
    ("Các đơn vị đào tạo của ĐHQGHN được dùng tối đa bao nhiêu phương thức tuyển sinh từ năm 2026?", "Tối đa 5 phương thức tuyển sinh, không bao gồm xét tuyển thẳng"),
    ("Quy chế tuyển sinh ĐHQGHN năm 2026 nêu những phương thức tuyển sinh nào?", "Kết quả thi tốt nghiệp THPT, kết quả thi đánh giá năng lực của ĐHQGHN, chứng chỉ quốc tế như SAT, A-Level, ACT và các phương thức kết hợp hoặc đặc thù khác"),
    ("Theo quy chế tuyển sinh ĐHQGHN năm 2026, tổng điểm cộng không được vượt quá bao nhiêu?", "Không vượt quá 10% thang điểm xét tuyển"),
    ("Quy chế tuyển sinh đại học chính quy tại ĐHQGHN năm 2025 ban hành kèm quyết định nào?", "Quyết định số 1868/QĐ-ĐHQGHN"),
    ("Quy chế tuyển sinh đại học chính quy tại ĐHQGHN năm 2025 gồm bao nhiêu chương, bao nhiêu điều?", "03 chương, 24 điều"),
    ("Trường Đại học Kinh tế - ĐHQGHN tuyển sinh bao nhiêu chỉ tiêu đại học năm 2026?", "3000 chỉ tiêu"),
    ("Năm 2026 Trường Đại học Kinh tế - ĐHQGHN tuyển sinh bao nhiêu ngành và bao nhiêu chương trình đào tạo?", "6 ngành, 8 chương trình đào tạo"),
    ("Trường Đại học Kinh tế - ĐHQGHN năm 2026 có bao nhiêu chuyên ngành chuyên sâu?", "30 chuyên ngành chuyên sâu"),
    ("Trường Đại học Kinh tế - ĐHQGHN năm 2026 có sử dụng học bạ cho tuyển sinh chính quy trong nước không?", "Không sử dụng kết quả học tập bậc THPT (học bạ) trong tuyển sinh đại học chính quy trong nước"),
    ("Các tổ hợp xét tuyển chính quy trong nước của Trường Đại học Kinh tế - ĐHQGHN năm 2026 gồm những mã nào?", "D01, C01, C04, C03 và X01"),
    ("Trường Đại học Kinh tế - ĐHQGHN xét tuyển HSA năm 2026 không?", "Có, trường xét tuyển kết quả thi đánh giá năng lực học sinh bậc THPT do ĐHQGHN tổ chức"),
    ("Trường Quốc tế - ĐHQGHN năm 2026 xét tuyển bằng những phương thức nào?", "Điểm thi tốt nghiệp THPT, điểm thi HSA, xét tuyển thẳng hoặc ưu tiên xét tuyển, chứng chỉ tiếng Anh quốc tế kết hợp kết quả thi tốt nghiệp THPT, A-Level hoặc thí sinh quốc tế"),
    ("Điều kiện HSA được nêu trong thông tin tuyển sinh Trường Quốc tế - ĐHQGHN là bao nhiêu?", "Điểm thi HSA từ 80 trở lên"),
    ("Điều kiện SAT được nêu trong thông tin tuyển sinh Trường Quốc tế - ĐHQGHN là bao nhiêu?", "SAT từ 1100/1600 trở lên"),
    ("Điều kiện IELTS được nêu trong thông tin tuyển sinh Trường Quốc tế - ĐHQGHN là bao nhiêu?", "IELTS từ 5.5 trở lên hoặc TOEFL iBT từ 72 trở lên và GPA từ 8.0 trở lên"),
    ("Trường Đại học Khoa học Tự nhiên - ĐHQGHN là trường đầu tiên trong khu vực nào đạt chuẩn chất lượng cấp trường của AUN?", "Khu vực Đông Nam Á"),
    ("Tất cả bao nhiêu khoa của Trường Đại học Khoa học Tự nhiên - ĐHQGHN đã được kiểm định theo tiêu chuẩn AUN?", "08 khoa"),
    ("Trường Đại học Khoa học Tự nhiên - ĐHQGHN có khoảng bao nhiêu học sinh, sinh viên?", "Gần 10.000 học sinh, sinh viên"),
    ("Trường Đại học Khoa học Xã hội và Nhân văn - ĐHQGHN tuyển sinh đại học năm 2026 bao nhiêu ngành đào tạo?", "28 ngành đào tạo"),
    ("USSH ĐHQGHN năm 2026 sử dụng những phương thức tuyển sinh đại học nào được nêu trong bài tư vấn?", "Xét tuyển thẳng và ưu tiên xét tuyển, xét tuyển kết quả thi đánh giá năng lực HSA còn hiệu lực của ĐHQGHN, và xét tuyển kết quả thi tốt nghiệp THPT"),
    ("Chủ đề chuỗi tư vấn tuyển sinh hướng nghiệp năm 2026 mà USSH tham gia là gì?", "Hiểu đúng mình - Chọn đúng nghề - Đi đúng hướng"),
    ("USSH mở đăng ký dự thi thạc sĩ đợt 1 năm 2026 đến ngày nào?", "17/05/2026"),
    ("USSH tổ chức xét tuyển thạc sĩ theo phương thức đánh giá hồ sơ ngày nào?", "20/05/2026"),
    ("USSH dự kiến thông báo kết quả tuyển sinh thạc sĩ đợt 1 năm 2026 ngày nào?", "24/06/2026"),
    ("Trường Đại học Ngoại ngữ - ĐHQGHN tập huấn chuyên môn tuyển sinh đại học chính quy năm 2026 cho đội ngũ nào?", "Đội ngũ Đại sứ Đặc nhiệm 2026 thuộc chương trình Đại sứ ULIS"),
    ("Buổi tập huấn tuyển sinh năm 2026 của ULIS có bao nhiêu Đại sứ Đặc nhiệm tham dự?", "46 Đại sứ Đặc nhiệm 2026"),
]


VNU_WIDE_TEST_PAIRS = [
    ("Quy chế tuyển sinh ĐHQGHN năm 2026 có điểm mới nổi bật nào?", "Đa dạng hóa phương thức tuyển sinh"),
    ("Từ năm 2026, ĐHQGHN cho phép tối đa bao nhiêu phương thức tuyển sinh ngoài xét tuyển thẳng?", "Tối đa 5 phương thức tuyển sinh"),
    ("Quy chế tuyển sinh ĐHQGHN năm 2026 kiểm soát điểm cộng ở mức nào?", "Tổng điểm cộng không vượt quá 10% thang điểm xét tuyển"),
    ("Năm 2026 UEB tuyển sinh 3000 chỉ tiêu cho bao nhiêu ngành?", "6 ngành"),
    ("UEB năm 2026 có dùng học bạ cho hệ chính quy trong nước không?", "Không"),
    ("Các mã tổ hợp xét tuyển trong nước của UEB năm 2026 là gì?", "D01, C01, C04, C03 và X01"),
    ("Trường Quốc tế - ĐHQGHN yêu cầu điểm HSA tối thiểu bao nhiêu trong thông tin tuyển sinh 2026?", "Điểm thi HSA từ 80 trở lên"),
    ("Trường Quốc tế - ĐHQGHN yêu cầu SAT tối thiểu bao nhiêu?", "SAT từ 1100/1600 trở lên"),
    ("HUS có bao nhiêu khoa đã kiểm định theo tiêu chuẩn AUN?", "08 khoa"),
    ("USSH tuyển sinh đại học năm 2026 với bao nhiêu ngành đào tạo?", "28 ngành đào tạo"),
    ("USSH nhận đăng ký dự thi thạc sĩ đợt 1 năm 2026 đến ngày nào?", "17/05/2026"),
    ("ULIS tập huấn tuyển sinh năm 2026 cho bao nhiêu Đại sứ Đặc nhiệm?", "46 Đại sứ Đặc nhiệm 2026"),
]


def write_split(directory: Path, rows: list[tuple[str, str]]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "questions.txt").write_text(
        "\n".join(question for question, _ in rows) + "\n", encoding="utf-8"
    )
    (directory / "reference_answers.txt").write_text(
        "\n".join(answer for _, answer in rows) + "\n", encoding="utf-8"
    )


def clean_document_text(text: str) -> str:
    text = re.sub(r"\{\{.*?\}\}", " ", text)
    text = re.sub(r"\[\s*\d+\s*\]", " ", text)
    text = re.sub(r"\^\s*\"[^\"]+\"\s*\.?", " ", text)
    text = re.sub(r"\bsửa\s*\|\s*sửa mã nguồn\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bQuản lý CS1:[^.]+\.?", " ", text)
    text = re.sub(r"\bChú thích web\b", " ", text)
    text = re.sub(r"\|\s*\w+\s*=", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def noisy_document(document: dict) -> bool:
    blob = " ".join(str(document.get(key, "")) for key in ["title", "description", "text", "url"]).lower()
    markers = [
        "vnpost ensures uninterrupted public services",
        "temperatures exceeding 40",
        "follow vietnam.vn on",
        "top interests newest",
    ]
    return any(marker in blob for marker in markers)


def rewrite_documents_and_corpus() -> tuple[int, int]:
    documents_path = Path("data/uet_vnu/documents.jsonl")
    raw_corpus_path = Path("data/raw/uet_vnu/corpus_long.txt")
    if not documents_path.exists():
        return 0, 0

    documents = []
    removed = 0
    for line in documents_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        document = json.loads(line)
        if noisy_document(document):
            removed += 1
            continue
        document["text"] = clean_document_text(str(document.get("text", "")))
        document["description"] = clean_document_text(str(document.get("description", "")))
        documents.append(document)

    documents_path.write_text(
        "\n".join(json.dumps(document, ensure_ascii=False) for document in documents) + "\n",
        encoding="utf-8",
    )

    # Write clean corpus - only title + content, no metadata noise
    contexts = []
    for document in documents:
        title = document.get("title", "")
        content = document.get("text", "")
        contexts.append(f"{title}\n{content}")

    raw_corpus_path.parent.mkdir(parents=True, exist_ok=True)
    raw_corpus_path.write_text("\n\n".join(contexts) + "\n", encoding="utf-8")
    return len(documents), removed


def main() -> None:
    all_pairs = (
        PAIRS
        + ADDITIONAL_TRAIN_PAIRS
        + VNU_WIDE_TRAIN_PAIRS
        + TEST_PAIRS
        + ADDITIONAL_TEST_PAIRS
        + VNU_WIDE_TEST_PAIRS
    )
    train = PAIRS + ADDITIONAL_TRAIN_PAIRS + VNU_WIDE_TRAIN_PAIRS
    test = TEST_PAIRS + ADDITIONAL_TEST_PAIRS + VNU_WIDE_TEST_PAIRS
    write_split(Path("data/train"), train)
    write_split(Path("data/test"), test)
    document_count, removed_documents = rewrite_documents_and_corpus()

    metadata_path = Path("data/uet_vnu/metadata.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
    if document_count:
        metadata["documents"] = document_count
    metadata["qa_examples"] = len(all_pairs)
    metadata["train_examples"] = len(train)
    metadata["test_examples"] = len(test)
    metadata["qa_curation"] = "manual_curated_concise_answers"
    metadata["removed_noisy_documents_count"] = removed_documents
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote manual curated QA: train={len(train)}, test={len(test)}")


if __name__ == "__main__":
    main()
