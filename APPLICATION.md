# Chetaka — iQOO Hackathon 2026, Hyderabad City Battle
## Application / Idea Submission

**Track:** FinTech & Commerce (fallback: Open Innovation)
**Device requirement:** Flagship iQOO with Snapdragon NPU — on-device inference is core, not optional.
**Positioning:** Not an app that runs on an iQOO. A shippable OriginOS safety layer that only a
Snapdragon-NPU flagship can run.

---

## One-liner

Chetaka is an on-device AI shield that listens to a live phone call and warns the user
mid-conversation — before they share an OTP or transfer money. No audio ever leaves the phone.

---

## The problem

Digital arrest and KYC scams are draining Indian households. Scammers impersonate police,
CBI or bank officials, manufacture panic, and extract OTPs or transfers within a single call.
The victim is usually an elderly parent at home alone, and the money is gone before any
family member finds out.

Every existing defence is too late or too shallow:

- Caller-ID apps (Truecaller and similar) tell you *who* is calling. They cannot tell you
  *what is being said*. A scammer calling from a clean number passes every check.
- Bank SMS warnings arrive after the transfer.
- Cyber-crime portals are for reporting a loss, not preventing one.
- Awareness campaigns fail at the exact moment they are needed, because the victim is in
  a state of engineered panic.

Nobody intervenes during the sixty seconds that actually decide the outcome.

---

## The solution

Chetaka runs on the phone during a speakerphone call and does four things:

1. Transcribes the call on-device, handling Telugu, Hindi and English code-switching.
2. Scores scam risk from the words spoken, the manipulation tactic, and the urgency pattern.
3. Alerts the user mid-call — full-screen red banner plus haptics — naming the scam type
   and the reason in plain language ("Police never ask for OTP. Hang up.").
4. Alerts the family — a trusted contact is notified on their own phone when risk is critical.

The intervention lands while the call is still live. That is the entire point.

---

## Why this needs the iQOO hardware

Chetaka is not an app that happens to run on an iQOO. It is a feature that a flagship
Snapdragon phone makes possible.

**Three-tier escalation architecture** — each tier wakes only when the previous one is
suspicious, so battery and thermals stay sane across a long call:

| Tier | Trigger | Workload | Hardware |
|------|---------|----------|----------|
| 0 | Always on | Offline STT + keyword scoring | CPU, negligible cost |
| 1 | Risk >= 20 | Whisper Tiny + LiteRT scam classifier | Hexagon NPU |
| 2 | Risk >= 45 | ~1B on-device LLM explains the manipulation tactic | NPU, short burst |

- **Hexagon NPU** — real-time inference without a server round trip. A cloud call would add
  latency the victim cannot afford, and would ship private conversations off the device.
- **12–16 GB LPDDR5X** — speech model and language model resident simultaneously.
- **Flagship vapour-chamber cooling** — sustained inference across a ten-minute call without
  throttling. This is the difference between a demo and a product.
- **50 MP cameras** — ML Kit reads scam SMS screenshots and validates UPI QR codes before payment.
- **Large battery** — always-on protection is credible rather than theoretical.

---

## Why this belongs to iQOO

iQOO's flagship silicon is sold on raw speed — frames, thermals, sustained load. Chetaka points
that same capability at something a benchmark cannot score: the moment an elderly parent is
being talked out of their savings.

**A feature, not an app.** Chetaka is built to ship inside OriginOS as a system-level safety
layer, alongside the phone dialler, the way Call Assistant and the AI suite already sit there.
Nothing about it requires a store download to be useful. It is one toggle in Settings.

**It sells the hardware.** Every competitor phone can run a caller-ID app. None of them can run
a speech model, a scam classifier and a language model concurrently on-device through a live
call without throttling. That is a Snapdragon-NPU flagship capability and a genuine reason to
choose an iQOO — an AI feature that protects money rather than retouching photos.

**Made for India, first.** Telugu-Hindi-English code-switching is how scam calls actually sound
in Hyderabad. A global vendor will build this for English last. iQOO's core Indian user base —
young buyers who hand their old flagship down to their parents — is exactly the population
being targeted by digital-arrest scams today.

**Zero cloud cost to operate.** On-device means no inference bill, no server fleet, and no data
liability for the OEM. The feature scales to every unit shipped at no marginal cost.

**Trust is the moat.** A phone brand that can credibly say "your calls never leave this device
and it still caught the scam" owns a claim no cloud assistant can make.

---

## Privacy position

Zero audio leaves the device. No server, no cloud API, no account. Transcripts are stored
encrypted locally and can be deleted by the user at any time. Privacy is not a feature bullet
here — it is the reason on-device AI is the only correct architecture for this problem.

---

## Demo plan (30-hour build, three loaner phones)

- Phone A — the parent, protected by Chetaka.
- Phone B — the scammer, running a scripted digital-arrest call.
- Phone C — the son, receiving the family alert live.

The jury watches the alert fire mid-call on Phone A and land on Phone C seconds later.

---

## Scope discipline

Built in the window, in priority order:

1. Live call detection, scoring, and the alert — the core, must work.
2. Camera: UPI QR validation and scam-screenshot reading.
3. Post-call report and family alert.
4. NPU classifier with a visible on-screen latency readout.
5. On-device LLM explanation — dropped without hesitation if it endangers the core.

Deliberately out of scope: voice-clone detection (not solvable reliably at phone-codec audio
quality in 30 hours), behavioural biometrics (unsupported on most hardware), and any cloud
component whatsoever.

---

## Honest evaluation

Accuracy will be reported from a real test set built during the event: 20 scripted scam calls
and 20 ordinary calls, with the false-alarm count stated plainly. No invented percentages.

---

## Stack

Kotlin · Jetpack Compose · Whisper (on-device) · LiteRT with the Qualcomm NPU delegate ·
ML Kit (text recognition, barcode scanning) · CameraX · Room · Foreground Service.
All open-source, attributed, and written during the event window.

---

## Team

<names> — <student / working professional>, <college or company>.
Roles: core Android and audio pipeline · on-device models and scam-pattern dataset ·
demo, pitch and Office Kit workflow.
