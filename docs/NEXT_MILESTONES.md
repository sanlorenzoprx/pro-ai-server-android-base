# Next Milestones

This document records the current working milestones for the phone runtime transition from the validated Phase 22 baseline.

These milestones assume:

- the repository base is not being rethought again
- the Windows control plane remains the strongest preserved layer
- the phone runtime is the current bottleneck
- major new runtime direction work follows the Research Pause SOP

See:

- [PHONE_RUNTIME_TRANSITION.md](PHONE_RUNTIME_TRANSITION.md)
- [RESEARCH_PAUSE_SOP.md](RESEARCH_PAUSE_SOP.md)

## Milestone 1: Document Current Runtime Responsibilities

Questions to answer:

- What does the phone lane do today?
- What does the host already expect from it?

Current status:

- Started
- First draft captured in [PHONE_RUNTIME_TRANSITION.md](PHONE_RUNTIME_TRANSITION.md)

Expected output:

- stable description of phone-side runtime behavior
- stable description of host-side assumptions

## Milestone 2: Define Runtime Replacement Boundary

Questions to answer:

- What can change without breaking host tooling?
- What API contract must stay stable?

Current status:

- Started
- First draft captured in [PHONE_RUNTIME_TRANSITION.md](PHONE_RUNTIME_TRANSITION.md)

Expected output:

- stable replacement boundary
- preserved host contract during runtime transition

## Milestone 3: Evaluate Native Runtime Path

Questions to answer:

- Is `llama.cpp` the right next runtime base?
- What is the tradeoff against staying longer with Termux/Debian/Ollama?
- Which similar projects should we adopt from, adapt from, reference, or reject?

Current status:

- Not complete
- This is the next serious step

Required rule:

- This milestone must follow [RESEARCH_PAUSE_SOP.md](RESEARCH_PAUSE_SOP.md)
- If the research result changes repo philosophy, architecture direction, support boundaries, or roadmap assumptions, pause and bring the finding back for explicit go/no-go before baking it in

Expected output:

- short runtime decision note
- external project classification
- native runtime recommendation

## Milestone 4: Keep Compatibility Modular

Questions to answer:

- Should the runtime surface stay Ollama-compatible, OpenAI-compatible, or both?
- How do we keep the runtime implementation swappable underneath that surface?

Current status:

- Framed
- Not fully specified yet

Expected output:

- stable runtime API contract
- compatibility strategy for future runtime swaps

## Plain Recommendation

Do not rethink the repo base again.

Start solving the phone runtime problem from this base.

Preserve:

- Windows control plane
- USB host contract
- diagnostics and validation flow
- compatibility and profile selection behavior

Transition:

- phone runtime packaging
- phone runtime lifecycle control
- phone runtime install friction

## Immediate Next Step

Run the native-runtime Research Pause and return with a decision note before large implementation work begins.
