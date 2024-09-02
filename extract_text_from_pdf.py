import json
import fitz  # PyMuPDF
import openai
from openai import OpenAI
import pdf2image
from pydantic import BaseModel
from typing import List
import pytesseract

import os

folder_path = "/content/drive/MyDrive/Thesis-Data/lichsuVietNamtap2"


class PartContent(BaseModel):
    title: str
    start_page: int
    end_page: int
    content: str
    sub_parts: List["PartContent"] = []


# Đặt API key của bạn
api_key = ""
client = OpenAI(api_key=api_key)
# Open the PDF file
pdf_document = "/content/drive/MyDrive/Thesis-Data/pdf/lichsuvietnam2.pdf"
document = fitz.open(pdf_document)
images = pdf2image.convert_from_path(pdf_document)

lang = "vie"
config = r"--oem 3 --psm 6"

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_table_content",
            "description": "Trích xuất mục lục từ văn bản được cung cấp",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "table_contents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "page": {
                                    "type": "number",
                                    "description": "Số trang tương ứng với tiêu đề",
                                },
                                "title": {
                                    "type": "string",
                                    "description": "Xem xét một cách cẩn thận các tiêu đề và viết dưới dạng Tiếng Việt. Các tiêu đề thường bắt đầu bằng 'Chương',các chữ số  La Mã, hoặc các chữ số bình thường. Sự bắt đầu của các tiêu đề cần phải viết lại và sắp xép theo đúng thứ tự",
                                },
                                "level": {
                                    "type": "string",
                                    "description": "Cấp độ tiêu đề",
                                    "enum": ["1", "2", "3", "4"],
                                },
                            },
                            "required": ["page", "title", "level"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["table_contents"],
                "additionalProperties": False,
            },
        },
    }
]


def get_table_content(text_contain_index):

    prompt = "Trích xuất mục lục từ văn bản sau: " + text_contain_index
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Hoặc model khác tùy chọn của bạn
            messages=[
                {
                    "role": "system",
                    "content": "Bạn là trợ lý hữu ích trong việc xử lý, trích xuất văn bản. Nhiệm vụ của bạn là trích xuất mục lục từ văn bản được cung cấp. Lấy tất cả cấp độ các tiêu đề có trong văn bản được cung cấp",
                },
                {"role": "user", "content": prompt},
            ],
            tools=tools,
        )
        print(response)
        return response.choices[0].message.tool_calls[0].function.arguments
    except Exception as e:
        return f"An error occurred: {str(e)}"


# Get text contain table of content
text_contain_index = ""
for image in images[-30:]:
    text = pytesseract.image_to_string(image, lang=lang, config=config)
    text_contain_index = text_contain_index + text

table_contents = json.loads(get_table_content(text_contain_index))
table_contents

# Create a list of PartContent from table_contents


def make_list_part(table_contents):
    list_content: List[PartContent] = []
    in_table_content = False
    for content in table_contents["table_contents"]:
        if (
            in_table_content
            and content["level"] == "1"
            and "Chương" not in content["title"]
        ):
            in_table_content = False
            if len(list_content) > 0:
                list_content[-1].end_page = content["page"]
                if list_content[-1].sub_parts:
                    list_content[-1].sub_parts[-1].end_page = content["page"]
                    if list_content[-1].sub_parts[-1].sub_parts:
                        list_content[-1].sub_parts[-1].sub_parts[-1].end_page = content[
                            "page"
                        ]
            break
        if content["level"] == "1" and "Chương" in content["title"]:
            in_table_content = True
            if len(list_content) > 0:
                list_content[-1].end_page = content["page"]
                if list_content[-1].sub_parts:
                    list_content[-1].sub_parts[-1].end_page = content["page"]
                    if list_content[-1].sub_parts[-1].sub_parts:
                        list_content[-1].sub_parts[-1].sub_parts[-1].end_page = content[
                            "page"
                        ]
            list_content.append(
                PartContent(
                    title=content["title"],
                    start_page=content["page"],
                    end_page=0,
                    content="",
                    sub_parts=[],
                )
            )
        if content["level"] == "2":
            if len(list_content) > 0:
                if len(list_content[-1].sub_parts) > 0:
                    list_content[-1].sub_parts[-1].end_page = content["page"]
                    if list_content[-1].sub_parts[-1].sub_parts:
                        list_content[-1].sub_parts[-1].sub_parts[-1].end_page = content[
                            "page"
                        ]
                list_content[-1].sub_parts.append(
                    PartContent(
                        title=content["title"],
                        start_page=content["page"],
                        end_page=0,
                        content="",
                        sub_parts=[],
                    )
                )
        if content["level"] == "3":
            if len(list_content) > 0:
                if len(list_content[-1].sub_parts) > 0:
                    if len(list_content[-1].sub_parts[-1].sub_parts) > 0:
                        list_content[-1].sub_parts[-1].sub_parts[-1].end_page = content[
                            "page"
                        ]
                    list_content[-1].sub_parts[-1].sub_parts.append(
                        PartContent(
                            title=content["title"],
                            start_page=content["page"],
                            end_page=0,
                            content="",
                            sub_parts=[],
                        )
                    )
    return list_content


def get_content_of_part(part: PartContent):
    if part.sub_parts:
        for sub_part in part.sub_parts:
            get_content_of_part(sub_part)
    else:
        content_of_part = ""
        for image in images[part.start_page - 1 : part.end_page]:
            image_w, image_h = image.size
            content_of_part = content_of_part + pytesseract.image_to_string(
                image.crop((0, image_h * 1 / 10, image_w, image_h * 11 / 12)),
                lang=lang,
                config=config,
            )
        part.content = content_of_part
    return part


def save_content_to_file(folder_path: str, list_content: List[PartContent]):
    os.makedirs(folder_path, exist_ok=True)
    for content in list_content:
        if content.sub_parts:
            os.makedirs(f"{folder_path}/{content.title}", exist_ok=True)
            for sub_part in content.sub_parts:
                if sub_part.sub_parts:
                    os.makedirs(
                        f"{folder_path}/{content.title}/{sub_part.title}", exist_ok=True
                    )
                    for sub_sub_part in sub_part.sub_parts:
                        with open(
                            f"{folder_path}/{content.title}/{sub_part.title}/{sub_sub_part.title}.txt",
                            "w",
                            encoding="utf-8",
                        ) as f:
                            f.write(sub_sub_part.content)
                            f.close()
                else:
                    with open(
                        f"{folder_path}/{content.title}/{sub_part.title}.txt",
                        "w",
                        encoding="utf-8",
                    ) as f:
                        f.write(sub_part.content)
                        f.close()
        else:
            with open(f"{folder_path}/{content.title}.txt", "w", encoding="utf-8") as f:
                f.write(content.content)
                f.close()
