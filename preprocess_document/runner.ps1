$scriptDir = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
Set-Location -Path $scriptDir ## .ps1 execute path from {root} to preprocess_document

python .\scripts\convert_pdf_to_image.py --input_dir "output" --output_dir "output" --postfix ".png"

python .\src\inference.py `
--image_dir "output/images" `
--out_dir "output/results" `
--mode "extract" `
--detection_config_path "src/detection_config.json" `
--detection_model_path "model/detection.pth" `
--structure_config_path "src/structure_config.json" `
--structure_model_path "model/structure.pth" `
--html `
--crops `
--objects `
--words_dir "output/words"
