# Chetaka — the scam shield that follows the call into the payment app

**Event:** iQOO Hackathon 2026 — Hyderabad City Battle
**Track:** FinTech & Commerce
**Positioning:** An OriginOS safety layer that only a Snapdragon-NPU flagship can run.

---

## One line

Chetaka is the only protection that follows a scam from the phone call into the payment app.
It warns during the call, and it steps in before the money moves. Nothing leaves the phone.

---

## The problem

Digital arrest and KYC scammers impersonate police and bank officials, create panic, and push
the victim to pay within minutes. Every existing defence fails in one of two ways:

- **It looks at the wrong thing.** Caller-ID apps judge *who* is calling. A scammer on a clean
  number passes every check.
- **It looks at the wrong moment.** Scam-call warnings stop when the call ends. Bank alerts
  arrive after the transfer. But the money moves in the payment app, minutes after the call,
  and nobody guards that gap.

A scam is not a call and not a payment. It is the path from one to the other. Nobody protects
the path.

---

## The solution: two layers of protection

### Layer 1 — during the call

- An unknown number calls. Chetaka shows a small bubble: *"Unknown caller. Tap speaker to let
  Chetaka listen."*
- On speaker, Chetaka transcribes on-device across Telugu, Hindi and English, and scores
  urgency, impersonation, and OTP or payment requests.
- At high risk, a full-screen red alert and haptics fire mid-call:
  *"Police never ask for OTP. Hang up."*

### Layer 2 — after the call

- The call ends. Chetaka remembers who called, for how long, and what risk it saw.
- If the user opens a UPI or banking app within 15 minutes, Chetaka steps in with a 30-second
  pause screen: *"You just spoke to an unknown caller for 12 minutes. Are they asking you to
  pay? Real police and banks never do."*
- The user can continue, call a trusted family member in one tap, or cancel.
- This layer works even if the user never turned on speaker. Call length and unknown-number
  status are enough to trigger it.

### Family Shield

At critical risk, a trusted family member is alerted on their own phone:
*"Amma spoke to an unknown caller for 14 min and just opened PhonePe."*

---

## Why this is new

| | Caller-ID apps | Built-in scam call alerts | Kavach | **Chetaka** |
|---|---|---|---|---|
| Judges who is calling | Yes | Yes | — | Yes |
| Understands what is said | No | Yes | Yes | Yes |
| Telugu-Hindi-English mix | No | No | No | Yes |
| **Guards the payment app after the call** | No | No | No | **Yes** |
| **Works without speakerphone** | Yes | Yes | No | **Yes** |
| Live family alert | No | No | No | Yes |

---

## How it works (all on-device)

| Signal | Android capability |
|---|---|
| Call starts and ends, caller number | `TelephonyManager` call state |
| Unknown number check | Contacts lookup |
| Live transcription | Offline `SpeechRecognizer`, upgraded to Whisper on-device |
| Scam scoring | Keyword rules, then a LiteRT classifier on the Hexagon NPU |
| UPI or banking app opened | `UsageStatsManager` foreground-app check |
| Alert and pause screen | Overlay window and haptics |
| Family alert | Notification to a paired phone |

### Three-tier escalation keeps the phone cool

| Tier | Wakes at | Work | Hardware |
|---|---|---|---|
| 0 | Always | Call state, app watch, keyword scoring | CPU, near-zero cost |
| 1 | Risk >= 20 | Whisper and scam classifier | Hexagon NPU |
| 2 | Risk >= 60 | Alert, payment guard, family alert | — |

The app detects the phone's chip and memory at runtime and picks the highest tier the hardware
supports, so it runs on any flagship iQOO the organizers hand out.

---

## Why this is iQOO's feature

- **Flagship silicon pointed at safety.** iQOO phones are built for sustained speed. Chetaka
  points that speed at the minutes when a parent's savings are at risk.
- **A system feature, not an app.** It belongs in OriginOS beside the dialler — one toggle in
  Settings, watching the path from call to payment the way only the OS can.
- **It sells the hardware.** Live multilingual speech AI plus an NPU classifier, sustained
  through a long call without throttling, is a flagship Snapdragon capability.
- **Made for India.** UPI is how India pays, and Telugu-Hindi-English is how scam calls sound in
  Hyderabad. iQOO's young buyers hand their old flagships to their parents — the exact people
  being targeted.
- **Zero cloud cost.** No servers, no inference bill, no data liability. It scales to every unit
  shipped.
- **Trust.** "Your call never left this phone, and it still stopped the payment" is a claim no
  cloud product can make.

---

## Privacy

No audio leaves the device. No server, no account. Chetaka stores only call length, risk score
and the phrases it caught, encrypted locally and deletable at any time. It never reads payment
amounts or banking screens — it only knows which app was opened.

---

## Demo (three loaner phones, 3 minutes)

1. Phone A — Amma, 67, protected by Chetaka. Phone B — the "police officer". Phone C — her son.
2. B calls A. The bubble appears; Amma taps speaker. The officer says *digital arrest*,
   *Aadhaar*, *money laundering*. The risk score climbs live on screen.
3. The red alert fires mid-call.
4. Replay the call without speaker. No live alert — the scammer tells Amma to pay via PhonePe.
5. Amma opens PhonePe. Chetaka's pause screen blocks it.
6. Phone C buzzes: *"Amma spoke to an unknown caller for 4 min and just opened PhonePe."*

Step 5 is the moment nobody else can show.

---

## Scope for 30 hours

1. Call detection, unknown-number check, payment-app guard — the core, must work.
2. Live transcription, keyword scoring, mid-call alert.
3. Family alert.
4. NPU classifier with an on-screen latency readout — stretch goal.
5. UPI QR check with the camera — stretch goal.

Deliberately out of scope: voice-clone detection, behavioural biometrics, on-device LLM, and
anything cloud.

---

## Honest evaluation

Tested at the event on 20 scripted scam calls and 20 ordinary calls, including realistic bank
calls. The report states scams caught, false alarms, and payment-guard triggers. No invented
percentages.

---

## Stack

Kotlin · Jetpack Compose · `TelephonyManager` · `UsageStatsManager` · `SpeechRecognizer` and
Whisper on-device · LiteRT with the Qualcomm NPU delegate · Room · Foreground Service.
Open-source, attributed, and written during the event window.

---

## Team

<names> — students, <college>.
Roles: core Android and call pipeline · on-device models and scam-phrase dataset ·
demo, pitch and Office Kit workflow.
