# Native CFD archives

The complete generated CFD directories are preserved as split, zstd-compressed tar archives in Git LFS. Source, reports, compact result tables, animations and CAD remain directly accessible elsewhere in `AA Project/`.

`../import-manifest.json` lists every imported source file. Its `archives` table lists the parts, byte counts and SHA-256 hashes. Archive parts must be joined in numeric order before decompression. Part files in the migration checkout may contain LFS pointers until explicitly downloaded. The original native outputs remain in the earlier local workspace.

| Archive group | Restored path under `AA Project/` |
|---|---|
| `pass-by` | `Airflow-Assessment/pass-by-study/cfd` |
| `motor-seat` | `Airflow-Assessment/motor-seat-study/cfd` |
| `design-search` | `Airflow-Assessment/optimization/cases` |
| `early-cfd` | `Airflow-Assessment/cases` |

To avoid downloading all large artifacts at clone time:

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone --branch ege https://github.com/zcong0202/Adiabatic-Air-Expansion.git
cd Adiabatic-Air-Expansion
# Reports, CAD, images and existing deliverable bundles; skip full native archives.
git lfs pull --exclude='AA Project/CFD-Archives/**,AA Project/Airflow-Assessment/mass-flow-study/archives/**'
```

To download and restore one native study, run from the repository root. Install `zstd` first. Allow sufficient disk space for both the downloaded archive and extracted output. Extracting replaces matching generated files; use a separate destination to inspect an archive independently.

```bash
git lfs pull --include='AA Project/CFD-Archives/native-pass-by.tar.zst.part*' --exclude=''
cat 'AA Project/CFD-Archives/'native-pass-by.tar.zst.part* | zstd -d -c | tar -xf - -C 'AA Project'
```

Change `pass-by` to another archive group as needed. Existing compact ZIP deliverables are also retained. Their manifests describe their selected evidence; the native archives preserve the full original CFD directories, including failed and historical cases.

Excluded items are replaceable runtimes and caches: Python virtual environments, Lean `.lake` builds, `node_modules`, Python bytecode, Swift builds and macOS metadata. The Lean toolchain and dependency lock file remain in the repository.

Generated case directories are ignored to prevent accidental commits of expanded solver fields. Existing tracked replay dictionaries and audit JSON remain versioned. Add any new replay dictionaries deliberately with `git add -f`; keep full generated fields in the archives.

## New mass-flow sweep

The 23 October sweep keeps each complete run in `../Airflow-Assessment/mass-flow-study/archives/CASE.zip` through Git LFS. Per-case archive records in the study results include SHA-256 and verified field counts. These ZIPs contain the case folder itself; unzip into that study’s `cfd/cases/` directory. CAD, figures and the interactive result viewer remain directly linked from the study. Native ZIPs can be fetched one at a time with `git lfs pull --include='AA Project/Airflow-Assessment/mass-flow-study/archives/CASE.zip' --exclude=''`.
