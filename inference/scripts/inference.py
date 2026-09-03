"""Run deterministic inference for the trained Franka Push SAC policy."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import gymnasium as gym
import imageio.v2 as imageio
import numpy as np
from stable_baselines3 import SAC


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "panda_mujoco_gym_src"
DEFAULT_MODEL = (
    PROJECT_ROOT
    / "models/baseline/SAC_HER_Push_MuJoCo3_env4_bs512_ds0.12_dg0.05_seed42_20260831_051030_final.zip"
)

if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from panda_mujoco_gym.envs.push import FrankaPushEnv  # noqa: E402


class FrankaPushLayeredRewardEnv(FrankaPushEnv):
    """The exact reward and termination wrapper used by the training notebook."""

    def __init__(
        self,
        reward_a: float = 1.0,
        reward_k: float = 5.0,
        d_switch: float = 0.12,
        d_success: float = 0.05,
        max_episode_steps: int = 50,
        terminate_on_success: bool = True,
        render_mode: str | None = None,
    ) -> None:
        super().__init__(reward_type="dense", render_mode=render_mode)
        if not 0.0 < d_success < d_switch:
            raise ValueError("Require 0 < d_success < d_switch")

        self.reward_a = float(reward_a)
        self.reward_k = float(reward_k)
        self.d_switch = float(d_switch)
        self.d_success = float(d_success)
        self.distance_threshold = self.d_success
        self.custom_max_episode_steps = int(max_episode_steps)
        self.terminate_on_success = bool(terminate_on_success)
        self._custom_elapsed_steps = 0

    def compute_reward(self, achieved_goal, desired_goal, info):
        achieved_goal = np.asarray(achieved_goal, dtype=np.float32)
        desired_goal = np.asarray(desired_goal, dtype=np.float32)
        distance = np.linalg.norm(achieved_goal - desired_goal, axis=-1)
        outer_reward = -1.0 - self.reward_a * (
            np.tanh(self.reward_k * distance)
            - np.tanh(self.reward_k * self.d_switch)
        )
        reward = np.where(distance > self.d_switch, outer_reward, -1.0)
        reward = np.where(distance <= self.d_success, 0.0, reward)
        return np.asarray(reward, dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        self._custom_elapsed_steps = 0
        return super().reset(seed=seed, options=options)

    def step(self, action):
        obs, reward, _terminated, _truncated, info = super().step(action)
        self._custom_elapsed_steps += 1

        distance = float(np.linalg.norm(obs["achieved_goal"] - obs["desired_goal"]))
        success = distance <= self.d_success
        info = dict(info)
        info.update(
            is_success=success,
            distance_to_goal=distance,
            reward_layered=float(reward),
            reward_region=(
                "success"
                if success
                else "sparse_inner"
                if distance <= self.d_switch
                else "dense_outer"
            ),
        )
        terminated = success if self.terminate_on_success else False
        truncated = self._custom_elapsed_steps >= self.custom_max_episode_steps
        return obs, float(reward), bool(terminated), bool(truncated), info


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--episodes", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=5042)
    parser.add_argument("--max-steps", type=int, default=50)
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--render",
        choices=("none", "human", "rgb_array"),
        default="none",
        help="Use human for a live MuJoCo window or rgb_array for off-screen frames.",
    )
    parser.add_argument("--video", type=Path, help="Save the first episode as MP4.")
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument(
        "--hold-start", type=float, default=1.0, help="Seconds to hold the first frame."
    )
    parser.add_argument(
        "--hold-end", type=float, default=2.0, help="Seconds to hold the final frame."
    )
    parser.add_argument(
        "--output-csv", type=Path, default=PROJECT_ROOT / "inference/results/inference_results.csv"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.episodes < 1 or args.max_steps < 1 or args.fps < 1:
        raise ValueError("--episodes and --max-steps must be positive")
    if args.hold_start < 0 or args.hold_end < 0:
        raise ValueError("--hold-start and --hold-end cannot be negative")
    if not args.model.is_file():
        raise FileNotFoundError(f"Model not found: {args.model}")

    render_mode = "rgb_array" if args.video else None if args.render == "none" else args.render
    env = FrankaPushLayeredRewardEnv(
        max_episode_steps=args.max_steps,
        render_mode=render_mode,
    )
    # SB3 reconstructs the saved HerReplayBuffer metadata during load, so an
    # environment is required even though inference never uses the buffer.
    model = SAC.load(str(args.model), env=env, device=args.device)
    rows: list[dict[str, float | int]] = []
    frames: list[np.ndarray] = []

    try:
        for episode in range(args.episodes):
            obs, _ = env.reset(seed=args.seed + episode)
            episode_return = 0.0
            min_distance = float("inf")
            final_distance = float("nan")
            success = False
            steps = 0

            for step in range(args.max_steps):
                if episode == 0 and args.video:
                    frame = env.render()
                    if frame is not None:
                        frames.append(frame)

                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                steps = step + 1
                episode_return += float(reward)
                final_distance = float(info["distance_to_goal"])
                min_distance = min(min_distance, final_distance)
                success = success or bool(info["is_success"])
                if terminated or truncated:
                    break

            # Capture the reached state as well; the loop captures frames before
            # actions, so without this frame a successful video ends too early.
            if episode == 0 and args.video:
                frame = env.render()
                if frame is not None:
                    frames.append(frame)

            rows.append(
                {
                    "episode": episode,
                    "seed": args.seed + episode,
                    "steps": steps,
                    "return": episode_return,
                    "success": int(success),
                    "final_distance": final_distance,
                    "min_distance": min_distance,
                }
            )
            print(
                f"episode={episode:03d} steps={steps:02d} success={int(success)} "
                f"return={episode_return:8.3f} final_d={final_distance:.4f} m "
                f"min_d={min_distance:.4f} m"
            )
    finally:
        env.close()

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    if args.video:
        if not frames:
            raise RuntimeError("MuJoCo returned no video frames")
        start_hold = [frames[0]] * round(args.hold_start * args.fps)
        end_hold = [frames[-1]] * round(args.hold_end * args.fps)
        frames = start_hold + frames + end_hold
        args.video.parent.mkdir(parents=True, exist_ok=True)
        imageio.mimsave(args.video, frames, fps=args.fps)
        print(f"video={args.video.resolve()}")

    success_rate = float(np.mean([row["success"] for row in rows]))
    mean_final_distance = float(np.mean([row["final_distance"] for row in rows]))
    mean_min_distance = float(np.mean([row["min_distance"] for row in rows]))
    print(
        f"summary episodes={len(rows)} success_rate={success_rate:.3f} "
        f"mean_final_d={mean_final_distance:.4f} m "
        f"mean_min_d={mean_min_distance:.4f} m"
    )
    print(f"results={args.output_csv.resolve()}")


if __name__ == "__main__":
    main()
