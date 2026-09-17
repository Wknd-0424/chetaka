# CHETAKA: Real-Time AI Scam Detection Shield
## "The Alert One" / "One Who Warns"

---

## ONE-LINE PITCH
On-device AI guardian. Listens to phone calls real-time, detects scam patterns mid-call via multi-signal fusion (audio + urgency + voice cloning + behavioral biometrics), warns via multi-modal alerts (haptic + visual + audio whisper + LED) BEFORE user shares OTP or money. Zero audio to cloud.

---

## INSPIRATION
Builds on Kavach (iQOO Hackathon 2026 Bengaluru, 2nd Runner-Up, Student Track) — proved scam detection wins. Kavach: Audio → Whisper Tiny (STT) → Text Pattern Matching → Risk Scoring → Visual/Haptic Alerts.

Chetaka: single-signal (text patterns) to multi-signal fusion (audio + urgency + voice cloning + behavioral). 12 new features incl. Family Shield, AI voice cloning detection, offline-first.

---

## THE PROBLEM
- India lost ₹1,200+ crore to UPI scams in 2025
- 68% of Indians get scam calls weekly
- AI voice cloning scams up 700% in 2025 (Bank of England warning)
- Elderly, rural users most vulnerable (61% medication non-adherence, targeted by scammers)
- Existing solutions reactive (report after fraud), not preventive
- 315M Indians with hypertension + 101M with diabetes (ICMR-INDIAB) primary targets

---

## THE SOLUTION
Listen to calls (speakerphone), transcribe real-time on-device (Whisper Tiny + Phi-3 Mini + Custom CNN), detect scams via multi-signal fusion (audio patterns + urgency + voice cloning + behavioral biometrics), alert DURING call before user shares sensitive info.

---

## COMPLETE SYSTEM ARCHITECTURE

### HIGH-LEVEL ARCHITECTURE

```text
ANDROID APP (On-Device, Privacy-First)

MULTI-MODAL INPUT LAYER
  Microphone (live audio) | Camera (QR scanning) | Touch/Keyboard (behavioral)
        |
        v
ON-DEVICE AI ENGINE
  Whisper Tiny (STT)
    - Real-time transcription (Hindi + English)
    - ~40MB model, runs on Snapdragon NPU
  Phi-3 Mini 3.8B (Urgency/Context)
    - Analyzes transcription for urgency tactics
    - Detects pressure: "within 5 minutes", "immediately"
    - ~2GB Q4 quantized, on-device inference
  Custom CNN (Voice Cloning Detection)
    - Spectral analysis for synthetic voice artifacts
    - Breathing pattern detection
    - Frequency spectrum anomaly detection
  Custom Audio Classifier (Keyword Spotting)
    - 20+ scam phrases (Hindi + English)
    - Real-time detection (<100ms latency)
        |
        v
MULTI-SIGNAL FUSION LAYER
  Risk Score Aggregator:
    - Audio patterns (0-40 points)
    - Urgency detection (0-30 points)
    - Voice cloning score (0-20 points)
    - Behavioral biometrics (0-10 points)
    = Total Risk Score (0-100)
        |
        v
MULTI-MODAL ALERT SYSTEM
  Haptic: short vibration = low risk (30-50), long vibration = high risk (70-100)
  Visual Overlay: red banner "UPI SCAM DETECTED" + scam type + confidence score
  Audio Whisper: quiet voice "Warning: This call shows scam patterns"
  LED Indicator: red LED blinks during suspicious call
  Smartwatch: vibrates wrist discreetly

FAMILY SHIELD MODULE
  Trusted contacts: add/remove family members (son, daughter, spouse)
  Real-time alerts: if Risk Score > 80, SMS to trusted contacts
    "Dad received potential scam call from +91-XXXXX"
  Emergency button: one-tap call to trusted contact
  Weekly report: "This week: 3 suspicious calls, 0 OTP shared"

TRAINING MODULE
  Scenarios: UPI Fraud, KYC Scam, Digital Arrest, Lottery Scam
  AI-generated scripts: realistic scam call simulations
  Feedback: "Good! You didn't share OTP. Here's what to do..."
  Progress: scam recognition score (0-100), badges "Scam Spotter", "Fraud Fighter"

LOCAL STORAGE (Encrypted, Offline-First) - Room Database
  - Call logs + transcripts (AES-256 encrypted)
  - Scam pattern database (pre-downloaded, weekly update)
  - Trusted contacts (Family Shield)
  - Training progress + badges
  - User settings + preferences

COMMUNITY SYNC (Optional, User Consent)
  When online:
    - Download latest scam patterns (weekly)
    - Upload anonymized reports (no audio, only metadata)
    - Community scam radar (geographic heatmap)
  Privacy guarantees:
    - No call recordings uploaded
    - No phone numbers shared (anonymized hashes)
    - Opt-in only

PRIVACY-FIRST DESIGN
  - Zero audio leaves device
  - All processing on-phone (Snapdragon NPU)
  - Encrypted local storage (AES-256)
  - Community reports anonymized (no PII)
```

---

### DETAILED DATA PIPELINE

#### Pipeline 1: Real-Time Audio Scam Detection

```text
Phone Call (Speakerphone)
  -> Android Microphone API (AudioRecord / MediaRecorder)
  -> Raw Audio Stream (PCM, 16kHz, mono)

ON-DEVICE AI PIPELINE
  1. Whisper Tiny (Speech-to-Text)
     - Input: raw audio stream; Output: real-time transcription
     - Latency: ~200ms per sentence; Model size: ~40MB; Runs on: Snapdragon NPU
  2. Custom Audio Classifier (Keyword Spotting)
     - Input: raw audio stream; Patterns: 20+ scam phrases (Hindi + English)
     - Output: match confidence (0-1); Latency: <100ms
  3. Phi-3 Mini 3.8B (Urgency/Context Analysis)
     - Input: transcription; Analyzes: urgency tactics, pressure language
     - Output: urgency score (0-1); Latency: ~500ms; Model size: ~2GB (Q4)
  4. Custom CNN (Voice Cloning Detection)
     - Input: spectrogram; Analyzes: spectral artifacts, breathing patterns
     - Output: synthetic voice probability (0-1); Latency: ~300ms

MULTI-SIGNAL FUSION LAYER
  - Audio patterns (keyword matches): 0-40 points
  - Urgency detection (Phi-3): 0-30 points
  - Voice cloning score (CNN): 0-20 points
  - Behavioral biometrics (typing/touch): 0-10 points
  Total: 0-100
  Thresholds: 0-30 Safe (green) | 31-50 Low (yellow) | 51-70 Medium (orange) | 71-100 High/SCAM (red)

MULTI-MODAL ALERT SYSTEM (if Risk Score > 70)
  1. Haptic: long vibration (500ms pulse), repeats every 10 seconds
  2. Visual overlay: "UPI SCAM DETECTED", "Caller requesting OTP", "87% likelihood"; does not interrupt call
  3. Audio whisper: TTS "Warning: This call shows scam patterns. Do not share OTP or bank details." at 30% volume
  4. LED: red blink (1 Hz)
  5. Smartwatch: vibrate wrist, show scam type

Post-Call: save to encrypted local DB
  - Call duration, risk score, transcript (AES-256)
  - Scam type classification
  - Reviewable in History tab
```

#### Pipeline 2: UPI QR Code Scanner

```text
Camera Preview (CameraX)
  -> QR Code Detection (ML Kit / ZXing)
  -> QR Payload Extraction (URL, UPI ID, amount)

QR VALIDATION PIPELINE
  1. URL parsing: extract UPI ID (e.g., merchant@upi), amount, transaction note
  2. Beneficiary verification: cross-check with UPI app API (if available); flag name mismatches
  3. Payment direction detection: detect PAYING vs RECEIVING; flag "receive money" scams
  4. Tampering detection: computer vision for sticker overlays; compare printed QR vs scanned payload
  5. Transaction history: check local DB; flag first-time or large amounts; community reports (opt-in)

  -> Risk Score (0-100)
  -> If > 70: "SUSPICIOUS QR CODE" / "Beneficiary name mismatch detected" / "Do not proceed with payment"
```

#### Pipeline 3: Family Shield Mode

```text
Scam Detected (Risk Score > 80)

FAMILY SHIELD WORKFLOW
  1. Check settings: Family Shield enabled? trusted contacts list
  2. Generate alert: "Dad received potential scam call from +91-XXXXX-XXXXX at 2:34 PM",
     "Risk Score: 87/100", "Scam Type: UPI Fraud - Caller requesting OTP",
     "Action Taken: Alerted user via haptic + visual"
  3. Send SMS to trusted contacts (Android SMS API, requires permission; parallel; optional callback link)
  4. Log to family dashboard (encrypted local DB; optional cloud sync with consent; web dashboard)
  5. Weekly report: aggregate past week, "3 suspicious calls, 0 OTP shared", send via SMS/email
```

---

## 12 KEY INNOVATIONS (BEYOND KAVACH)

### 1. Real-Time Audio Scam Detection
- Live on-device transcription (Whisper Tiny)
- Keyword spotting, 20+ scam phrases (Hindi + English)
- Urgency detection via Phi-3 Mini
- Haptic alerts mid-call, no interruption
- Overlay: "UPI SCAM DETECTED: Caller requesting OTP. Do not share."

### 2. AI Voice Cloning Detector
- Spectral analysis for synthetic artifacts
- Breathing pattern detection (AI voices lack natural breathing)
- Frequency spectrum anomaly detection
- Live score: "87% likelihood: SYNTHETIC VOICE"
- Demo: play cloned voice, app flags fake

### 3. Smart Contact Verification
- Cross-check official databases (RBI bank numbers, government helplines)
- Crowdsourced anonymized scam number DB
- Number reputation score (0-100 from reports)
- Offline cache for low connectivity

### 4. Behavioral Biometrics (Stress Detection)
- Typing pattern (rushed = high stress)
- Touch pressure (stress raises pressure)
- App switching (rapid call ↔ UPI app = red flag)
- Intervention: "HIGH STRESS DETECTED. Take a deep breath. Is this urgent?"

### 5. Family Shield Mode
- Scam detected: SMS to son/daughter
- Remote dashboard: children see parent's scam exposure stats
- One-tap emergency call
- Weekly report: "Mom encountered 3 suspicious calls this week"
- Privacy: only alerts shared, no recordings

### 6. Scam Simulation Training
- Scenarios: UPI fraud, KYC scam, digital arrest, lottery scam
- AI-generated realistic scam scripts
- Live feedback: "Good! You didn't share OTP. Here's what to do next..."
- Recognition score tracked over time
- Badges: "Scam Spotter", "Fraud Fighter", "Digital Guardian"

### 7. Multi-Modal Alert System
- Haptic: short = low risk, long = high risk
- Red overlay banner with scam type
- Audio whisper: "Warning: This call shows scam patterns"
- LED blinks red
- Smartwatch wrist vibration

### 8. UPI QR Code Scanner (Kavach Feature + Upgrade)
- QR validation before payment
- Beneficiary name check vs UPI app preview
- Pay vs receive detection
- Sticker overlay tampering detection
- Unusual transaction pattern flags

### 9. Offline-First Architecture
- Core fully offline (audio analysis, pattern detection, alerts)
- Local scam pattern DB, weekly update
- Offline QR validation (local hash matching)
- Sync when online (upload reports, download patterns)
- Works in rural low-connectivity areas

### 10. Post-Call Analysis & Reporting
- Transcript with scam keywords in red
- Risk timeline graph across call
- Recommendations: "Next time: Ask for official callback number, verify with bank"
- One-tap report (Chakshu portal, cyber crime, bank)
- PDF export for police complaint/FIR

### 11. Community Scam Radar
- Anonymous crowdsourced pattern reports
- Pattern updates pushed to all devices
- Geographic scam heatmap
- Trending alerts: "UPI KYC scam up 300% in Hyderabad this week"
- Privacy: no recordings, only pattern metadata

### 12. Multi-Language Support
- Hindi + English code-switching (common in Indian scam calls)
- Regional: Telugu, Tamil, Kannada, Marathi (future scope)
- Transcription in preferred language
- Region-specific scam patterns

---

## TECH STACK

### On-Device AI Models
- **Whisper Tiny** (OpenAI): STT, ~40MB, Snapdragon NPU
- **Phi-3 Mini 3.8B** (Microsoft): urgency/context, ~2GB Q4
- **Custom CNN**: voice cloning detection (spectral)
- **Custom Audio Classifier**: scam keyword spotting (TensorFlow Lite)

### Android Development
- **Language**: Kotlin
- **UI Framework**: Jetpack Compose
- **Audio**: Android MediaRecorder API, AudioRecord
- **Database**: Room (logs, patterns, contacts)
- **Background Processing**: WorkManager (pattern updates, sync)
- **Notifications**: Android NotificationManager (haptic + visual)
- **Camera**: CameraX (QR scanning)
- **Encryption**: Android Keystore (AES-256 transcripts)

### Infrastructure
- **On-Device Inference**: MLC Chat / llama.cpp (Whisper + Phi-3)
- **Offline Database**: pre-downloaded scam patterns (SQLite)
- **Community Updates**: encrypted opt-in sync
- **Privacy**: zero audio leaves device

---

## UI/UX DESIGN (CLEAN, MINIMAL, ACCESSIBLE)

### Home Screen
- Big status: "Chetaka Active" (green shield)
- Stats: "Today: 0 scam calls detected"
- Big "Test Mode" button (demo, plays recorded scam calls)
- Bottom nav: Home | History | Training | Settings

### During Call Screen (Overlay)
- Top banner: "SCAM DETECTED" (red)
- Type: "UPI Fraud - Caller requesting OTP"
- Confidence: "87% likelihood"
- "Emergency Contact" button (one-tap call)
- Discreet: no call interruption, scammer unaware

### Post-Call Report
- Duration: "3:42"
- Risk: "87/100" (red)
- Type: "UPI Fraud"
- Transcript, scam keywords in red
- Recommendation: "You did well! You didn't share OTP. Next time, ask for official number."
- Buttons: "Report to Cyber Crime" | "Export PDF"

### Family Shield Dashboard
- Trusted contact list (add/remove)
- Recent: "Dad received potential scam call from +91-XXXXX (2 hours ago)"
- Weekly: "This week: 3 suspicious calls, 0 OTP shared"
- "Call Dad Now" button

### Training Mode
- Scenarios: "UPI Fraud" | "KYC Scam" | "Digital Arrest" | "Lottery Scam"
- AI generates scam call script
- User answers: multiple choice or voice
- Feedback: "Excellent! You recognized the scam pattern."
- Progress: "Level 3: Scam Spotter (75/100)"

### Settings
- Feature toggles: real-time detection, voice cloning detector, Family Shield, etc.
- Language: Hindi / English / Regional
- Sensitivity: Low / Medium / High (detection threshold)
- Privacy: "No audio leaves device" badge
- About: "Inspired by Kavach (iQOO Bengaluru 2nd Runner-Up)"

---

## WHY CHETAKA WINS

### 1. Builds on Proven Winner
- Kavach won 2nd Runner-Up (validated problem)
- Judges already rated scam detection "important"
- Iterating on success, not guessing

### 2. Meaningful Differentiation
- Kavach post-call text; Chetaka real-time audio
- Kavach visual alerts; Chetaka haptic + visual + audio
- Kavach basic patterns; Chetaka 12 new features (voice cloning, Family Shield, etc.)

### 3. Technical Depth
- Multi-model pipeline (Whisper + Phi-3 + CNN)
- Behavioral biometrics (novel)
- Offline-first (hard, impressive)

### 4. Demo Wow Factor
- Live test call, phone vibrates mid-call
- Voice cloning demo (synthetic vs real)
- Family Shield demo (parent + child phones)
- Judges feel urgency, see live protection

### 5. Real-World Impact
- Protects elderly parents (emotional story)
- Works offline (rural India)
- Community-powered (network effect)
- Educational (training prevents future scams)

---

## COMPETITION ADVANTAGE

| Feature | Kavach (Bengaluru) | Chetaka (You) |
|---------|-------------------|---------------|
| Detection timing | Post-call | **Real-time during call** |
| Input method | Text + QR | **Live audio + QR** |
| Alert method | Visual | **Haptic + visual + audio** |
| AI models | Text patterns | **Whisper + Phi-3 + CNN** |
| Voice cloning detection | No | YES |
| Family Shield | No | YES |
| Behavioral biometrics | No | YES |
| Training mode | No | YES |
| Community radar | No | YES |
| Multi-language | English only | **Hindi + English** |

---

## TARGET OUTCOME
- **Win Hyderabad City Battle** (Student Track)
- **Advance to Grand Finale** (Top 6 from Hyderabad)
- **Compete for ₹40 Lakh national prize pool**
- **Real-world deployment**: partner with banks, telecom providers, cyber crime cells

---

## ACKNOWLEDGMENTS
- **Inspiration**: Kavach (Team Smoke Test, iQOO Bengaluru 2nd Runner-Up)
- **Models**: Whisper Tiny (OpenAI), Phi-3 Mini (Microsoft)
- **Datasets**: public scam call transcripts, community reports
- **Guidance**: iQOO Hackathon mentors, Reskilll team

---

## BUILD PLAN (30-HOUR HACKATHON)

### Hours 1-6: Core MVP
- [ ] Android app setup (Kotlin, Jetpack Compose)
- [ ] Mic capture (speakerphone)
- [ ] Whisper Tiny STT integration
- [ ] Basic keyword spotting (10 scam phrases)

### Hours 7-12: AI Integration
- [ ] Phi-3 Mini urgency detection
- [ ] Train audio classifier (scam patterns)
- [ ] Haptic alerts
- [ ] In-call visual overlay

### Hours 13-18: Advanced Features
- [ ] QR scanner + validation
- [ ] Contact verification (local DB)
- [ ] Post-call report
- [ ] Family Shield (basic SMS alerts)

### Hours 19-24: Polish
- [ ] UI/UX refinement
- [ ] Hindi + English support
- [ ] Offline mode testing
- [ ] Training mode (1-2 scenarios)

### Hours 25-28: Demo Prep
- [ ] Record test scam calls (actor, 3-5 scenarios)
- [ ] Live demo script
- [ ] Pitch deck (8-10 slides)
- [ ] Rehearse demo (timing, flow)

### Hours 29-30: Final Testing
- [ ] Stress test (edge cases, low battery, poor network)
- [ ] Bug fixes
- [ ] Submit to hackathon portal
- [ ] Rest before judging
