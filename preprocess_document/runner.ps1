python .\scripts\convert_pdf_to_image.py --input_dir "data" --output_dir "data" --postfix ".png"

python .\src\inference.py `
--image_dir "data/images" `
--out_dir "data/extract_200_200_debug_with_image_save" `
--mode "extract" `
--detection_config_path "src/detection_config.json" `
--detection_model_path "model/detection.pth" `
--structure_config_path "src/structure_config.json" `
--structure_model_path "model/structure.pth" `
--html `
--csv `
--visualize `
--crops `
--objects `
--words_dir "data/words"
