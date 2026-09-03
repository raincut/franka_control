# Franka Control Project Catalog

This catalog describes the project after its top-level artifacts were organized by purpose.

## Training notebooks

- `notebooks/Franka_A_Formal500k_DistanceLayered_AutoDL_MuJoCo3_output.ipynb` — formal 500k-step Distance-Layered experiment (A).
- `notebooks/Franka_B_Formal500k_Dense2Sparse_AutoDL_MuJoCo3_output.ipynb` — formal 500k-step Dense-to-Sparse experiment (B).
- `notebooks/Franka_Advanced_ForceFeedback_SAC_HER_AutoDL_MuJoCo3_outpu.ipynb` — formal 500k-step Force Feedback experiment (C).
- `notebooks/Franka_Push_SAC_HER_MuJoCo3_Colab_FINAL.ipynb` — original/reference Colab notebook.

## Models and training archives

- `franka_rl_model_backup/experiment_A_distance_layered/` — A models, checkpoints, config, eval CSV, and notebook.
- `franka_rl_model_backup/experiment_B_dense2sparse/` — B models, checkpoints, config, eval CSV, and notebook.
- `franka_rl_model_backup/experiment_C_force_feedback/` — C models, checkpoints, config, eval CSV, and notebook.
- `models/baseline/SAC_HER_Push_MuJoCo3_env4_bs512_ds0.12_dg0.05_seed42_20260831_051030_final.zip` — previous baseline inference model.
- `archives/franka_ablation.tar.gz` — original A/B training archive, including periodic checkpoints.
- `archives/franka_force_feedback.tar.gz` — original C training archive, including periodic checkpoints.

## Inference code and outputs

- `inference/scripts/` — baseline, A/B/C evaluation, video recording, and Windows launcher scripts.
- `inference/results/` — baseline, experiment, smoke, and partitioned inference CSV metrics.
- `inference/logs/` — inference execution logs.
- `inference/videos/` — baseline and A/B/C inference videos.

## Environment source

- `panda_mujoco_gym_src/` — local Franka MuJoCo Gym environment source, assets, tests, documentation, and license.

## Documentation and extracted results

- `README.md` — inference usage notes.
- `docs/TRAINING_RESULTS.md` — figures and tables extracted from the three formal training notebooks.
- `docs/training_results/assets/` — embedded notebook figures referenced by `TRAINING_RESULTS.md`.
- `docs/PROJECT_CATALOG.md` — this catalog.
- `scripts/extract_training_results.py` — reproducible notebook extraction utility.

## Generated/cache files

- `inference/__pycache__/` — Python bytecode cache; not required to reproduce training or inference.
- `inference/results/inference_smoke.csv` — empty smoke-output placeholder.
