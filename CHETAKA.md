# Chetaka — Design Document
## "The One Who Warns"

On-device scam shield for the iQOO Hackathon 2026, Hyderabad City Battle (Sept 26-27).
The pitch lives in [APPLICATION.md](APPLICATION.md). This file is the build blueprint:
architecture, components, screens, risks, and the event-day plan.

> **Build rule:** all app code is written during the 30-hour event window. This repository holds
> design documents only until the event starts.

---

## 1. Core idea in one paragraph

Scams move along a path: an unknown call creates panic, then the victim opens a payment app and
sends money. Chetaka watches that path on the phone. During the call it listens (on speaker),
transcribes on-device, and fires an alert when scam language appears. After the call it
remembers what happened, and if a UPI or banking app opens soon after a suspicious or long
unknown call, it shows a pause screen before any money moves. A trusted family member can be
alerted at critical risk. Nothing leaves the device.

---

## 2. User flows

### Flow A — scam caught during the call (speaker on)

1. Unknown number calls. Call-state listener fires.
2. Chetaka shows a floating bubble: "Unknown caller. Tap speaker to let Chetaka listen."
3. User taps speaker. Listening service starts.
4. Transcript chunks are scored continuously. The risk meter rises.
5. Risk reaches the alert threshold. Full-screen red alert plus haptics, naming the scam type
   and the reason.
6. Call ends. Session saved with score, duration, and matched phrases.

### Flow B — scam caught after the call (speaker off)

1. Unknown number calls. The user never taps speaker, so no transcript exists.
2. Call ends. Chetaka records duration and unknown-number status.
3. Within 15 minutes, the user opens a UPI or banking app.
4. Chetaka shows a 30-second pause screen with the call summary and three actions: continue,
   call family, cancel.
5. If risk is critical, the family member is alerted.

### Flow C — family alert

1. Risk crosses the critical threshold, in either flow.
2. A notification is sent to the paired family phone with name, call duration, risk level, and
   the app just opened.
3. The family member can call back in one tap.

---

## 3. Risk model

Risk is a single score from 0 to 100, built from independent signals. Every signal is
explainable, so the alert can always say *why*.

| Signal | Source | Points |
|---|---|---|
| Caller not in contacts | Contacts lookup | +10 |
| Call longer than 5 minutes | Call timer | +10 |
| Call longer than 10 minutes | Call timer | +10 more |
| Scam phrase matched (per category, capped) | Transcript | up to +40 |
| Classifier scam probability | LiteRT model | up to +20 |
| Payment app opened within 15 min of call | Foreground-app check | +20 |

### Phrase categories (Telugu, Hindi, English)

| Category | Examples |
|---|---|
| Authority impersonation | police, CBI, customs, cyber cell, RBI officer |
| Threat | digital arrest, warrant, case filed, account blocked |
| Credential request | OTP, UPI PIN, CVV, password, share the code |
| Urgency | immediately, within 10 minutes, turant, abhi |
| Isolation | don't tell anyone, stay on the line, don't cut the call |
| Identity hook | Aadhaar, PAN, KYC update, parcel seized |

Credential request plus authority impersonation is treated as near-certain scam, because no real
institution asks for an OTP.

### Thresholds

| Score | Level | Action |
|---|---|---|
| 0-29 | Safe | Nothing shown |
| 30-59 | Watch | Small amber indicator on the bubble |
| 60-84 | High | Full-screen alert, haptics; payment guard armed |
| 85-100 | Critical | Alert, payment guard, family alert |

The payment guard also arms on any unknown call longer than 5 minutes, even at a low score,
because Flow B has no transcript to score.

---

## 4. Architecture

### Components

| Component | Responsibility |
|---|---|
| `CallMonitor` | Listens to call state; records caller number, start, end, duration. |
| `ContactChecker` | Answers "is this number saved?" |
| `ListeningService` | Foreground service; captures speaker audio during an active call. |
| `Transcriber` | Converts audio to text. `SpeechRecognizer` first, Whisper as the upgrade. |
| `PhraseMatcher` | Matches transcript against the multilingual phrase list. |
| `ScamClassifier` | LiteRT model on the NPU; returns scam probability for a sentence. |
| `RiskEngine` | Combines all signals into one score and a list of reasons. |
| `AppWatcher` | Detects when a UPI or banking app comes to the foreground. |
| `PaymentGuard` | Decides whether to show the pause screen. |
| `AlertOverlay` | Draws the in-call alert and the pause screen over other apps. |
| `FamilyNotifier` | Sends the critical alert to the paired phone. |
| `SessionStore` | Room database of past calls and their risk results. |
| `HardwareProfile` | Reads chip, RAM, and NPU availability at startup; chooses the tier. |

### Three-tier escalation

The heavy models only run when there is reason to.

| Tier | Wakes when | Runs | Hardware |
|---|---|---|---|
| 0 | Always | `CallMonitor`, `AppWatcher`, `PhraseMatcher` | CPU, near-zero cost |
| 1 | Score >= 20 | `Transcriber` (Whisper), `ScamClassifier` | Hexagon NPU |
| 2 | Score >= 60 | `AlertOverlay`, `PaymentGuard`, `FamilyNotifier` | — |

### Hardware fallback ladder

The loaner phone model is unknown (a flagship iQOO with a Snapdragon NPU). `HardwareProfile`
picks the best path that actually loads:

1. NPU delegate loads: full three tiers, latency shown on screen.
2. NPU delegate fails: classifier on GPU or CPU; Whisper on CPU.
3. Models fail to load: `SpeechRecognizer` plus `PhraseMatcher` only. Flows A, B and C still work.

The demo must never depend on the top rung.

---

## 5. Screens

| Screen | Content |
|---|---|
| Home | Protection status, today's calls checked, last alert, "Test with a sample call" button |
| Call bubble | Floating over the dialler: "Unknown caller — tap speaker"; amber when risk is watch-level |
| In-call alert | Full-screen red, scam type, one-line reason, "Hang up" and "Call family" buttons |
| Pause screen | Call summary, 30-second countdown, continue / call family / cancel |
| Call report | Duration, final score, matched phrases highlighted, advice |
| Family setup | Add one trusted contact and pair their phone |
| Settings | Protection toggles, language, sensitivity, watched payment apps, privacy statement |
| Hardware card | Detected chip, active tier, inference latency (proof of NPU use for the jury) |

Design principles: large text, high contrast, one action per screen, no jargon. The primary user
is 60 or older.

---

## 6. Tech stack

| Area | Choice |
|---|---|
| Language and UI | Kotlin, Jetpack Compose |
| Minimum Android | API 26 |
| Call state | `TelephonyManager` |
| Foreground app | `UsageStatsManager` |
| Overlays | `SYSTEM_ALERT_WINDOW` |
| Speech to text | `SpeechRecognizer` (offline), Whisper on-device as upgrade |
| Classifier | LiteRT with the Qualcomm NPU delegate |
| Storage | Room |
| Background | Foreground Service, Kotlin coroutines |
| Optional camera stretch | CameraX with ML Kit barcode scanning for UPI QR checks |

### Permissions

| Permission | Used for |
|---|---|
| `READ_PHONE_STATE`, `READ_CALL_LOG` | Call start, end, and caller number |
| `READ_CONTACTS` | Unknown-number check |
| `RECORD_AUDIO` | Listening on speaker |
| `PACKAGE_USAGE_STATS` | Detecting the payment app (granted in system settings) |
| `SYSTEM_ALERT_WINDOW` | Alert and pause screen overlays |
| `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_MICROPHONE` | Listening during a call |
| `POST_NOTIFICATIONS` | Alerts on Android 13 and later |
| `VIBRATE` | Haptics |
| `CAMERA` | Optional QR stretch goal |

Onboarding must walk the user through the two settings-screen permissions
(`PACKAGE_USAGE_STATS` and `SYSTEM_ALERT_WINDOW`), because they cannot be requested with a
normal dialog.

---

## 7. Privacy rules

- No audio is written to disk. Audio buffers are discarded after transcription.
- No network calls except the family alert.
- Stored per call: caller number hash, duration, final score, matched phrase categories.
- Transcripts are kept only in memory during the call, unless the user saves the report.
- The payment guard knows only which app opened. It never reads screen content or amounts.
- One button deletes all stored history.

---

## 8. Scoring against the judging rubric

| Criterion | Weight | How Chetaka earns it |
|---|---|---|
| End product quality | 30% | Flows A, B and C work reliably; fallback ladder prevents crashes |
| Novelty and impact | 20% | Payment-app guard after the call; Telugu-Hindi-English phrases |
| Creative phone use | 15% | Microphone, call state, on-device NPU inference, overlays, optional camera |
| Technical depth | 15% | Tiered escalation, hardware detection, explainable risk engine |
| Office Kit usage | 10% | Used throughout: mirroring for demos, file transfer for test audio, clipboard |
| Demo and presentation | 10% | Three-phone live story on the iQOO device |

---

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Speech recognition weak in a noisy hall | Flow B does not need audio; keep test calls short and scripted |
| NPU delegate fails on the loaner phone | Fallback ladder; the demo runs on rung 3 if needed |
| Overlay blocked by OriginOS battery or permission settings | Test permissions in the first hour on the loaner phone |
| `UsageStatsManager` reports the app late | Poll every second while the guard is armed |
| False alarm on a real bank call | Credential request required for High; pause screen always offers "continue" |
| Running out of time | Build order below puts the novel, model-free part first |
| Jury asks technical questions | Core logic written by the team, not generated; rehearse the eight standard questions |

---

## 10. Event-day build order (30 hours)

| Hours | Milestone | Done when |
|---|---|---|
| 0-1 | Setup on loaner phone | Empty app installs; first commit pushed to the linked repo |
| 1-5 | `CallMonitor`, `ContactChecker`, `SessionStore` | Unknown call logged with duration |
| 5-9 | `AppWatcher`, `PaymentGuard`, pause screen | Opening PhonePe after a long unknown call shows the pause screen |
| 9-14 | `ListeningService`, `Transcriber`, `PhraseMatcher`, `RiskEngine` | Live score rises during a scripted scam call |
| 14-17 | In-call alert overlay and haptics | Red alert fires mid-call |
| 17-20 | `FamilyNotifier` and family setup | Second phone receives the alert |
| 20-24 | `ScamClassifier` on NPU, hardware card | Latency shown on screen; skipped if blocked |
| 24-27 | Test set: 20 scam calls, 20 normal calls | Real results recorded |
| 27-30 | Polish, slides, demo rehearsal | Full demo runs three times in a row |

Commit and push at every milestone.

---

## 11. Demo script (3 minutes)

1. **Setup (20 s):** "Meet Amma, 67." Phone A shows Chetaka active. Phone C belongs to her son.
2. **Call with speaker (60 s):** Phone B calls as a police officer. Amma taps speaker. The
   officer mentions digital arrest, Aadhaar, and money laundering. The risk meter climbs. The red
   alert fires.
3. **Call without speaker (60 s):** Same scam, no speaker. The officer tells Amma to pay through
   PhonePe. She opens PhonePe. The pause screen blocks it.
4. **Family (20 s):** Phone C buzzes with the alert. Her son calls back.
5. **Proof (20 s):** Hardware card shows chip, tier, and NPU latency. Test results slide.

---

## 12. Jury questions to rehearse

1. Walk through what happens from the caller's voice to the alert.
2. Why on-device and not cloud?
3. What exactly runs on the NPU, and how do you know?
4. How does the risk score decide? What about false alarms?
5. How do you handle Telugu mixed with English?
6. How is this different from caller-ID apps and built-in scam alerts?
7. What happens if the microphone permission is denied or recognition fails?
8. What would you build next?

---

## 13. Future scope

- Ship as an OriginOS system feature, with dialler-level audio access instead of speakerphone.
- More Indian languages: Tamil, Kannada, Marathi, Bengali.
- Opt-in, anonymised scam-phrase updates.
- UPI QR tampering checks with the camera.
- Scam-awareness training mode for elderly users.

---

## Acknowledgments

Earlier scam-detection work in this hackathon series, including Kavach (Bengaluru), showed the
problem matters. Open-source components used at the event will be listed here with licences.
