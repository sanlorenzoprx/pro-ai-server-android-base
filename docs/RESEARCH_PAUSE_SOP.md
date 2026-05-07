# Research Pause SOP

This repository uses a Research Pause before major new directions, feature families, or subsystem changes.

The purpose is simple:

- spend engineering effort on novel product work
- avoid rebuilding commodity patterns blindly
- learn from similar projects before committing implementation time
- keep adaptation intentional, modular, and licensing-aware

This is not copying for its own sake. It is technical due diligence and pattern harvesting.

This repository treats research as part of the product philosophy. We are building a real product, but we are also building an adaptable platform and learning system. That means one of the core skills of the project is knowing when to adopt, adapt, or discard outside work with discipline.

## When To Trigger A Research Pause

Trigger this SOP before work such as:

- new runtime direction
- new transport mode
- new installer flow
- companion app work
- model catalog or model lifecycle redesign
- gateway/backend architecture changes
- onboarding UX flow changes
- any new subsystem that is bigger than a small isolated fix

If the change would likely become a new phase, ticket cluster, or architectural dependency, do the pause first.

## Required Outputs

Create a short research note that answers:

1. What are we trying to build?
2. Which similar projects already exist?
3. What can we adopt directly?
4. What patterns can we adapt?
5. What should we avoid?
6. What is actually novel in our approach?
7. What is the final decision: build, adapt, integrate, or defer?

## Project Classification

Each external project reviewed during the pause should be tagged as one of:

- `adopt`
- `adapt`
- `reference`
- `reject`

These tags keep later planning concrete.

## Decision Rule

Do not write major implementation tickets until the Research Pause is complete for that direction.

The pause should happen before:

- phase plans
- major build tickets
- runtime shifts
- new platform modules
- large onboarding or install changes

## Working Principles

- Do not rebuild commodity patterns unless there is a product reason.
- Do build the parts that are genuinely differentiating.
- Keep borrowed ideas behind clean interfaces where possible.
- Prefer adapting proven patterns over inventing weak new ones.
- Preserve modular boundaries so external influence does not trap the architecture.

## Repository Application

For this repository, Research Pause results should shape:

- runtime transition planning
- companion app planning
- transport expansion
- gateway/API surface decisions
- model catalog design
- installer/onboarding work

Use the Research Pause to spend time where this product is novel:

- Windows-managed Android host control
- private local-first setup flow
- adaptive Android device compatibility
- swappable phone runtime under a stable host contract
