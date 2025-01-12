ner_prompt_instruction = """
# Bạn là: Bạn là một người thông hiểu lịch sử. Và nhiệm vụ của bạn là trích xuất tất cả các thực thể, khái niệm xuất hiện trong câu hỏi. Chỉ trích xuất các thực thể, khái niệm là nhân vật, sự kiện lịch sử, mốc thời gian, khoảng thời gian, cơ quan - tổ chức. Nếu bạn cảm thấy đây không phải là một câu hỏi lịch sử, hãy chỉ trả lời 'Không phải câu hỏi lịch sử'.
# Thực hiện theo các bước hướng dẫn:
Bước 1. Đọc kỹ câu hỏi và xác định các thực thể quan trọng xuất hiện trong câu hỏi.
Bước 2. Trích xuất các thực thể, khái niệm là mốc thời gian, khoảng thời gian như ngày, tháng, năm, triều đại.
Bước 3. Trích xuất các thực thể, khái niệm là nhân vật, sự kiện lịch sử
Bước 4. Trích xuất các thực thể, khái niệm là cơ quan - tổ chức
Ví dụ suy luận:
- Câu hỏi: "Hội nghị Ban Chấp hành Trung ương Đảng Cộng sản Đông Dương (5-1941) do Nguyễn Ái Quốc chủ trì xác định nhiệm vụ trực tiếp trước mắt là?"
- Thực thể:
##'Hội nghị Ban Chấp hành Trung ương Đảng Cộng sản Đông Dương': Đây là một cơ quan - tổ chức
##'Nguyễn Ái Quốc': Đây là một nhân vật lịch sử
##'5-1941': Đây mà mốc thời gian
"""

relation_prune_prompt_instruct = """# Nhiệm vụ:
1. Cẩn thận xem xét câu hỏi được cung cấp.
2. Từ danh sách các quan hệ có sẵn cho thực thể tương ứng, chọn % mà bạn cho là có khả năng liên kết với các thực thể có thể cung cấp thông tin liên quan nhất để giúp trả lời câu hỏi được cung cấp.
3. Đối với mỗi quan hệ được chọn, cung cấp điểm từ 0 đến 10 phản ánh mức độ hữu ích của nó trong việc trả lời câu hỏi, với 10 là hữu ích nhất.
4. Không thay đổi hoặc thêm vào danh sách các quan hệ đã cung cấp.
5. Luôn luôn sử dụng function_call được cung cấp
# Đầu vào theo định dạng dưới đây:
## Câu hỏi: [Nội dung câu hỏi]
## Thực thể chính: [Tên của thực thể]
## Danh sách mối quan hệ: [Danh sách các quan hệ của thực thể để lựa chọn.]
"""

answer_prompt_instruct = """# Nhiệm vụ:
1. Đưa ra câu trả lời trả lời cho câu hỏi dựa trên các thông tin được cung cấp trong các đoạn văn bản.
2. Giải thích vì sao dựa trên các thông tin từ các đoạn văn được cung cấp lại đưa ra câu trả lời như vậy.
3. Nếu là câu hỏi trắc nghiệm, hãy đưa ra đáp án đúng và giải thích vì sao các lựa chọn còn lại là sai.
# Đầu vào theo định dạng dưới đây:
##Câu hỏi: [Nội dung câu hỏi]
##Các đoạn văn bản:
1. [Nội dung đoạn văn bản 1]
2. [Nội dung đoạn văn bản 2]
...(Tiếp tục theo cùng cách cho các đoạn văn bản)"""

answer_prompt_instruct_mcp = """# Nhiệm vụ:
Đầu vào là một câu hỏi trắc nghiệm với các lựa chọn [A,B,C,D]. Nhiệm vụ của bạn là dựa trên các đoạn văn bản ngữ cảnh được cung cấp, chọn câu trả lời đúng nhất và trả về 1 trong 4 lựa chọn [A,B,C,D]."""

reasoning_path_prune_instruction = """Bạn được cung cấp câu hỏi và danh sách các đường dẫn suy luận chứa các BỘ 3 (triples) được truy xuất từ đồ thị tri thức, vui lòng chấm điểm mức độ liên quan của các  các BỘ 3 (triples) cho việc trả lời câu hỏi theo thang điểm 100.
# Thực hiện suy luận theo hướng dẫn:
Bước 1: Đọc kỹ câu hỏi và xem xét cách trả lời câu hỏi.
Bước 2: Phân tích mức độ liên quan giữa BỘ 3 và câu hỏi.
Bước 3: Chấm điểm cho mức độ đóng góp thông tin để để trả lời câu hỏi dựa trên BỘ 3 đó. Đánh giá điểm một cách công tâm và chính xác.
"""

validate_entities_instruction = """Cho một câu hỏi và danh sách các thực thể chủ đề liên quan, nhiệm vụ của bạn là chấm điểm dộ phù hợp của thực thể trong việc làm điểm khởi đầu cho việc suy luận trên đồ thị tri thức để tìm thông tin và manh mối hữu ích cho việc trả lời câu hỏi. Chấm điểm trên thang điểm 10
# Thực hiện suy luận theo hướng dẫn:
Bước 1: Đọc câu hỏi và xem xét các thực thể chủ đề được cung cấp.
Bước 2: Phân tích mối liên quan giữa các thực thể và câu hỏi để xác định thực thể nào có thể cung cấp thông tin hữu ích nhất cho việc trả lời câu hỏi.
Bước 3: Chú ý rằng các thực thể về thời gian, nhân vật, sự kiện, cơ quan tổ chức, địa danh là những thực thể quan trọng trong việc trả lời câu hỏi và đánh giá cao những thực thể này.
"""

evaluate_chunks_instruction = """
# Nhiệm vụ:
1. Đánh giá xem dựa vào các thông tin có trong đoạn văn bản, các manh mối và tri thức có sẵn của bạn có thể trả lời được câu hỏi hay không
2. Câu trả lời của bạn phải bắt đầu bằng 'Có' hoặc 'Không' và không giải thích gì thêm.
Đầu vào theo định dạng dưới đây:
# Câu hỏi: [Nội dung câu hỏi]
# Các đoạn văn bản:
1. [Nội dung đoạn văn bản 1]
2. [Nội dung đoạn văn bản 2]
...(Tiếp tục theo cùng cách cho các đoạn văn bản)
"""


requery_clues_instruction = """Dựa trên một câu hỏi và một số kiến thức đã thu thập được cho đến nay, hãy dự đoán bằng chứng bổ sung cần được tìm thấy để trả lời câu hỏi hiện tại, sau đó đưa ra một truy vấn phù hợp để tìm kiếm bằng chứng tiềm năng này. Lưu ý rằng truy vấn phải được đặt trong dấu ngoặc nhọn {xxx}."""

evaluate_chunks_change_query_instruction_2shot = """
# Nhiệm vụ:
1. Đánh giá xem dựa vào các thông tin có trong đoạn văn bản có thể trả lời được câu hỏi hay không
2. Câu trả lời của bạn phải bắt đầu bằng 'Có' hoặc 'Không' và không giải thích gì thêm.
3. Nếu {{Có}}, lưu ý rằng thực thể câu trả lời đã phân tích phải được đặt trong dấu ngoặc nhọn {{xxxxxx}}.
4. Nếu {{Không}}, điều đó có nghĩa là các tài nguyên này vô dụng hoặc chỉ cung cấp các manh mối có ích nhưng không đủ để trả lời câu hỏi một cách chắc chắn, hãy xác định các khía cạnh còn thiếu và tinh chỉnh truy vấn tìm kiếm để nhắm cụ thể vào thông tin cần thiết để hoàn thiện câu trả lời. Truy vấn tìm kiếm được nhắm mục tiêu cũng phải được đặt trong dấu ngoặc nhọn {{xxxxxx}}.
# Đầu vào theo định dạng dưới đây:
## Câu hỏi: [Nội dung câu hỏi]
## Các đoạn văn bản:
1. [Nội dung đoạn văn bản 1]
2. [Nội dung đoạn văn bản 2]
...(Tiếp tục theo cùng cách cho các đoạn văn bản)
# Ví dụ:

Câu hỏi: Nam tước Yamaji Motoharu là một tướng lĩnh trong Quân đội Đế quốc Nhật Bản đầu thế kỷ, thuộc về Đế quốc nào?
Manh mối: Không có
Các đoạn văn bản:
1. Nam tước Yamaji Motoharu là một tướng lĩnh trong Quân đội Đế quốc Nhật Bản đầu thế kỷ, thuộc về Đế quốc Nhật Bản. Đế quốc Nhật Bản là một nhà nước có chủ quyền tồn tại từ năm 1868 đến năm 1947, được cai trị bởi Thiên hoàng Nhật Bản.
2. Quân đội Đế quốc Nhật Bản, nơi Nam tước Yamaji Motoharu từng phục vụ với vai trò tướng lĩnh, là lực lượng quân sự trên bộ của Đế quốc Nhật Bản trong những năm đầu.
3. Khi Nam tước Yamaji Motoharu giữ chức tướng lĩnh, Đế quốc Nhật Bản đang mở rộng ảnh hưởng của mình khắp Đông Á và tham gia vào nhiều chiến dịch quân sự.
4. Là một tướng lĩnh trong Quân đội Đế quốc Nhật Bản đầu thế kỷ, Nam tước Yamaji Motoharu đã góp phần định hình chiến lược và hoạt động quân sự của Đế quốc Nhật Bản trong giai đoạn đó.
5. Đế quốc Nhật Bản, nơi Nam tước Yamaji Motoharu từng phục vụ với vai trò tướng lĩnh, có tham vọng thống trị khu vực và theo đuổi chính sách bành trướng mạnh mẽ, dẫn đến xung đột với các nước láng giềng như Trung Quốc và Nga.
Trả lời: Có. Dựa trên manh mối, các đoạn văn ngữ cảnh thu thập được và kiến thức của tôi, Nam tước Yamaji Motoharu, người là một tướng lĩnh trong Quân đội Đế quốc Nhật Bản đầu thế kỷ, thuộc về Đế quốc Nhật Bản. Do đó, câu trả lời cho câu hỏi là {Đế quốc Nhật Bản}.

Câu hỏi: Ai là huấn luyện viên của đội bóng do Steve Bisciotti sở hữu?
Manh mối: Không có
Các đoạn văn bản:
1. Đội bóng do Steve Bisciotti sở hữu là Baltimore Ravens.
2. Steve Bisciotti đã ký hợp đồng 3 năm với huấn luyện viên chính của ông ấy.
Trả lời: Không. Dựa trên bộ ba tri thức được cung cấp, các câu tham khảo thu thập được và kiến thức của tôi, đội bóng do Steve Bisciotti sở hữu là Baltimore Ravens. Cần có thêm thông tin về huấn luyện viên cụ thể của đội Baltimore Ravens để trả lời câu hỏi. Do đó, manh mối là {đội bóng do Steve Bisciotti sở hữu là Baltimore Ravens}.
"""

evaluate_chunks_change_query_instruction_zero_shot = """
# Nhiệm vụ:
1. Đánh giá xem dựa vào các thông tin có trong đoạn văn bản có thể trả lời được câu hỏi hay không
2. Câu trả lời của bạn phải bắt đầu bằng 'Có' hoặc 'Không' và không giải thích gì thêm.
3. Nếu {{Có}}, lưu ý rằng thực thể câu trả lời đã phân tích phải được đặt trong dấu ngoặc nhọn {{xxxxxx}}.
4. Nếu {{Không}}, điều đó có nghĩa là các tài nguyên này vô dụng hoặc chỉ cung cấp các manh mối có ích nhưng không đủ để trả lời câu hỏi một cách chắc chắn, hãy xác định các khía cạnh còn thiếu và tinh chỉnh truy vấn tìm kiếm để nhắm cụ thể vào thông tin cần thiết để hoàn thiện câu trả lời. Truy vấn tìm kiếm được nhắm mục tiêu cũng phải được đặt trong dấu ngoặc nhọn {{xxxxxx}}.
# Đầu vào theo định dạng dưới đây:
## Câu hỏi: [Nội dung câu hỏi]
## Các đoạn văn bản:
1. [Nội dung đoạn văn bản 1]
2. [Nội dung đoạn văn bản 2]
...(Tiếp tục theo cùng cách cho các đoạn văn bản)
"""
