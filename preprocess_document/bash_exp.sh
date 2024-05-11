#!/bin/bash

############################ TRAIN #########################################
# CUDA_VISIBLE_DEVICES=0 python src/main.py --data_root_dir data/input/Steel/Order-Detection \
#                                           --config_file src/detection_config.json \
#                                           --data_type detection \
#                                           --model_load_path data/saved/pretrained/pubtables1m_detection_detr_r18.pth \
#                                           --model_save_dir data/saved/detection/batch2_longer \
#                                           --mode train \
#                                           --batch_size 2 \
#                                           --num_workers 2 \
#                                           --load_weights_only \
#                                           --epochs 300 \
#                                           --checkpoint_freq 20

# CUDA_VISIBLE_DEVICES=0 python src/main.py --data_root_dir data/input/Steel/Order-Structure \
#                                           --config_file src/structure_config.json \
#                                           --data_type structure \
#                                           --model_load_path data/saved/pretrained/TATR-v1.1-All-msft.pth \
#                                           --model_save_dir data/saved/structure/batch2_longer \
#                                           --mode train \
#                                           --batch_size 2 \
#                                           --num_workers 2 \
#                                           --load_weights_only \
#                                           --epochs 300 \
#                                           --checkpoint_freq 20

############################ INFERENCE #########################################
CUDA_VISIBLE_DEVICES=0 python src/inference.py --image_dir data/input/Steel_with_words/Order-Detection/images/ \
                                               --out_dir data/output/Steel_with_words/extract_200_200_debug_with_image_save/ \
                                               --mode extract \
                                               --detection_config_path src/detection_config.json \
                                               --detection_model_path data/saved/detection/batch2_longer/model_200.pth \
                                               --structure_config_path src/structure_config.json \
                                               --structure_model_path data/saved/structure/batch2_longer/model_200.pth \
                                               --html \
                                               --csv \
                                               --visualize \
                                               --crops \
                                               --objects \
                                               --words_dir data/input/Steel_with_words/Order-Detection/words

