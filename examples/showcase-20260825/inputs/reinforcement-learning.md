# Synthetic evidence pack: reinforcement-learning

- Nature: synthetic RL fixture; not a real environment or result.
- Environment: `SyntheticReach-v0`; finite-horizon MDP, horizon 200, discount 0.99; vector observation and continuous action.
- Return: undiscounted episodic reward, higher-is-better; each seed value is the mean of 20 deterministic evaluation episodes.
- Independent training seeds: 5 per method; no exclusions or failed seeds.
- Method P returns by seed 1–5: 510, 530, 490, 520, 500.
- Method Q returns by seed 1–5: 500, 505, 495, 510, 490.
- Selection: final training checkpoint at 1 million environment steps for every seed; one fixed hyperparameter configuration per method selected before these five seeds.
- Compute: same synthetic host and 1 million environment steps per seed; wall-clock and energy not measured.
- Statistics requested by fixture: sample SD and two-sided 95% t interval over five seed-level means; no hypothesis test or multiplicity correction.
