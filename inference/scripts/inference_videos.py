"""Record exactly N deterministic environment steps for A, B, and C."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import imageio.v2 as imageio
import mujoco
import numpy as np
from stable_baselines3 import SAC
from stable_baselines3.common.monitor import Monitor

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "panda_mujoco_gym_src"))
from panda_mujoco_gym.envs.push import FrankaPushEnv


def class_from_notebook(path: Path, class_name: str):
    data = json.loads(path.read_text(encoding="utf-8"))
    for cell in data["cells"]:
        source = "".join(cell.get("source", []))
        if f"class {class_name}" in source:
            ns = {"np": np, "mujoco": mujoco, "FrankaPushEnv": FrankaPushEnv,
                  "Monitor": Monitor, "CONTACT_BODY_NAMES": ("hand", "left_finger", "right_finger", "link7"),
                  "CONTACT_COUNT_SCALE": 4.0}
            exec(source, ns)
            return ns[class_name]
    raise RuntimeError(f"{class_name} not found in {path}")


def record(model_path: Path, env, output: Path, steps: int, seed: int, fps: int) -> None:
    model = SAC.load(str(model_path), env=env, device="cpu")
    frames = []
    obs, _ = env.reset(seed=seed)
    completed = 0
    successes = 0
    try:
        for i in range(steps):
            frame = env.render()
            if frame is None:
                raise RuntimeError("MuJoCo returned no rgb_array frame")
            frames.append(frame)
            action, _ = model.predict(obs, deterministic=True)
            obs, _, terminated, truncated, info = env.step(action)
            successes += int(bool(info.get("is_success", False)))
            if terminated or truncated:
                completed += 1
                obs, _ = env.reset(seed=seed + completed)
        frame = env.render()
        if frame is not None:
            frames.append(frame)
    finally:
        env.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(output, frames, fps=fps, macro_block_size=1)
    print(f"video={output} frames={len(frames)} steps={steps} episode_resets={completed} successes={successes}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--steps", type=int, default=2000)
    p.add_argument("--fps", type=int, default=10)
    p.add_argument("--seed", type=int, default=5042)
    args = p.parse_args()
    common = dict(max_episode_steps=50, terminate_on_success=False, render_mode="rgb_array")

    a = class_from_notebook(ROOT / "notebooks/Franka_A_Formal500k_DistanceLayered_AutoDL_MuJoCo3_output.ipynb", "FrankaPushAblationEnv")
    b = class_from_notebook(ROOT / "notebooks/Franka_B_Formal500k_Dense2Sparse_AutoDL_MuJoCo3_output.ipynb", "FrankaPushAblationEnv")
    c = class_from_notebook(ROOT / "notebooks/Franka_Advanced_ForceFeedback_SAC_HER_AutoDL_MuJoCo3_outpu.ipynb", "FrankaPushForceEnv")

    record(ROOT / "franka_rl_model_backup/experiment_A_distance_layered/models/SAC_HER_distance_layered_full_seed42_20260901_142922_final.zip",
           a(**common), ROOT / "inference/videos/inference_experiment_A_2000_steps.mp4", args.steps, args.seed, args.fps)
    record(ROOT / "franka_rl_model_backup/experiment_B_dense2sparse/models/SAC_HER_dense2sparse_full_seed42_20260901_143014_final.zip",
           b(reward_mode="sparse", **common), ROOT / "inference/videos/inference_experiment_B_2000_steps.mp4", args.steps, args.seed, args.fps)
    record(ROOT / "franka_rl_model_backup/experiment_C_force_feedback/models/SAC_HER_Force_distance_layered_force_obs_only_seed42_20260901_144757_final.zip",
           c(reward_scheme="distance_layered", reward_mode="dense", use_force_obs=True,
             force_obs_scale=50.0, force_obs_clip=2.0, contact_body_names=("hand", "left_finger", "right_finger", "link7"),
             max_episode_steps=50, terminate_on_success=False, use_action_smoothing=False,
             use_force_penalty=False, use_smooth_penalty=False, render_mode="rgb_array"),
           ROOT / "inference/videos/inference_experiment_C_2000_steps.mp4", args.steps, args.seed, args.fps)


if __name__ == "__main__":
    main()
