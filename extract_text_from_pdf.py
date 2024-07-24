import pytesseract
import shutil
import os
import random
from PIL import Image
import pdf2image

path_file_pdf = ""
path_file_text = ""

images = pdf2image.convert_from_path(path_file_pdf)

lang = "vie"
config = r"--oem 3 --psm 6"
content_book = ""
for img in images:
    content_book += pytesseract.image_to_string(img, lang=lang, config=config)

text_file = open(path_file_text, "w")
text_file.write(content_book)
