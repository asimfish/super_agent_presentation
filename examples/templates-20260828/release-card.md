# Release card: showcase-grasp-dp, version 1.2

Release status: evaluated on two simulation suites and approved for internal
research use; the headline result is 84.2% grasp success on suite A. All facts
below are synthetic showcase data; they demonstrate the template, not a real
release.

## Identity and access

Diffusion-policy grasping checkpoint, version 1.2, released 2026-08-28 under a
research-only license. Persistent locator: commit 3f2c1a9 in the synthetic
showcase repository, checkpoint directory `releases/grasp-dp-1.2/`. Owner: the
showcase robotics team; issues go to the repository tracker. Intended audience
is internal research; the weights are not published outside the organization.

## Intended use and out-of-scope use

Intended: tabletop grasping of rigid objects in the two evaluated simulation
suites, and research on gating and recovery behavior. Out of scope: deformable
objects, transparent objects, real-robot deployment without a new safety
review, and any use where a failed grasp can damage hardware. None of the
out-of-scope settings were evaluated.

## Composition and provenance

Training data: 18,400 synthetic teleoperation episodes collected 2026-05 to
2026-07 in the showcase simulator. Filtering removed 1,210 episodes for
truncated trajectories and 342 for annotation conflicts, leaving 16,848; the
counts per step are logged in the dataset manifest. Known gap: fewer than 3%
of episodes contain clutter above six objects. No human-subject or personal
data is involved.

## Evaluation

Primary metric: grasp success rate over 200 scripted scenes per suite, higher
is better, five seeds per cell. Suite A: 84.2% mean, standard deviation 1.9
points. Suite B: 71.5% mean, standard deviation 2.7 points. Clutter slice
above six objects: 58.0%, notably below the aggregate. Latency at the default
gate: 46 ms per action chunk on the reference GPU. Full protocol and per-seed
tables live in the version 1.2 experiment report; real-robot transfer was not
evaluated.

## Known limitations and failure modes

The dominant failure mode is a repeated regrasp loop on flat, thin objects,
which accounts for 61% of observed failures in suite B. Success degrades with
clutter density, and the policy was never exposed to moving objects. The gate
suppresses but does not eliminate collisions with scene fixtures; residual
collision rate is 0.8% of episodes.

## Reproduction

Training and evaluation code sit at the same commit 3f2c1a9; configuration
files and the five seeds are checked in next to the checkpoint. A third party
inside the organization can reproduce evaluation exactly from the released
artifacts; retraining additionally needs the dataset manifest and roughly 310
GPU-hours on the reference hardware.

## Maintenance

Version 1.3 is planned when the clutter gap is addressed; version 1.2 stays
available under the same locator after that. Breaking interface changes bump
the major version. Defects are reported through the repository tracker.
