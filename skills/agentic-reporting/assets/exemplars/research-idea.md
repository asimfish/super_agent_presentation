# Exemplar: research-idea

Read this for register, not content; the mechanism and thresholds are
illustrative. Notice what it does: states the idea as a claim in one sentence,
says what would be true if it works, explains in two sentences why the gap
exists, and names a cheap first test with the result that would kill the idea.
Notice what it omits: no survey of related work, no definition of diffusion
time, no list of every risk, no roadmap beyond the first experiment.

## English

Reward guidance in diffusion sampling may only need to act in the middle of the
trajectory. Distill the reward model into a small time-conditioned head that
runs only for t in [0.3, 0.7], with the backbone and the reward model frozen
and the rest of the trajectory untouched. If the reward's useful influence
really concentrates there, per-sample cost should fall below 30% of full
online guidance while keeping at least 95% of its reward attainment. The gap
exists because the two current routes sit at the extremes: online guidance
calls the reward model at every step, and fine-tuning the reward into the
backbone gives up training independence. The first test is cheap: sweep the
window on one backbone and one reward, and measure attainment and step time
against full online guidance. If attainment stays below 90% for every window,
the core assumption is wrong and the idea stops there.

## 中文

扩散采样里的奖励引导，可能只需要在轨迹中段起作用。把奖励模型蒸馏成一个小的
时间条件引导头，只在 t∈[0.3, 0.7] 内运行，骨干和奖励模型全程冻结，窗口外的
轨迹不动。如果奖励的有效影响真的集中在中段，每样本开销应该降到全程在线引导
的 30% 以下，同时奖励达成率保住 95% 以上。这个空缺存在，是因为现有两条路线
各在一端：在线引导每一步都调奖励模型；把奖励微调进骨干则丢掉训练无关性。第
一个实验很便宜：在一个骨干、一个奖励上扫窗口，对照全程在线引导测达成率和
每步耗时。如果所有窗口的达成率都不到 90%，核心假设就是错的，想法到此为止。
