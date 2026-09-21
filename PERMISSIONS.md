# Permissions and privacy

Every permission Chetaka requests is tied to exactly one feature. If you decline one,
that feature is disabled and the rest of the app keeps working. Nothing is requested
"for later".

## Declared permissions

| Permission | Feature it powers | What happens if denied |
| --- | --- | --- |
| `READ_PHONE_STATE` | Detects call start, end and duration | No call-linked detection; manual guard only |
| `READ_CONTACTS` | Checks whether the caller is a known contact | Every caller is treated as unknown |
| `RECORD_AUDIO` | Live transcription, speakerphone only | No transcript tier; payment guard still works |
| `FOREGROUND_SERVICE` + `FOREGROUND_SERVICE_MICROPHONE` | Keeps the listener alive during a call | Listening stops when the screen locks |
| `PACKAGE_USAGE_STATS` | Detects a payment app coming to the foreground | **Payment guard disabled** — this is the core feature |
| `SYSTEM_ALERT_WINDOW` | Draws the warning and pause overlays | Falls back to a full-screen notification |
| `POST_NOTIFICATIONS` | Alerts on Android 13+ | Silent operation, overlay only |
| `VIBRATE` | Haptic warning during a call | Visual alert only |
| `INTERNET` | **Family alert delivery only** (FCM) | Family alert disabled; all detection unaffected |

`PACKAGE_USAGE_STATS` and `SYSTEM_ALERT_WINDOW` are special-access permissions. They
cannot be granted from a runtime dialog, so onboarding deep-links the user to the
system screens with `ACTION_USAGE_ACCESS_SETTINGS` and
`ACTION_MANAGE_OVERLAY_PERMISSION`.

## What we do not request

| Not requested | Why it matters |
| --- | --- |
| `BIND_ACCESSIBILITY_SERVICE` | Rejected by design. It would grant us the entire screen contents of every app, and Google restricts its use for non-accessibility purposes. We use `UsageStatsManager`, which tells us *which* app is in the foreground and nothing about what is inside it. |
| `READ_SMS` / `RECEIVE_SMS` | We never read your messages. |
| `READ_CALL_LOG` | We only observe the call happening now, not your history. |
| `ACCESS_FINE_LOCATION` | Location is irrelevant to this problem. |
| `READ_EXTERNAL_STORAGE` | Models ship inside the APK. Nothing is scanned on your storage. |

## The network claim, stated precisely

> **The entire detection pipeline runs with no network access. `INTERNET` is declared
> solely so an opt-in family alert can be delivered.**

This is the honest version of "nothing leaves the phone", and it is the one we say on
stage. Specifically:

- Speech-to-text, the scam classifier, the risk engine and the payment guard run fully
  on-device. Turn on aeroplane mode and all of them still work.
- Model weights ship inside the APK. Nothing is downloaded at runtime.
- No call audio, no transcript and no risk detail is ever transmitted. The family alert
  carries a risk level, a timestamp and a call duration — the four fields below, and
  nothing else.
- With the Family Shield feature off, Chetaka makes zero network requests. This is
  verifiable in the demo by putting the phone in aeroplane mode and running the full
  detection flow.

### Everything the family alert transmits

| Field | Example | Notes |
| --- | --- | --- |
| `risk_level` | `CRITICAL` | Bucket only, never the raw score breakdown |
| `event_type` | `PAYMENT_GUARD_TRIGGERED` | One of a fixed enum |
| `call_duration_s` | `842` | Integer seconds |
| `occurred_at` | `2026-09-26T09:59:12+05:30` | ISO 8601 with offset |

No phone number, no contact name, no audio, no transcript, no location.

## Data at rest

- Local history is stored in Room, encrypted with SQLCipher.
- No raw audio is ever written to disk. Audio is processed in memory in short segments
  and discarded.
- Transcript segments are held only as long as the call, then dropped.
- One-tap delete clears all local history.

## Consent

- Family Shield is opt-in per contact. The protected user adds the contact, and can
  remove them at any time.
- The protected user sees exactly what a contact would receive before enabling it.
- Detection can be paused from the notification without uninstalling.
