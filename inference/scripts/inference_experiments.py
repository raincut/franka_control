"""Run deterministic inference for the three formal Franka experiments."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import mujoco
import numpy as np
from stable_baselines3 import SAC
from stable_baselines3.common.monitor import Monitor

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "panda_mujoco_gym_src"
sys.path.insert(0, str(SOURCE_ROOT))
from panda_mujoco_gym.envs.push import FrankaPushEnv


def class_from_notebook(path: Path, class_name: str):
    notebook = json.loads(path.read_text(encoding="utf-8"))
    source = None
    for cell in notebook["cells"]:
        text = "".join(cell.get("source", []))
        if f"class {class_name}" in text:
            source = text
            break
    if source is None:
        raise RuntimeError(f"{class_name} not found in {path}")
    namespace = {
        "np": np,
        "mujoco": mujoco,
        "FrankaPushEnv": FrankaPushEnv,
        "Monitor": Monitor,
        "CONTACT_BODY_NAMES": ("hand", "left_finger", "right_finger", "link7"),
        "CONTACT_COUNT_SCALE": 4.0,
    }
    exec(source, namespace)
    return namespace[class_name]


def evaluate(model_path: Path, env, output: Path, episodes: int, seed: int) -> None:
    model = SAC.load(str(model_path), env=env, device="cpu")
    rows = []
    try:
        for episode in range(episodes):
            obs, _ = env.reset(seed=seed + episode)
            total = 0.0
            min_d = float("inf")
            final_d = float("nan")
            success = False
            for step in range(50):
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                total += float(reward)
                final_d = float(info["distance_to_goal"])
                min_d = min(min_d, final_d)
                success = success or bool(info["is_success"])
                if terminated or truncated:
                    break
            rows.append({"episode": episode, "seed": seed + episode,
                         "steps": step + 1, "return": total, "success": int(success),
                         "final_distance": final_d, "min_distance": min_d})
            print(f"episode={episode:03d} success={int(success)} final_d={final_d:.4f} m")
    finally:
        env.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    print(f"summary episodes={episodes} success_rate={np.mean([r['success'] for r in rows]):.3f} results={output}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--episodes", type=int, default=2000)
    p.add_argument("--seed", type=int, default=5042)
    p.add_argument("--only", choices=("A", "B", "C", "all"), default="all")
    args = p.parse_args()

    a_cls = class_from_notebook(ROOT / "notebooks/Franka_A_Formal500k_DistanceLayered_AutoDL_MuJoCo3_output.ipynb", "FrankaPushAblationEnv")
    b_cls = class_from_notebook(ROOT / "notebooks/Franka_B_Formal500k_Dense2Sparse_AutoDL_MuJoCo3_output.ipynb", "FrankaPushAblationEnv")
    c_cls = class_from_notebook(ROOT / "notebooks/Franka_Advanced_ForceFeedback_SAC_HER_AutoDL_MuJoCo3_outpu.ipynb", "FrankaPushForceEnv")

    common = dict(max_episode_steps=50, terminate_on_success=False, render_mode=None)
    if args.only in ("A", "all"):
        evaluate(ROOT / "franka_rl_model_backup/experiment_A_distance_layered/models/SAC_HER_distance_layered_full_seed42_20260901_142922_final.zip",
                 a_cls(**common), ROOT / "inference/results/inference_results_experiment_A_2000.csv", args.episodes, args.seed)
    if args.only in ("B", "all"):
        evaluate(ROOT / "franka_rl_model_backup/experiment_B_dense2sparse/models/SAC_HER_dense2sparse_full_seed42_20260901_143014_final.zip",
                 b_cls(reward_mode="sparse", **common), ROOT / "inference/results/inference_results_experiment_B_2000.csv", args.episodes, args.seed)
    if args.only in ("C", "all"):
        evaluate(ROOT / "franka_rl_model_backup/experiment_C_force_feedback/models/SAC_HER_Force_distance_layered_force_obs_only_seed42_20260901_144757_final.zip",
                 c_cls(reward_scheme="distance_layered", reward_mode="dense", use_force_obs=True,
                       force_obs_scale=50.0, force_obs_clip=2.0, contact_body_names=("hand", "left_finger", "right_finger", "link7"),
                       max_episode_steps=50, terminate_on_success=False, use_action_smoothing=False,
                       use_force_penalty=False, use_smooth_penalty=False, render_mode=None),
                 ROOT / "inference/results/inference_results_experiment_C_2000.csv", args.episodes, args.seed)


if __name__ == "__main__":
    main()
