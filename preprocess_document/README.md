# Table Transformer (TATR)
This repository is a clone from original [TATR](https://github.com/microsoft/table-transformer).

A deep learning model based on object detection for extracting tables from PDFs and images.

First proposed in ["PubTables-1M: Towards comprehensive table extraction from unstructured documents"](https://openaccess.thecvf.com/content/CVPR2022/html/Smock_PubTables-1M_Towards_Comprehensive_Table_Extraction_From_Unstructured_Documents_CVPR_2022_paper.html).

![table_extraction_v2](https://user-images.githubusercontent.com/10793386/139559159-cd23c972-8731-48ed-91df-f3f27e9f4d79.jpg)


Note: If you are looking to use Table Transformer to extract your own tables, here are some helpful things to know:
- TATR can be trained to work well across many document domains and everything needed to train your own model is included here. But at the moment pre-trained model weights are only available for TATR trained on the PubTables-1M dataset. (See the additional documentation for how to train your own multi-domain model.)
- TATR is an object detection model that recognizes tables from image input. The inference code built on TATR needs text extraction (from OCR or directly from PDF) as a separate input in order to include text in its HTML or CSV output.


## Model Weights
We provide different pre-trained models for table detection and table structure recognition.

<b>Table Detection:</b>
<table>
  <thead>
    <tr style="text-align: right;">
      <th>Model</th>
      <th>Training Data</th>
      <th>File</th>
      <th>Size</th>
    </tr>
  </thead>
  <tbody>
    <tr style="text-align: right;">
      <td>DETR R18-Steel</td>
      <td>Provided Steel Order Documents</td>
      <td><a href="https://drive.google.com/file/d/1CeIkHb7Vp-Yt-IqyigPgqnLp2qupGIeP/view?usp=sharing">Weights</a></td>
      <td>115.4 MB</td>
    </tr>
  </tbody>
</table>

<b>Table Structure Recognition:</b>
<table>
  <thead>
    <tr style="text-align: left;">
      <th>Model</th>
      <th>Training Data</th>
      <th>File</th>
      <th>Size</th>
    </tr>
  </thead>
  <tbody>
    <tr style="text-align: left;">
      <td>TATR-Steel</td>
      <td>Cropped tables from Provided Steel Order Documents</td>
      <td><a href="https://drive.google.com/file/d/1xT1pRZPNyE0k3s-fR6Xtb2RxDx9NjINX/view?usp=sharing">Weights</a></td>
      <td>115.5 MB</td>
    </tr>
  </tbody>
</table>


## Code Installation
Create a conda environment from the yml file and activate it as follows
```
conda env create -f environment.yml
conda activate tables-detr
```

## Model Training
The code trains models for 2 different sets of table extraction tasks:

1. Table Detection
2. Table Structure Recognition + Functional Analysis

For a detailed description of these tasks and the models, please refer to the paper.

To train, you need to specify: 1. the path to the dataset, 2. the task (detection or structure), and 3. the path to the config file, which contains the hyperparameters for the architecture and training.

To train the detection model:
```
python src/main.py --data_type detection --config_file detection_config.json --data_root_dir /path/to/detection_data
```

To train the structure recognition model:
```
python src/main.py --data_type structure --config_file structure_config.json --data_root_dir /path/to/structure_data
```

##  Inference
The inference code outputs prediction results of detection, structure recognition, or both.

To infer the entire model:
```
python src/inference.py --image_dir /path/to/input/document/images \
                        --words_dir /path/to/input/words \
                        --out_dir /path/to/output \
                        --mode extract \
                        --detection_config_path src/detection_config.json \
                        --detection_model_path /path/to/detection_model \
                        --structure_config_path src/structure_config.json \
                        --structure_model_path /path/to/recognition_model \
                        --html \
                        --csv \
                        --visualize \
                        --crops \
                        --objects
```
To infer the detection model:
```
python src/inference.py --image_dir /path/to/input/document/images \
                        --out_dir /path/to/output \
                        --mode detect \
                        --detection_config_path src/detection_config.json \
                        --detection_model_path /path/to/detection_model \
                        --visualize \
                        --crops \
                        --objects
```
To infer the structure recognition model:
```
python src/inference.py --image_dir /path/to/input/table/images \
                        --words_dir /path/to/input/words \
                        --out_dir /path/to/output \
                        --mode recognize \
                        --structure_config_path src/structure_config.json \
                        --structure_model_path /path/to/recognition_model \
                        --html \
                        --csv \
                        --visualize \
                        --objects
```

You can refer to the sample bash file ```bash_exp.sh```.

Optionally you can add or remove flags for things like saving visualizations:\
```--crops```: Save cropped table images. Only valid during detection.\
```--objects```: Save detected objects' class and location.\
```--cells```: Save cells list.\
```--html```: Save table HTML files.\
```--csv```: Save table CSV files.\
```--verbose```: Verbose outputs.\
```--visualize```: Visualize detected outputs on the images.\
```--crop_padding int```: Change the amount of padding to add around a detected table when cropping. Default: 10.\


## Get words and images from pdf file
To extract words from given pdf file, you can use PyMuPDF library.
You can use pdf2image library to render images from pdf files.
To get words and images from pdf file:
```
python scripts/convert_pdf_to_image.py --input_dir /path/to/input/pdf/files/root \
                                       --output_dir /path/to/output \
                                       --postfix /image/postfix
```
Two postfix options ```--postfix .png``` and ```--postfix .jpg``` are allowed.

## Fine-tuning and Other Model Training Scenarios
If model training is interrupted, it can be easily resumed by using the flag ```--model_load_path /path/to/model.pth``` and specifying the path to the saved dictionary file that contains the saved optimizer state.

If you want to restart training by fine-tuning a saved checkpoint, such as ```model_20.pth```, use the flag ```--model_load_path /path/to/model_20.pth``` and the flag ```--load_weights_only``` to indicate that the previous optimizer state is not needed for resuming training.

Whether fine-tuning or training a new model from scratch, you can optionally create a new config file with different training parameters than the default ones we used. Specify the new config file using: ```--config_file /path/to/new_structure_config.json```. Creating a new config file is useful, for example, if you want to use a different learning rate ```lr``` during fine-tuning.

Alternatively, many of the arguments in the config file can be specified as command line arguments using their associated flags. Any argument specified as a command line argument overrides the value of the argument in the config file.

## Citing
Our work can be cited using:
```
@software{smock2021tabletransformer,
  author = {Smock, Brandon and Pesala, Rohith},
  month = {06},
  title = {{Table Transformer}},
  url = {https://github.com/microsoft/table-transformer},
  version = {1.0.0},
  year = {2021}
}
```
```
@inproceedings{smock2022pubtables,
  title={Pub{T}ables-1{M}: Towards comprehensive table extraction from unstructured documents},
  author={Smock, Brandon and Pesala, Rohith and Abraham, Robin},
  booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
  pages={4634-4642},
  year={2022},
  month={June}
}
```


## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
