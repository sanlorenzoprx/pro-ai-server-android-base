# Native Runtime Research Note

This note records the Research Pause for the next phone runtime direction.

It follows [RESEARCH_PAUSE_SOP.md](RESEARCH_PAUSE_SOP.md) and is intended to support Milestone 3 in [NEXT_MILESTONES.md](NEXT_MILESTONES.md).

## What We Are Trying To Build

We are trying to replace or reduce dependence on the current Termux/Debian/Ollama phone runtime without breaking the proven Windows host control plane.

The target outcome is:

- lower install friction on Android
- better phone-side lifecycle control
- preserved host-side API contract
- preserved USB-first `adb forward tcp:11434 tcp:11434` workflow
- a runtime path that can scale beyond the current proof lane

## Similar Projects Reviewed

### `llama.cpp`

Source:

- `ggml-org/llama.cpp` Android docs

Relevant findings:

- official Android GUI binding exists through `examples/llama.android`
- official Android cross-compile path exists through Android NDK
- runtime checks allow use across devices with different CPU feature levels
- official docs still include a Termux CLI path and a host cross-compile plus `adb push` path

Why it matters:

- strongest candidate for the actual long-term inference engine
- closest fit to our need for broad Android-side control
- least product risk compared with keeping the full runtime story inside Debian/Termux

Classification:

- `adopt`

### `Llamatik`

Source:

- `ferranpons/Llamatik`

Relevant findings:

- Kotlin API is exposed through a clean `LlamaBridge` abstraction
- the library surface includes model init, generation, streaming, embeddings, and shutdown
- architecture is strongly aligned with a companion-managed runtime rather than shell-driven orchestration

Why it matters:

- strong reference for the app/runtime boundary
- strong reference for Kotlin-native structure
- useful for understanding how to wrap `llama.cpp` behind a stable higher-level API

Classification:

- `adapt`

### `Maid`

Source:

- `Mobile-Artificial-Intelligence/maid`

Relevant findings:

- Android app with local inference through `llama.cpp`
- supports remote providers including Ollama and OpenAI-compatible services
- includes curated model download UX and bring-your-own GGUF flow

Why it matters:

- strong reference for Android-side model management UX
- strong reference for local plus remote product shape
- useful for download and session UX patterns

Classification:

- `adapt`

### `MLC LLM`

Source:

- `mlc-ai/mlc-llm`

Relevant findings:

- MLCEngine exposes an OpenAI-compatible API
- Android support is documented around OpenCL on Adreno and Mali GPUs
- the project is a universal deployment engine, not a narrow Android host-product fit

Why it matters:

- very strong technical reference for API-facing engine design
- useful if we later want a newer-device performance lane
- weaker fit for the baseline because it adds more engine and compiler complexity than we need right now

Classification:

- `reference`

## What We Can Adopt

- `llama.cpp` as the likely long-term inference engine base

## What We Can Adapt

- `Llamatik` API and wrapper patterns for Android/Kotlin runtime control
- `Maid` model download and Android UX patterns

## What We Should Avoid

- treating Termux/Debian/Ollama as the final product runtime
- replacing the host control plane while trying to solve the phone runtime
- overcommitting to a heavy engine stack before we lock the host contract and runtime wrapper boundary

## What Is Novel In Our Approach

The novelty is not raw on-device inference by itself.

The novelty is the combination of:

- Windows-managed Android host control
- local-first USB-oriented setup and diagnostics
- adaptive Android compatibility decisions
- a swappable phone runtime underneath a stable host-side API and transport contract

That is where our effort should stay concentrated.

## Build / Adapt / Integrate / Defer Decision

Decision:

- build around `llama.cpp`
- adapt architecture patterns from `Llamatik`
- adapt UX and model-management patterns from `Maid`
- defer `MLC LLM` to a possible higher-performance future lane

## Recommendation

Stay aligned with the current repo direction.

- Do not rethink the repo base again.
- Preserve the Windows control plane.
- Preserve the Ollama-compatible host contract.
- Use the current Termux/Debian/Ollama lane as the transitional evidence lane.
- Start defining a native runtime wrapper around `llama.cpp`.

## Directional Impact

This research does not currently overturn repo philosophy or support boundaries.

It reinforces the existing transition plan:

- `llama.cpp` is still the leading native-runtime candidate
- the host contract should stay stable
- the phone runtime problem should be solved from this base instead of by replacing the whole product shape

Because the research supports the current direction rather than changing it, no repo-level go/no-go pause is required at this stage.
