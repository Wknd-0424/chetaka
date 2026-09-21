# Model pipeline and NPU runtime

How the on-device models are produced, quantised, loaded and benchmarked.

Like [HEURISTICS.md](HEURISTICS.md), this is a specification rather than committed
code. Application and build code is written during the 30-hour window. The commands
below are the ones we will run, recorded now so hour 20 is execution, not research.

---

## Models

| Role | Model | Precision | Size | Backend |
| --- | --- | --- | --- | --- |
| Speech-to-text, Tier 1 | Whisper small | int8 | ~180 MB | NPU, GPU or CPU |
| Speech-to-text, Tier 0 | Android `SpeechRecognizer` | — | — | System |
| Scam classifier, Tier 1 | Small transformer encoder | int8 | ~25 MB | NPU, GPU or CPU |
| Explanation, Tier 2 (stretch) | Gemma 3 1B | int4 | ~550 MB | MediaPipe LLM Inference |

All weights ship inside the APK. Nothing is downloaded at runtime, so the app works in
aeroplane mode and in weak-signal areas.

---

## Quantisation pipeline

### Whisper — via whisper.cpp

`whisper.cpp` ships its own GGML quantiser, which is why we prefer it over a TFLite
conversion for the ASR path.

```bash
# 1. fetch the base weights
bash ./models/download-ggml-model.sh small

# 2. build the quantiser
cmake -B build && cmake --build build --config Release -j

# 3. quantise to int8 (q8_0)
./build/bin/quantize \
    models/ggml-small.bin \
    models/ggml-small-q8_0.bin \
    q8_0
```

The `.bin` goes in `app/src/main/assets/models/`. Android must not compress it, or it
cannot be memory-mapped — see the `noCompress` rule in the Gradle section.

### Classifier — PyTorch to LiteRT

```bash
# 1. export to ONNX with a fixed sequence length
python -m tools.export_onnx \
    --checkpoint checkpoints/scam-clf.pt \
    --seq-len 128 \
    --out build/scam_clf.onnx

# 2. ONNX to TensorFlow SavedModel
onnx2tf -i build/scam_clf.onnx -o build/scam_clf_tf

# 3. SavedModel to int8 LiteRT, with a representative dataset
python tools/quantize_litert.py \
    --saved-model build/scam_clf_tf \
    --calib data/calibration.jsonl \
    --out app/src/main/assets/models/scam_clf_int8.tflite
```

Full-integer quantisation requires a representative dataset — roughly 200 tokenised
samples drawn from our own scam corpus, never from the evaluation set. The converter
config:

```python
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_gen
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8
```

`inference_input_type = int8` matters. Leaving it float forces a dequantise op at the
graph boundary, which the QNN delegate cannot absorb, and the whole subgraph falls back
to CPU.

---

## NPU runtime

### Gradle

```kotlin
android {
    // keep model files uncompressed so they can be memory-mapped from the APK
    androidResources { noCompress += listOf("tflite", "bin") }

    defaultConfig {
        // the loaner phone is arm64 only; QNN ships per-ABI .so files
        ndk { abiFilters += "arm64-v8a" }
    }
    packaging {
        jniLibs { useLegacyPackaging = false }
    }
}

dependencies {
    implementation("com.google.ai.edge.litert:litert:__")
    implementation("com.google.ai.edge.litert:litert-gpu:__")
    // QNN delegate + Qualcomm runtime .so files, vendored under app/libs
    implementation(files("libs/litert-qnn.aar"))
    // stretch: Gemma 3 1B
    implementation("com.google.mediapipe:tasks-genai:__")
}
```

Versions are pinned on the day against what the loaner phone's Qualcomm runtime
actually supports. Pinning them now would be a guess.

### Delegate selection, in order

```
try QNN delegate  (HTP / NPU backend, int8 graph)
    on failure -> try GPU delegate
        on failure -> CPU with XNNPACK, 4 threads
            on failure -> Tier 0 rules only
```

The chosen backend and the measured per-segment latency both appear in the debug HUD,
so the NPU claim is visible on screen rather than asserted on a slide. This is what we
mirror through iQOO Office Kit.

### Things that silently break NPU acceleration

Recorded because each one costs an hour to diagnose at 3 a.m.

- A float input or output tensor on an int8 graph. The delegate declines the subgraph.
- Dynamic shapes. Sequence length must be fixed at export time.
- An unsupported op mid-graph partitions the graph. Half runs on NPU, half on CPU, and
  the latency looks like pure CPU. Check the partition log, not just "delegate applied".
- Thermal throttling after sustained inference. Our segments are short and duty-cycled
  for exactly this reason.

---

## Audio segmentation

| Parameter | Value | Why |
| --- | --- | --- |
| Sample rate | 16 kHz mono | Whisper's native rate; no resampling cost |
| Segment length | 5 s | Short enough for a sub-3 s alert, long enough for context |
| Overlap | 1 s | Stops a trigger phrase being split across a boundary |
| Source | `MediaRecorder.AudioSource.VOICE_RECOGNITION` | Speakerphone room audio |

Latency budget per 5-second segment, which is what the alert target depends on:

```
segment capture     5000 ms   (unavoidable, runs continuously)
Whisper int8 NPU     TBD ms   <- measured on the loaner phone
classifier int8 NPU  TBD ms   <- measured on the loaner phone
rules + scoring        <5 ms
overlay draw          ~16 ms
```

The alert fires on the segment boundary, so end-to-end worst case is one segment plus
inference. Target is under 3 s from the trigger phrase being spoken. If measured
inference pushes past that, segment length drops to 3 s before anything else is
sacrificed.

---

## Benchmarks

**No numbers are filled in yet, and we will not invent them.** These tables are
populated on the loaner phone during the build window and committed with the results.

### Inference latency, per 5-second segment

| Model | Precision | Backend | Median ms | p95 ms |
| --- | --- | --- | --- | --- |
| Whisper small | int8 | QNN / NPU | TBD | TBD |
| Whisper small | int8 | GPU | TBD | TBD |
| Whisper small | int8 | CPU (4 threads) | TBD | TBD |
| Scam classifier | int8 | QNN / NPU | TBD | TBD |
| Scam classifier | int8 | CPU (4 threads) | TBD | TBD |

### Detection quality

Test set: 20 scripted scam calls, 20 normal calls, both languages. Methodology in
[HEURISTICS.md](HEURISTICS.md).

| Metric | Target | Tier 0 rules only | Full pipeline |
| --- | --- | --- | --- |
| Recall on scam calls | >= 0.80 | TBD | TBD |
| False-positive rate on normal calls | <= 10% | TBD | TBD |
| Median alert latency | < 3 s | TBD | TBD |
| Payment guard trigger rate | 100% of linked cases | TBD | TBD |

The "Tier 0 rules only" column exists deliberately. It shows what the app still achieves
if every model fails to load. The payment guard row should read 100% in both columns,
because it depends on no model at all.
