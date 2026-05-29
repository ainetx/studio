# Brainstorm: Global cfs Runtime Mode

Date: 2026-05-29

## Topic

Global mode for `cfs`: skills and sub-agents are available globally across all repositories, while each repository keeps only configuration, lock/update policy, and cache metadata. Local/per-repo mode remains available and must not depend on global runtime.

## Panel

- Runtime Architect
- Versioning & Reproducibility Lead
- Developer Experience Designer
- Offline & Cache Systems Engineer
- Compatibility & Adoption Strategist

## Decisions

- `init_mode`: `cfs init` creates only `{cf-studio-path}/config` by default.
- `local_init`: `cfs init --local` creates `.core` and `.gen` for a fully repo-local installation.
- `command_targeting`: `cfs update` and `cfs generate-agents` inspect init mode by default.
- `explicit_targeting`: `cfs update --local|--global` and `cfs generate-agents --local|--global` override the default target.
- `global_mode`: skills and sub-agents are global; the repo stores config, lock/update policy, and cache metadata only.
- `local_mode`: everything is per-repo, with no dependency on global runtime.
- `repo_compatibility_pin`: execution uses an immutable lock only.
- `update_policy`: semver/range policy is used only by `cfs update` to choose the next lock.
- `global_cache`: cache is immutable and multi-version.
- `offline_policy`: offline startup is allowed only after full hydration and integrity verification of the locked bundle and manifest.
- `host_footprint`: existing `{cf-studio-path}/config` is enough as the repo discovery/config surface; no extra `cfs.toml` is required by default.
- `mixed_mode`: global/config-only and local/per-repo modes are permanent first-class modes.

## Open Questions

- Exact `core.toml` schema for runtime lock and update policy.
- Global cache directory layout and bundle identity key.
- Where each supported host stores global skills/sub-agents.
- Migration path from existing `.bootstrap/.core/.gen` repositories.
- `cfs info` output for active mode, effective runtime source, lock status, and hydration status.

## Recommended Next Step

Draft a resolution matrix for `init`, `update`, `generate-agents`, runtime lookup, `--local`, and `--global`.
