# Detection heuristics

This is the specification the rules engine is built from. It is deliberately written as
a spec and not as committed Kotlin: hackathon rules require all application code to be
written during the 30-hour window, and a git commit is a timestamp. The design is
settled here so the implementation is typing, not thinking.

Two independent detectors run in parallel. Either can raise an alert alone.

```
Detector A — content        Detector B — behaviour
speech on speakerphone      call state + foreground app
needs RECORD_AUDIO          needs no audio at all
can be fooled by a script   cannot be fooled by a script
```

---

## Detector B — the payment guard

The core innovation, and the simpler of the two. It reads two signals and no content.

### Trigger condition

A guard fires when **all** of these hold:

| # | Condition | Source |
| --- | --- | --- |
| 1 | A call was active within the last `LINK_WINDOW` (default 300 s) | `TelephonyManager` call state |
| 2 | That call was from a number not in contacts, **or** scored `risk >= 40` | `READ_CONTACTS`, risk engine |
| 3 | The call lasted at least `MIN_CALL_S` (default 120 s) | Call start/end timestamps |
| 4 | A package in the watch list is now in the foreground | `UsageStatsManager` |
| 5 | No guard has fired for this call already | Local state |

### Pseudo-service

```
on call state change:
    RINGING   -> record number, mark unknown if not in contacts
    OFFHOOK   -> start call timer, start Detector A if speakerphone on
    IDLE      -> stop timer, write CallEvent{number_known, duration_s, risk}
                 arm the guard for LINK_WINDOW seconds

while guard armed, poll every POLL_MS (default 800):
    events = UsageStatsManager.queryEvents(now - POLL_MS*2, now)
    foreground = last event of type MOVE_TO_FOREGROUND
    if foreground.packageName in WATCHED_PACKAGES:
        if call.duration_s >= MIN_CALL_S and (not call.number_known or call.risk >= 40):
            show PaymentPauseOverlay(countdown = 10s, skippable = true)
            if risk == CRITICAL and family_shield_enabled:
                send FamilyAlert
            disarm guard
```

Polling `UsageStatsManager` rather than binding an `AccessibilityService` is a
deliberate trade. We learn *which* app opened and nothing about what is inside it.
See [PERMISSIONS.md](PERMISSIONS.md).

### Watched packages

Seed list. Final list is assembled on the loaner phone, since only installed packages
matter.

| App | Package |
| --- | --- |
| Google Pay | `com.google.android.apps.nbu.paisa.user` |
| PhonePe | `com.phonepe.app` |
| Paytm | `net.one97.paytm` |
| BHIM | `in.org.npci.upiapp` |
| Amazon (Amazon Pay) | `in.amazon.mShop.android.shopping` |
| SBI YONO | `com.sbi.lotusintouch` |
| HDFC | `com.snapwork.hdfc` |
| ICICI iMobile | `com.csam.icici.bank.imobile` |
| Axis | `com.axis.mobile` |
| Kotak | `com.msf.kbank.mobile` |

**Tuning knobs**, all exposed in the debug HUD so they can be adjusted live during the
demo: `LINK_WINDOW`, `MIN_CALL_S`, `POLL_MS`, countdown duration.

### Skip logging

Every skip writes `{reason_code, risk_at_skip, call_duration_s, occurred_at}` locally.
Reasons offered: *I know this person*, *This is my own bank*, *Not a payment*, *Other*.
This is how we measure the false-positive rate honestly rather than guessing it.

---

## Detector A — content heuristics

Tier 0 runs these rules on the live transcript before any model is involved. They are
cheap, explainable, and they are what the risk engine falls back to when the NPU or the
models are unavailable.

### Scoring

Score starts at 0 and accumulates. Bands:

| Band | Score | Action |
| --- | --- | --- |
| Watch | 20–39 | Silent. Escalate to Tier 1 (Whisper + classifier). |
| Elevated | 40–59 | Arms the payment guard even for known contacts. |
| High | 60–79 | Full-screen alert with haptics. |
| Critical | 80–100 | Alert + payment guard + family alert. |

A category scores once, at its highest matching weight. Score is capped at 100. Every
alert names the categories that fired — this is what makes the score explainable.

### Trigger categories

| Category | Weight | Rationale |
| --- | --- | --- |
| Authority impersonation | 25 | No real agency cold-calls about arrests |
| Credential / OTP request | 30 | Single strongest signal; no legitimate caller asks |
| Arrest or legal threat | 25 | Core of the digital-arrest script |
| Urgency and deadlines | 15 | Manufactured time pressure |
| Isolation instruction | 20 | "Tell nobody" has no legitimate use |
| Payment instruction | 20 | Direct request to transfer |
| Verification pretext | 10 | Softens the target before the ask |

### Phrase list

Seed list. Matching is case-insensitive on the normalised transcript, with fuzzy
tolerance for ASR error. Native-script and romanised forms are both matched, because
code-mixed ASR output is inconsistent about which it emits.

**Authority impersonation**

| Language | Phrases |
| --- | --- |
| English | CBI, Enforcement Directorate, ED officer, Narcotics Bureau, NCB, cyber crime branch, TRAI, customs department, police station, sub-inspector |
| Hindi | सीबीआई, पुलिस थाना, साइबर क्राइम, कस्टम विभाग, अधिकारी बोल रहा हूँ |
| Telugu | సీబీఐ, పోలీస్ స్టేషన్, సైబర్ క్రైమ్, కస్టమ్స్ డిపార్ట్‌మెంట్, ఆఫీసర్ మాట్లాడుతున్నాను |
| Romanised | police station se bol raha hun, officer maatladutunnanu, cyber crime se |

**Arrest / legal threat**

| Language | Phrases |
| --- | --- |
| English | digital arrest, arrest warrant, non-bailable, your Aadhaar was used, money laundering case, FIR registered, asset seizure, court summons, custody |
| Hindi | डिजिटल अरेस्ट, गिरफ्तारी वारंट, मनी लॉन्ड्रिंग, एफआईआर दर्ज, जमानत नहीं |
| Telugu | డిజిటల్ అరెస్ట్, అరెస్ట్ వారెంట్, మనీ లాండరింగ్, ఎఫ్ఐఆర్ నమోదు |
| Romanised | digital arrest ho jayega, arrest warrant hai, case register ho gaya |

**Credential / OTP request**

| Language | Phrases |
| --- | --- |
| English | share the OTP, read the OTP, six digit code, CVV, UPI PIN, ATM PIN, net banking password, screen share, AnyDesk, TeamViewer, install this app |
| Hindi | ओटीपी बताइए, ओटीपी शेयर कीजिए, पिन बताइए, स्क्रीन शेयर करें |
| Telugu | ఓటీపీ చెప్పండి, పిన్ చెప్పండి, స్క్రీన్ షేర్ చేయండి |
| Romanised | OTP bataiye, OTP share kijiye, pin cheppandi, screen share cheyandi |

**Isolation instruction**

| Language | Phrases |
| --- | --- |
| English | do not tell anyone, do not disconnect, stay on the line, do not inform your family, keep this confidential, this is a sealed investigation |
| Hindi | किसी को मत बताइए, फोन मत काटिए, लाइन पर रहिए, परिवार को मत बताना |
| Telugu | ఎవరికీ చెప్పొద్దు, ఫోన్ కట్ చేయొద్దు, లైన్‌లో ఉండండి, ఇంట్లో చెప్పొద్దు |
| Romanised | kisi ko mat bataiye, phone mat katiye, evarikee cheppoddu |

**Urgency**

| Language | Phrases |
| --- | --- |
| English | within 30 minutes, immediately, right now, last warning, before the account is frozen, within the hour |
| Hindi | तुरंत, अभी के अभी, आखिरी चेतावनी, अकाउंट फ्रीज हो जाएगा |
| Telugu | వెంటనే, ఇప్పుడే, చివరి హెచ్చరిక, ఖాతా ఫ్రీజ్ అవుతుంది |
| Romanised | turant kijiye, abhi ke abhi, ventane cheyandi |

**Payment instruction**

| Language | Phrases |
| --- | --- |
| English | transfer the amount, verification deposit, RBI verification account, refundable security deposit, send it to this account, clear the amount |
| Hindi | पैसे ट्रांसफर कीजिए, वेरिफिकेशन के लिए जमा, रिफंड हो जाएगा |
| Telugu | డబ్బు ట్రాన్స్‌ఫర్ చేయండి, వెరిఫికేషన్ కోసం జమ చేయండి |
| Romanised | paise transfer kijiye, dabbu transfer cheyandi |

### Known limitations

Stated here because a judge will ask, and because they shape what we build first.

- **A phrase list is not a model.** It catches the script, not the intent. Tier 1 exists
  precisely because scammers vary wording; Detector B exists because Tier 1 will still
  sometimes miss.
- **ASR error degrades matching.** Telugu on-device recognition is the weakest link in
  the whole system. Fuzzy matching helps; it does not solve it.
- **Single phrases cause false positives.** A real bank employee may say "verification".
  This is why no single category reaches the alert threshold alone, and why the payment
  guard — which reads no content — is the layer we trust most.
