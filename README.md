# Franka Push RL inference

This directory runs the trained SAC + HER policy against the custom Franka Push
environment used by the training notebook. The upstream environment source is in
`panda_mujoco_gym_src`, and inference utilities are grouped under `inference/`.

## Run with the host Conda Python

From Windows Command Prompt or PowerShell:

```bat
inference\scripts\run_inference.bat
```

The command evaluates 2000 deterministic episodes, writes
`inference/results/inference_results.csv`, and records the first episode to
`inference/videos/inference_episode.mp4`. The video defaults to
10 FPS and holds the initial and final states so that the motion is easy to inspect.

For a live MuJoCo viewer instead of video recording, use Command Prompt:

```bat
%USERPROFILE%\.conda\envs\mujoco\python.exe inference\scripts\inference.py --episodes 5 --render human
```

Or use PowerShell:

```powershell
& "$env:USERPROFILE\.conda\envs\mujoco\python.exe" inference\scripts\inference.py --episodes 5 --render human
```

Useful options:

```text
--episodes N       number of evaluation episodes
--seed N           first deterministic environment seed
--video FILE.mp4   record the first episode
--render human     display the live MuJoCo viewer
--output-csv FILE  per-episode metrics destination
--fps N            recorded video FPS (default: 10)
--hold-start SEC   initial-frame hold (default: 1 second)
--hold-end SEC     final-frame hold (default: 2 seconds)
```

The deployed environment needs `gymnasium-robotics==1.4.2` in addition to the
already installed MuJoCo, Gymnasium, Stable-Baselines3, PyTorch, and imageio.
