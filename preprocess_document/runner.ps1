python .\scripts\convert_pdf_to_image.py --input_dir "data" --output_dir "data" --postfix ".png"

python .\src\inference.py `
--image_dir "data/images" `
--out_dir "data/results" `
--mode "extract" `
--detection_config_path "src/detection_config.json" `
--detection_model_path "model/detection.pth" `
--structure_config_path "src/structure_config.json" `
--structure_model_path "model/structure.pth" `
--html `
--crops `
--objects `
--words_dir "data/words"
