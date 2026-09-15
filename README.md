<div align="center">

# FIP — Food Image Processing

### From a single RGB image to food instances, portion weight, and nutritional insight

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Detectron2](https://img.shields.io/badge/Detectron2-Mask_R--CNN-0467DF)](https://github.com/facebookresearch/detectron2)
[![Format](https://img.shields.io/badge/annotations-COCO-6C63FF)](https://cocodataset.org/)
[![Research](https://img.shields.io/badge/status-research_prototype-F59E0B)](#scope-and-limitations)

**A research pipeline for instance-level food understanding that connects visual segmentation with physically informed weight estimation.**

</div>

---

## Why this project matters

Recognizing *what* is on a plate is only the first step toward automatic dietary assessment. A useful system must also separate individual food items, estimate their quantity, and connect those estimates to nutritional information—ideally without depth sensors or specialized acquisition hardware.

FIP investigates that full chain using monocular RGB images. It combines:

- **instance segmentation** with COCO-pretrained Mask R-CNN models;
- **object-level physical metadata**, including measured weight, volume, and density;
- **class-specific calibration** that maps projected mask area to estimated food mass; and
- **three complementary data sources**: manually captured photographs, GPT-generated scenes, and automatically annotated copy-paste composites.

The central research result is especially practical: when segmentation outputs, density inputs, and evaluation samples are held fixed, **class-specific calibration consistently outperforms a single global coefficient** across every evaluated dataset configuration.

## At a glance

| Capability | Implementation |
|---|---|
| Food localization | Mask R-CNN bounding-box prediction |
| Pixel-level understanding | Instance segmentation masks |
| Feature extraction | ResNet-50/101 with Feature Pyramid Networks |
| Weight estimation | Mask area × food density × learned calibration coefficient |
| Dataset interoperability | COCO JSON annotations |
| Synthetic enrichment | RGBA object extraction, constrained copy-paste composition, automatic masks |
| Evaluation | COCO AP/AP50/AP75 and dish-level RMSE/MAE/MAPE |

## Data in three domains

<table>
  <tr>
    <th width="33%">Controlled real capture</th>
    <th width="33%">GPT-generated scene</th>
    <th width="33%">Copy-paste composite</th>
  </tr>
  <tr>
    <td><img src="dataset/images/photo_100_2026-03-29_14-47-55.jpg" alt="Real food image" /></td>
    <td><img src="dataset/gpt_images/photo_100_2026-04-27_18-09-09.jpg" alt="GPT-generated food image" /></td>
    <td><img src="dataset/synthetic_dataset/train/train_00000.jpg" alt="Copy-paste synthetic food image" /></td>
  </tr>
  <tr>
    <td align="center">Measured portions and manually verified masks</td>
    <td align="center">Visual and category expansion</td>
    <td align="center">Automatic scene and annotation generation</td>
  </tr>
</table>

The repository snapshot contains the following core datasets:

| Dataset | Images | Instances | Categories | Role |
|---|---:|---:|---:|---|
| FIPreal | 261 | 821 | 22 | Controlled real-world acquisition with physical metadata |
| FIPgpt | 165 | 483 | 37 | AI-generated category and appearance enrichment |
| Copy-paste synthetic | 750 | 2,238 | 37 in this snapshot | Automatically composed and annotated scenes |
| NutritionVerse-Real | 889 | 4,306 | 44 food classes¹ | Public-data baseline and extended taxonomy |
| FIPextended | 1,315 | 5,610 | 61 | Combined NutritionVerse-Real + FIPreal + FIPgpt experiment |

<sub>¹ The bundled COCO file contains one additional umbrella category, `food-ingredients`; the paper reports 44 food categories after excluding it.</sub>

## End-to-end methodology

```text
Annotated real + GPT images
            │
            ▼
   COCO polygons / RLE masks ──► RGBA object cut-outs
            │                              │
            │                              ▼
            │                    constrained copy-paste
            │                    + automatic COCO labels
            ▼                              │
       dataset registration ◄──────────────┘
            │
            ▼
  COCO-pretrained Mask R-CNN + ResNet-FPN
            │
            ├──► bounding boxes
            ├──► class labels
            └──► instance masks ──► projected area A
                                          │
                                  density ρ + coefficient Kc
                                          │
                                          ▼
                              estimated weight: Ŵ = AρKc
```

### 1. High-quality real-world data

FIPreal was captured with an iPhone 15 under controlled lighting, camera distance, background, and plate conditions. Each image contains multiple separated ingredients. Food instances were weighed with 1 g precision; volume was measured by water displacement; density was derived from mass divided by volume. Polygon masks were prepared in CVAT with SAM 2 assistance and manually refined—a process requiring approximately 20 hours of annotation work.

### 2. Scalable synthetic enrichment

The repository includes two scripts that turn existing annotations into new training data:

- [`dataset/extract.py`](dataset/extract.py) decodes polygon or RLE masks, falls back to bounding boxes when necessary, normalizes class aliases, and exports transparent RGBA crops by category.
- [`dataset/generate_synthetic.py`](dataset/generate_synthetic.py) samples 2–4 objects per image, applies scale and rotation transforms, constrains placement to the plate, prevents object overlap, and emits images with complete COCO annotations.

Generation is deterministic by default (`RANDOM_SEED = 42`) and produces a 600/150 train/test split.

### 3. Instance segmentation

The experiments fine-tune COCO-pretrained Mask R-CNN models in Detectron2. FIPreal and FIPgpt use ResNet-50-FPN for 4,000 iterations; the broader 61-class FIPextended configuration uses ResNet-101-FPN for 12,000 iterations. Multi-scale resizing and photometric augmentation support variation in scale and appearance.

### 4. Physically informed weight estimation

For a predicted binary mask `M`, projected area is the number of foreground pixels:

```math
A_i = \sum_x \sum_y M_i(x,y)
```

With food density `ρᵢ` and a training-derived class coefficient `Kc`, object weight is estimated as:

```math
\hat{W}_i = A_i \rho_i K_c
```

Dish weight is the sum of its retained object estimates. Calibration coefficients are learned only from training samples and then applied to held-out samples without recalibration.

## Results

### Instance segmentation

| Dataset configuration | Mask AP ↑ | AP50 ↑ | AP75 ↑ |
|---|---:|---:|---:|
| NutritionVerse-Real | 72.10 | 84.20 | 80.80 |
| **FIPreal** | **89.40** | **94.10** | **92.00** |
| FIPgpt | 58.95 | 60.47 | 60.47 |
| Copy-paste synthetic | 52.80 | 58.60 | 55.00 |
| FIPextended | 75.96 | 80.51 | 79.13 |

FIPextended also reached **84.2% F1**, **85.8% recall**, and **99.0% Hamming accuracy** in the paper's multilabel recognition analysis while expanding the output space from 44 to 61 food categories.

### Dish-level weight estimation

| Dataset configuration | Global RMSE (g) | Class-specific RMSE (g) ↓ | Global MAE (g) | Class-specific MAE (g) ↓ | Global MAPE | Class-specific MAPE ↓ |
|---|---:|---:|---:|---:|---:|---:|
| NutritionVerse-Real | 233.75 | **168.26** | 186.54 | **109.23** | 71.58% | **36.07%** |
| **FIPreal** | 181.57 | **116.86** | 123.78 | **69.42** | 44.93% | **22.83%** |
| FIPgpt | 216.62 | **153.43** | 156.48 | **112.62** | 47.59% | **34.24%** |
| Copy-paste synthetic | 275.00 | **198.00** | 205.00 | **139.00** | 82.00% | **46.00%** |
| FIPextended | 208.80 | **147.46** | 156.22 | **91.04** | 57.68% | **29.37%** |

On FIPreal, class-specific calibration reduced RMSE by **35.6%**, MAE by **43.9%**, and MAPE by **49.2%** relative to global calibration.

> [!IMPORTANT]
> The calibration comparison within each row is controlled: it uses the same model outputs, density inputs, and evaluation samples. Comparisons *between* dataset rows are descriptive rather than a controlled dataset-only ablation because backbones, schedules, augmentation, thresholds, and evaluation domains differ.

## Repository map

```text
.
├── first_experiment.ipynb          # full experimental workspace
├── train.json / test.json          # FIPreal 80/20 COCO split
├── train_annotations_gpt.json      # FIPgpt training annotations
├── test_annotations_gpt.json       # FIPgpt test annotations
├── dataset/
│   ├── annotations/                # FIPreal COCO source annotations
│   ├── annotations_gpt/            # FIPgpt COCO source annotations
│   ├── images/                     # controlled real photographs
│   ├── gpt_images/                 # generated food scenes
│   ├── extracted_objects/          # class-grouped RGBA cut-outs
│   ├── synthetic_dataset/          # generated images + COCO labels
│   ├── merged_final_annotations/   # FIPextended train/test annotations
│   ├── metadata.xlsx               # physical and nutritional metadata
│   ├── dish_weights.csv            # per-dish ingredient weights
│   ├── extract.py                  # object extraction pipeline
│   └── generate_synthetic.py       # copy-paste generator
└── dataset_nutri_verse/            # NutritionVerse-Real data and metadata
```

## Getting started

### Prerequisites

- Python 3.10+
- PyTorch and torchvision matching your CUDA/CPU environment
- Detectron2
- OpenCV, NumPy, pandas, matplotlib, scikit-learn, pycocotools, Pillow, tqdm, and Jupyter

Detectron2 installation is platform- and CUDA-specific; follow its [official installation guide](https://detectron2.readthedocs.io/en/latest/tutorials/install.html) before opening the notebook.

### Explore and reproduce the experiments

```bash
git clone https://github.com/FIIT-IDSA/fip-ai.git
cd fip-ai
jupyter lab first_experiment.ipynb
```

The notebook is an experiment log rather than a linear production script. Run the section matching the dataset configuration you want to reproduce, and review its paths and device setting (`cuda` or `cpu`) first. Model checkpoints and training-output directories are intentionally excluded from version control.

### Regenerate the copy-paste dataset

The extraction script uses paths relative to `dataset/`, while the generation script resolves paths from its own location:

```bash
cd dataset
python extract.py
python generate_synthetic.py
```

> [!WARNING]
> `generate_synthetic.py` resets `dataset/synthetic_dataset/` before writing a new deterministic 600/150 split. Back up that directory if you need to preserve an existing generated version.

## Scope and limitations

This repository is a **research snapshot**. Its strengths are the complete data-construction workflow, rich COCO annotations, physical-metadata experiments, and preserved notebook outputs. It is not yet a packaged inference library or one-command benchmark.

Key experimental boundaries are:

- FIPreal was acquired with one camera setup under controlled conditions; performance on unconstrained meal photography still requires independent validation.
- Monocular area-to-weight calibration depends on acquisition geometry and may need recalibration for different cameras, distances, resolutions, or presentation conditions.
- GPT weights are prompt-specified nominal values, not physical measurements.
- Copy-paste data showed a learnable signal but only moderate within-domain segmentation performance and limited observed transfer in the evaluated setup.
- Cross-dataset rankings cannot isolate the causal effects of dataset quality, metadata completeness, or model complexity.

These limitations motivate the next research steps: larger multi-device acquisition, common-protocol ablations, independent real-world evaluation, domain-aware training, and depth- or multi-view-assisted volume estimation.

## Research context

This repository accompanies the manuscript:

> **Food Weight Estimation from Images: The Role of Dataset Quality, Volume, and Density Information**  
> Alisa Podolska and Giang Nguyen  
> Faculty of Informatics and Information Technologies, Slovak University of Technology in Bratislava

If you build on this work, please cite the manuscript once its final bibliographic record is available. A provisional BibTeX entry is provided below:

```bibtex
@article{podolska_food_weight_estimation,
  title   = {Food Weight Estimation from Images: The Role of Dataset Quality, Volume, and Density Information},
  author  = {Podolska, Alisa and Nguyen, Giang},
  note    = {Manuscript}
}
```

## Acknowledgements

Experiments were carried out with computational support from the **IDC Lab (IDSA), FIIT STU in Bratislava**. The research was supported by **INTERREG SK-AT project No. 404601FBH3 — Building Regional Innovation Ecosystems**, co-funded by the European Union.

Generative AI was used as part of the research methodology to create the GPT-generated image dataset. All reported interpretations and conclusions remain the responsibility of the authors.

---

<div align="center">

**Built at FIIT STU to make visual dietary assessment more measurable, transparent, and data-aware.**

</div>
