# AI Decisional Tree

Python project for loading and checking the CPAISD (Core-Penumbra Acute
Ischemic Stroke Dataset). The current code downloads the dataset, reads its
study summary, separates studies by split, and checks that the corresponding
study folders are present. This repository is a portfolio/demo project and is
not intended for unrestricted reuse.

## License

This project is distributed under a proprietary license. All rights are
reserved by the copyright holder.

No permission is granted to use, copy, modify, distribute, sublicense, sell,
or otherwise exploit this repository or any of its contents without prior
written authorization from the copyright holder.

The repository is public for demonstration and review purposes only. Public
visibility does not imply permission for reuse.

## Dataset

CPAISD contains 112 anonymized non-contrast CT studies of hyperacute ischemic
stroke. The scans include expert annotations of the ischemic core and penumbra.
Kaggle reports the following study and slice counts:

| Split | Studies | Slices |
| --- | ---: | ---: |
| Training (`train`) | 92 | 8,376 |
| Validation (`val`) | 10 | 980 |
| Test (`test`) | 10 | 809 |

The dataset provides raw anonymized DICOM slices, NumPy image and mask files,
and metadata. Study-level metadata includes scanner manufacturer and model,
age, sex, NIHSS, time, and lethality; DICOM demographic/scanner fields are
retained for research. The Kaggle download is approximately 8.6 GB.

- [Dataset on Kaggle](https://www.kaggle.com/datasets/orvile/cpaisd-acute-ischemic-stroke-dataset/data)
- [Dataset DOI](https://doi.org/10.5281/zenodo.10892316)
- Dataset license: [MIT](https://opensource.org/licenses/MIT)

## Recent updates

The project has recently been updated to improve the volume-processing pipeline and make the export path more robust:

- Added the missing Parquet backend dependency (`pyarrow`) so pandas can serialize tabular volume data to `.parquet` files.
- Refactored the volume build pipeline to work with a DataFrame-based representation instead of per-voxel Python objects.
- Optimized valid-voxel extraction with a vectorized NumPy/Numba mask-based approach that keeps only non-empty voxels and adjacent background boundary voxels.
- Vectorized the 3x3x3 neighborhood extraction for the final tabular dataset, reducing Python-level overhead in the hot path.
- Volume exports are now stored in the project output folders as parquet files, ready for downstream analysis and model training.

## Requirements and setup

Use Python 3.11 or later. From the repository root, install the pinned
dependencies:

```powershell
python -m pip install -r requirements.txt
```

The project uses `kagglehub` to download the dataset. Configure Kaggle access
using the [KaggleHub authentication instructions](https://github.com/Kaggle/kagglehub#authenticate)
before the first download; the download may require network access and Kaggle
credentials. Do not commit credentials to the repository.

## Run

Run the application entry point from the repository root:

```powershell
python .\ai-decisional-tree\__main__.py
```

The entry point initializes the loader, plotter, and analyzer. The data manager
validates the summary and split folders; its loader uses KaggleHub to download
the configured dataset when needed. The pipeline now also creates tabular volume
exports in parquet format for each patient and stores them under the configured
volume folders.

## Configuration and expected files

The dataset settings are in
[`ai-decisional-tree/config/config.ini`](ai-decisional-tree/config/config.ini).
The default Kaggle dataset identifier is
`orvile/cpaisd-acute-ischemic-stroke-dataset`, and the configured output
directory is `file/`, relative to the application directory.

The loader expects to find `summary.csv` and the split folders under
`<output_path>/dataset/`, with study directories named as listed in the
summary. The summary must include `name` and `part` columns; split values are
`train`, `val`, and `test`. The loader partitions the summary by `part`, checks
each listed study folder, and records its path and immediate subfolders. It
also materializes per-patient tabular volume exports as parquet files when the
volume-building step is executed.

## Citation

If you use CPAISD, cite the dataset:

> Umerenkov, D., Kudin, S., Peksheva, M., & Pavlov, D. (2024). *CPAISD:
> Core-Penumbra Acute Ischemic Stroke Dataset* [Data set]. Zenodo.
> https://doi.org/10.5281/zenodo.10892316

The dataset's license applies to the dataset; this repository is separately
under a proprietary license. See [`LICENSE`](LICENSE).

## Disclaimer

This project and dataset are intended for research and educational use. They
are not a clinical diagnostic tool and must not be used as a substitute for
professional medical judgment.
