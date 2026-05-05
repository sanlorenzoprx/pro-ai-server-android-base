# DevStack Tracking Plan

Use this plan before sending paid traffic, affiliates, creator posts, or partner outreach to the DevStack launch page. The goal is simple: every link and event should identify the offer, message, channel, niche, and campaign that produced the lead or purchase.

This is an instrumentation plan, not a dependency on a specific analytics vendor. PostHog, a landing-page backend, or a lightweight server log can implement the same names later.

## Required URL Parameters

Every public launch link should include these parameters:

- `ref`: creator, affiliate, partner, or internal source slug.
- `partner_type`: `creator`, `affiliate`, `community`, `founder`, `customer`, or `internal`.
- `offer`: `trial_entry`, `starter_install`, or `pro_install`.
- `msg`: message tag from the approved message tags below.
- `channel`: `youtube`, `tiktok`, `x`, `linkedin`, `reddit`, `discord`, `email`, `direct`, or `sales_call`.
- `niche`: target buyer niche, such as `vibe_coder`, `indie_builder`, `student`, `consultant`, or `small_team`.
- `campaign`: launch campaign slug, such as `phase21_launch`, `creator_demo_001`, or `affiliate_pilot`.

Keep values lowercase, hyphen-free or underscore-delimited, and stable across links. Use `unknown` only when the source truly cannot be known.

## Offer Tags

Use these exact values for the `offer` URL parameter and event property:

- `trial_entry`: free trial or `$1` compatibility path.
- `starter_install`: `$49-$99` guided setup offer.
- `pro_install`: `$149-$199` hands-on install offer.

## Message Tags

Use these exact values for the `msg` URL parameter and event property:

- `private_coding_assistant`: turn an old Android phone into a private AI coding assistant.
- `no_monthly_model_bill`: no monthly AI model bill for supported local workflows.
- `usb_first_local`: local-first and USB-first setup.
- `cursor_vscode_continue`: works with Cursor or VS Code through Continue.
- `old_phone_reuse`: reuse an old Android phone for local AI.
- `low_ram_honest`: low-RAM devices use smaller models and may be slower.

Demo scripts, creator clips, and landing copy should use the same offer and message tags so winning proof assets can be connected to leads and purchases.

## Required Events

Every event should include the attribution properties from the launch URL when available:

- `ref`
- `partner_type`
- `offer`
- `msg`
- `channel`
- `niche`
- `campaign`

Also include:

- `page`: landing page slug or URL path.
- `session_id`: anonymous visit/session identifier.
- `timestamp`: event time in ISO 8601 format.

### `landing_page_viewed`

When: the DevStack landing page loads.

Required properties: all attribution properties, `page`, `session_id`, `timestamp`.

Use this to measure visitor volume by partner, channel, niche, offer, and message.

### `cta_clicked`

When: a visitor clicks a primary or secondary CTA.

Required properties: all attribution properties, `page`, `session_id`, `timestamp`, `cta_id`, `cta_label`, `cta_destination`.

Use this to compare trial, starter, pro install, demo request, and contact CTAs.

### `lead_captured`

When: an email, form, checkout lead, or sales-call lead is captured.

Required properties: all attribution properties, `page`, `session_id`, `timestamp`, `lead_type`, `lead_id`, `device_claimed`, `preferred_ide`.

Use this to measure real demand before scaling traffic.

### `trial_started`

When: a visitor starts the free trial or `$1` trial entry path.

Required properties: all attribution properties, `page`, `session_id`, `timestamp`, `trial_type`, `checkout_id` or `lead_id`.

Use this to measure compatibility-check demand.

### `install_started`

When: a customer starts starter or pro install setup.

Required properties: all attribution properties, `page`, `session_id`, `timestamp`, `install_type`, `device_profile`, `ide`, `operator`.

Use this to measure whether paid buyers reach setup.

### `install_completed`

When: setup reaches the agreed local smoke path.

Required properties: all attribution properties, `page`, `session_id`, `timestamp`, `install_type`, `device_profile`, `ide`, `model_profile`, `smoke_result`.

Use this to measure fulfillment quality and device-fit risk.

### `demo_requested`

When: a visitor requests a live demo, install call, or sales call.

Required properties: all attribution properties, `page`, `session_id`, `timestamp`, `demo_type`, `preferred_ide`, `device_claimed`, `calendar_source`.

Use this to measure high-intent demand by message and niche.

### `purchase_completed`

When: a paid trial, starter install, or pro install purchase completes.

Required properties: all attribution properties, `page`, `session_id`, `timestamp`, `purchase_id`, `price`, `currency`, `offer`, `payment_provider`.

Use this to measure revenue by ref, channel, campaign, offer, and message.

## Example Links

Trial entry:

```text
https://example.com/devstack?ref=founder&partner_type=internal&offer=trial_entry&msg=old_phone_reuse&channel=direct&niche=vibe_coder&campaign=phase21_launch
```

Starter install:

```text
https://example.com/devstack?ref=creator_demo_001&partner_type=creator&offer=starter_install&msg=no_monthly_model_bill&channel=youtube&niche=indie_builder&campaign=creator_pilot
```

Pro install:

```text
https://example.com/devstack?ref=partner_devtools&partner_type=affiliate&offer=pro_install&msg=private_coding_assistant&channel=email&niche=consultant&campaign=affiliate_pilot
```

## Measure Before Scaling

Do not scale affiliates, creator spend, or paid traffic until these are visible by `offer`, `msg`, `channel`, `niche`, and `campaign`:

- Landing page views.
- CTA click-through rate.
- Lead capture rate.
- Trial starts.
- Demo requests.
- Purchase conversion rate.
- Install start rate.
- Install completion rate.
- Refund or failed-install rate.
- Revenue by partner or creator.

Early launch decisions should be based on which message gets qualified leads and completed installs, not just views. A message that drives clicks but attracts unsupported low-RAM phones should be treated as risky until install completion proves otherwise.
