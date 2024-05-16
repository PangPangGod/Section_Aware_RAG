from pdf2image import convert_from_path
import fitz
from pathlib import Path
import argparse
import platform
from PIL import ImageDraw
import json
import os

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', help='input PDF data directory')
    parser.add_argument('--output_dir', help='output image directory')
    parser.add_argument('--postfix', choices=('.jpg', '.png'))
    args = parser.parse_args()
    return args

def get_words_from_pdf(page, image_size):
    """
    page: fitz.Page
    image_size: (width, height)
    output: a list of {"bbox": [x1, y1, x2, y2], "text": "Effect", "flags": 0, "span_num": 682, "line_num": 0, "block_num": 0}
    """
    mediabox = page.mediabox
    scale_height = image_size[1] / (mediabox[3] - mediabox[1])
    scale_width = image_size[0] / (mediabox[2] - mediabox[0])
    def scale_box(box):
        box[0], box[2] = box[0] * scale_width, box[2] * scale_width
        box[1], box[3] = box[1] * scale_height, box[3] * scale_height
        return box
    page_words = page.get_text_words()
    page_words = [{'bbox': scale_box(list(x[0:4])), 
                   'text': x[4], 
                   'flags': 0, 
                   'span_num': i, 
                   'line_num': x[6], 
                   'block_num': x[5]} for i, x in enumerate(page_words)]
    return page_words

if __name__ == "__main__":
    args = get_args()
    root = Path(args.input_dir)
    res = Path(args.output_dir)
    res_image = res / 'images'
    res_image.mkdir(exist_ok=True, parents=True)
    res_word = res / 'words'
    res_word.mkdir(exist_ok=True, parents=True)
    postfix = args.postfix

    os_type = platform.system()
    separator = '/' if os_type == 'Linux' else '\\' # windows

    error_files = []
    success_files = []
    pdf_files = sorted(list(root.glob(f'**{separator}*.[pP][dD][fF]')))
    success_imgs_count = 0

    for fname in pdf_files:
        pdf_basename = fname.stem
        folder_name = fname.parent.name
        folder_name = folder_name.split(')')[0] # for simplicity
        pdf_filename = f'{folder_name}_{fname.stem}'
        
        try:
            pages = convert_from_path(fname, dpi=300)
            pages_fitz = fitz.open(fname)
            print('successful PDF reading')

            for page_num, (page, page_fitz) in enumerate(zip(pages, pages_fitz)):
                print(f'{pdf_filename}_page{page_num}{postfix}')                
                page_words = get_words_from_pdf(page_fitz, page.size)
                # # check
                # draw = ImageDraw.Draw(page)
                # for word in page_words:
                #     box = word['bbox']
                #     draw.rectangle(box, outline=(255,0,0), width=4)

                page.save(res_image / f'{pdf_filename}_page{page_num}{postfix}')
                with open(res_word / f'{pdf_filename}_page{page_num}_words.json', 'w', encoding='utf-8') as f:
                    json.dump(page_words, f, indent=2, ensure_ascii=False)
                success_imgs_count += 1

            success_files.append(pdf_filename)
            print(f'convert pdf from {fname} to {pdf_filename}_page#{postfix}')
        except Exception as e:
            print(f'error occured while converting pdf from {fname} to {pdf_filename}_page#{postfix}')
            print(e)
            error_files.append(pdf_filename)
            continue

    print('======== Report ========')
    print(f'Processed {len(pdf_files)} pdf files.')
    print(f'Successed {len(pdf_files)-len(error_files)} pdf files, Failed {len(error_files)} pdf files.')
    print(f'Successed {success_imgs_count} pages.')

    with open(root / 'report.txt', 'w') as f:
        f.write('======== Report ========\n')
        f.write(f'Processed {len(pdf_files)} pdf files.\n')
        f.write(f'Successed {len(pdf_files)-len(error_files)} pdf files, Failed {len(error_files)} pdf files.\n')
        f.write(f'Successed {success_imgs_count} pages.\n')
        f.write('========================\n')
        f.write('Successful pdf file list:\n')
        f.write('\n'.join(success_files) + '\n')
        f.write('========================\n')
        f.write('Failed pdf file list:\n')
        f.write('\n'.join(error_files) + '\n')
