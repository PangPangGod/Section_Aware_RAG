import os
import json
import pdfplumber
from pathlib import Path
from pydantic import BaseModel
from typing import List, Any

import htmltabletomd

""" 
    Handle the results generated through preprocess_document

    1. Simply extract text coordinates using pdfplumber, and if they are within the table coordinates extracted through TATR, 
    change the TextElement type to Table and set the is_table attribute to True.

    2. Then, convert the HTML results processed through table detection into text, create TextElement objects from them, and return these objects.
    ===========================================================================================

    preprocess_document를 통해서 나온 결과(output folder -> TODO:나중에 파일별 폴더 시스템으로 변경)를 다룬다.

    단순하게 pdfplumber를 통해 텍스트 좌표를 추출하고, 이걸 TATR을 통해 추출된 테이블 좌표 내에 있는것으로 판단하면
    TextElement의 Type을 Table로 바꾸고 is_table Attribute도 True로 바꿔준다.

    그 다음에, Table Detection을 통해 처리된 html 결과물을 text로 변환한 후, 이를 TextElement로 만들어서 return한다.

"""


# Define TextElement class
class TextElement(BaseModel):
    type: str
    text: str
    page_number: int
    table_index: Any
    is_table: bool = False

def convert_pdf_to_pixels(pdf_width, pdf_height, dpi=300):
    """Convert PDF dimensions from points to pixels at a specific DPI."""
    pixels_per_point = dpi / 72
    return (pdf_width * pixels_per_point, pdf_height * pixels_per_point)

def adjust_coordinates_for_dpi(bbox, pdf_width, pdf_height, dpi=300):
    """Adjust bbox coordinates based on DPI scaling relative to the PDF dimensions."""
    pixels_width, pixels_height = convert_pdf_to_pixels(pdf_width, pdf_height, dpi)
    scale_x = pixels_width / pdf_width
    scale_y = pixels_height / pdf_height
    adjusted_bbox = (bbox[0] / scale_x, bbox[1] / scale_y, bbox[2] / scale_x, bbox[3] / scale_y)
    return adjusted_bbox

def load_page_objects(page_number, detection_folder, file_prefix):
    """Load JSON data for a specific page."""
    json_path = detection_folder / f"{file_prefix}_page{page_number}_objects.json"
    if json_path.exists():
        with open(json_path, 'r') as file:
            return json.load(file)
    return []

def is_within_bbox(word_bbox, table_bbox):
    """Check if the word's bounding box is within the table's bounding box."""
    word_x0, word_top, word_x1, word_bottom = word_bbox
    table_x0, table_top, table_x1, table_bottom = table_bbox
    return (word_x0 >= table_x0 and word_x1 <= table_x1 and
            word_top >= table_top and word_bottom <= table_bottom)

def process_pdf_text_from_plumber(pdf_path: str, detection_folder: Path, file_prefix: str, dpi: int = 300) -> List[TextElement]:
    """
    Process a PDF file and extract text elements.

    Args:
    pdf_path (str): The path to the PDF file.
    detection_folder (Path): The folder containing the detection data.
    file_prefix (str): The prefix for the detection files.
    dpi (int, optional): The DPI to use for adjustment. Defaults to 300.

    Returns:
    List[TextElement]: A list of extracted text elements.
    """
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages):
            objects = load_page_objects(page_number, detection_folder, file_prefix)
            if not objects:
                continue
            sorted_objects = sorted(objects, key=lambda x: x['bbox'][1])
            tables = [adjust_coordinates_for_dpi(obj['bbox'], page.width, page.height, dpi) for obj in sorted_objects]
            current_text = ""
            is_current_table = False
            table_index = -1  # index -1부터 시작

            for line in page.extract_text_lines(return_chars=True):
                line_bbox = (line['x0'], line['top'], line['x1'], line['bottom'])
                line_is_table = any(is_within_bbox(line_bbox, tbl) for tbl in tables)

                if line_is_table != is_current_table or not line['text'].strip():
                    if current_text:
                        results.append(TextElement(
                            type="table" if is_current_table else "text",
                            text=current_text,
                            page_number=page_number,
                            is_table=is_current_table,
                            table_index=table_index if is_current_table else None
                        ))
                        current_text = ""
                    is_current_table = line_is_table
                    if is_current_table:  # 테이블 시작 시 인덱스 증가
                        table_index += 1

                current_text += line['text'] + ' '

            if current_text:
                results.append(TextElement(
                    type="table" if is_current_table else "text",
                    text=current_text,
                    page_number=page_number,
                    is_table=is_current_table,
                    table_index=table_index if is_current_table else None
                ))

    return results

def postprocess_with_datr(elements: List[TextElement], structure_path: Path, file_prefix: str):
    """Parse html table to text and add to TextElement class."""
    for element in elements:
        if element.is_table:
            html_path = structure_path / f"{file_prefix}_page{element.page_number}_{element.table_index}_0.html"
            if html_path.exists():
                with open(html_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()
                element.text = htmltabletomd.convert_table(html_content)
    return elements


###########################################################
#Example

if __name__ == "__main__":
    try:
        # Example usage
        base_path = Path("preprocess_document/output")
        pdf_path = base_path / "Delivery condition_501001_DL-06-ST-463-ENG Rev J.pdf"

        detection_path = base_path / "results/detection"
        structure_path = base_path / "results/structure"
        
        # base_path의 마지막 디렉토리 이름과 pdf_path의 파일 이름(확장자를 제외한 부분)을 결합하여 file_prefix 생성
        file_prefix = f"{base_path.stem}_{pdf_path.stem}"

        pdfplumber_extracted_text = process_pdf_text_from_plumber(pdf_path, detection_path, file_prefix)

        # for element in pdfplumber_extracted_text:
        #     print(f"Type: {element.type}, Page: {element.page_number}, Table Index: {element.table_index}")
        #     print(element.text)
        #     print("-" * 80)

        postprocess_result = postprocess_with_datr(pdfplumber_extracted_text, structure_path, file_prefix)

        for element in postprocess_result:
            print(f"Type: {element.type}, Page: {element.page_number}, Table Index: {element.table_index}")
            print(element.text)
            print("-" * 80)

    except Exception as e:
        print(f"An error occurred: {e}")
