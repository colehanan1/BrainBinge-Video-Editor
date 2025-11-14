# Video Transitions - Usage Guide

> Professional xfade transitions between avatar and B-roll segments

## ✅ Implementation Status

**Phase 2 (Full xfade Transitions)** has been implemented!

- ✅ TransitionEngine module created (`src/modules/transitions.py`)
- ✅ Segment generation from B-roll plan
- ✅ Dynamic xfade filter chain building
- ✅ Audio crossfading support
- ✅ Configurable transition patterns
- ⏳ CLI integration (experimental)
- ⏳ Full testing and optimization

---

## 🎬 Available Transition Types

The system cycles through this pattern for varied, professional transitions:

1. **slideright** - Avatar → B-roll (dynamic slide)
2. **fade** - B-roll → Avatar (smooth fade)
3. **dissolve** - Avatar → B-roll (smooth blend)
4. **circleopen** - B-roll → Avatar (dramatic circle)
5. **slideright** - Avatar → B-roll (dynamic slide)
6. **zoomin** - B-roll → Avatar (dramatic zoom)

Pattern repeats for additional segments.

---

## 📋 How It Works

### Segment Generation

The system automatically splits your video into segments based on the B-roll plan:

```
Segment 0: Avatar (0s - 3s) → [slideright transition]
Segment 1: B-roll 1 (3s - 6.5s) → [fade transition]
Segment 2: Avatar (6.5s - 8s) → [dissolve transition]
Segment 3: B-roll 2 (8s - 11s) → [circleopen transition]
...and so on
```

### Transition Timing

- **Duration**: 0.5s (configurable)
- **Overlap**: Transitions happen AT the boundary (not before/after)
- **Audio**: Crossfaded during transitions for smooth sound

---

## 🚀 Usage (Experimental)

### Option 1: Direct Python Usage

```python
from pathlib import Path
from src.modules.transitions import TransitionEngine
from src.config import Config

# Load config
config = Config.from_yaml('config/brand_example.yaml')

# Create transition engine
engine = TransitionEngine(config)

# Define B-roll clips
broll_clips = [
    {
        'path': 'data/temp/broll_cache/clip1.mp4',
        'start_time': 3.0,
        'end_time': 6.5,
    },
    {
        'path': 'data/temp/broll_cache/clip2.mp4',
        'start_time': 8.0,
        'end_time': 11.0,
    },
    # ... more clips
]

# Process with transitions
result = engine.process(
    input_path=Path('data/test_samples/sample_01/video.mp4'),
    output_path=Path('data/output/transitioned.mp4'),
    broll_clips=broll_clips,
)

print(f"Created {result.metadata['segment_count']} segments")
print(f"Applied {result.metadata['transition_count']} transitions")
```

### Option 2: Test Script

```bash
# Create test script
python -c "
from pathlib import Path
from src.modules.transitions import TransitionEngine
from src.config import Config
import json

config = Config.from_yaml('config/brand_example.yaml')
engine = TransitionEngine(config)

# Load B-roll clips from JSON (from Stage 5 output)
with open('data/output/broll/video_clips.json') as f:
    data = json.load(f)
    broll_clips = data['clips']

result = engine.process(
    input_path=Path('data/test_samples/sample_01/video.mp4'),
    output_path=Path('data/output/transitioned_test.mp4'),
    broll_clips=broll_clips,
)
"
```

---

## ⚙️ Configuration

### Customize Transition Pattern

Edit `src/modules/transitions.py` line 64:

```python
self.transition_pattern = [
    'slideright',   # Avatar → B-roll
    'fade',         # B-roll → Avatar
    'dissolve',     # Avatar → B-roll
    'circleopen',   # B-roll → Avatar
    'slideright',   # Avatar → B-roll
    'zoomin',       # B-roll → Avatar
]
```

**Popular Options**:
- Smooth: `fade`, `dissolve`, `fadeblack`, `fadewhite`
- Dynamic: `slideright`, `slideleft`, `slideup`, `slidedown`
- Dramatic: `circleopen`, `circleclose`, `zoomin`, `radial`
- Wipes: `wipeleft`, `wiperight`, `wipeup`, `wipedown`
- Advanced: `pixelize`, `diagtl`, `diagbr`, `squeezeh`, `squeezev`

### Adjust Transition Duration

```python
# Line 63
self.default_duration = 0.5  # Change to 0.3s (faster) or 0.7s (slower)
```

### Disable Audio Crossfade

```python
# Line 65
self.audio_crossfade = False  # No audio crossfading
```

---

## 🔧 Integration with Pipeline

### Current Status

Transitions are currently **standalone** - they create a transitioned video but don't include captions/header.

### Full Integration (TODO)

To fully integrate with the pipeline:

1. **Option A**: Run transitions first, then add captions/header
   ```
   TransitionEngine → transitioned.mp4
   VideoComposer (captions/header) → final.mp4
   ```

2. **Option B**: Integrate into VideoComposer
   ```python
   # In composer.py process()
   if self.use_transitions and broll_clips:
       # Use TransitionEngine for base video
       temp_path = self.temp_dir / "transitioned_base.mp4"
       transition_engine.process(input_path, temp_path, broll_clips)
       input_path = temp_path  # Use transitioned video as input

   # Continue with caption/header overlay as normal
   ```

### CLI Integration (Future)

```bash
heygen-clipper process \
    --video video.mp4 \
    --script script.txt \
    --broll-plan plan.csv \
    --use-transitions \           # Enable transitions
    --transition-style varied \   # or 'smooth', 'dramatic', 'dynamic'
    --output data/output
```

---

## 📊 Performance Considerations

### Processing Time

**Without Transitions** (current):
- Video composition: ~0.5x realtime
- Example: 60s video = 30s processing

**With Transitions**:
- Segment extraction: ~0.2x realtime per segment
- xfade rendering: ~0.3x realtime per transition
- Example: 60s video with 5 B-roll clips = ~60-90s processing

**Optimization Tips**:
1. Use `preset=ultrafast` (already implemented)
2. Reduce transition duration (0.3s instead of 0.5s)
3. Limit number of B-roll segments
4. Use simpler transition types (fade vs circleopen)

### Output Quality

- **Codec**: libx264 (H.264)
- **Preset**: ultrafast (fast encoding)
- **CRF**: 18 (high quality)
- **Audio**: AAC 192kbps

---

## 🐛 Troubleshooting

### "FFmpeg failed: No such filter: 'xfade'"

**Cause**: Your FFmpeg version doesn't support xfade filter (requires FFmpeg 4.3+)

**Solution**:
```bash
# Check FFmpeg version
ffmpeg -version

# Update FFmpeg (macOS)
brew upgrade ffmpeg

# Update FFmpeg (Linux)
sudo apt update && sudo apt install ffmpeg
```

### Transitions Not Smooth

**Cause**: Transition duration too short or video quality mismatch

**Solutions**:
1. Increase transition duration to 0.6-0.8s
2. Ensure all videos are same resolution/framerate
3. Use simpler transitions (fade instead of complex effects)

### Audio Pops/Clicks at Transitions

**Cause**: Audio crossfade not smooth

**Solutions**:
1. Increase transition duration
2. Check audio_crossfade is enabled
3. Ensure all audio has same sample rate (48kHz)

### Segments Out of Sync

**Cause**: Timing calculation error or B-roll duration mismatch

**Solutions**:
1. Check B-roll plan CSV timing is correct
2. Verify B-roll videos are long enough for specified duration
3. Review segment generation logs for timing issues

---

## 📚 Examples

### Example 1: Simple Fade Transitions

```python
# Change transition pattern to all fades
engine.transition_pattern = ['fade'] * 6  # All transitions use fade

result = engine.process(video, output, broll_clips)
```

### Example 2: Dramatic Transitions Only

```python
# Use only dramatic effects
engine.transition_pattern = [
    'circleopen',
    'circleclose',
    'zoomin',
    'radial',
]

result = engine.process(video, output, broll_clips)
```

### Example 3: Custom Per-Segment Transitions

For now, edit the `transition_pattern` list to match your number of transitions.
Future: Configuration file support for per-segment control.

---

## 🔮 Roadmap

### Phase 3: Advanced Features (Future)

- [ ] Per-segment transition configuration via YAML
- [ ] CLI flag integration (`--use-transitions`)
- [ ] Transition preview/thumbnails
- [ ] Custom transition timing per segment
- [ ] GLSL shader transitions (advanced effects)
- [ ] Transition library management
- [ ] Performance profiling and optimization
- [ ] Parallel segment processing

### Phase 4: Professional Features (Future)

- [ ] Easing functions for smoother motion
- [ ] Custom transition curves
- [ ] Color grading during transitions
- [ ] Audio ducking synchronized with transitions
- [ ] Transition templates/presets
- [ ] Visual transition editor/preview
- [ ] Batch transition application

---

## 📖 Technical Reference

### FFmpeg xfade Filter Syntax

```bash
[input1][input2]xfade=transition=TRANSITION:duration=DURATION:offset=OFFSET[output]
```

**Parameters**:
- `transition`: Type (fade, dissolve, slide, etc.)
- `duration`: Transition length in seconds
- `offset`: When to start transition (relative to first input)

### Filter Complex Example

For 3 segments with 2 transitions:

```bash
ffmpeg -i seg0.mp4 -i seg1.mp4 -i seg2.mp4 \
  -filter_complex "
    [0:v][1:v]xfade=transition=slideright:duration=0.5:offset=2.5[v01];
    [v01][2:v]xfade=transition=fade:duration=0.5:offset=6.0[vout];
    [0:a][1:a]acrossfade=d=0.5[a01];
    [a01][2:a]acrossfade=d=0.5[aout]
  " \
  -map "[vout]" -map "[aout]" output.mp4
```

---

## 💡 Tips & Best Practices

1. **Start Simple**: Test with 2-3 B-roll clips before scaling up
2. **Match Duration**: Keep transitions 0.4-0.6s for TikTok/Reels style
3. **Vary Transitions**: Don't use same transition repeatedly (boring)
4. **Test Performance**: Profile on your hardware before production
5. **Audio Sync**: Always enable audio crossfade for professional results
6. **Preview First**: Test transitions on short clip before full video
7. **Backup Original**: Keep un-transitioned version for editing

---

## 🎯 Next Steps

1. **Test the Implementation**:
   ```bash
   # Run test with your video
   python test_transitions.py
   ```

2. **Customize Transitions**:
   - Edit `transition_pattern` in `transitions.py`
   - Adjust duration for your style
   - Test different combinations

3. **Integrate with Pipeline** (Optional):
   - Add CLI flag support
   - Integrate with VideoComposer
   - Add configuration file options

4. **Optimize Performance**:
   - Profile processing time
   - Optimize filter chain
   - Consider parallel processing

---

## 📞 Support

If you encounter issues:

1. Check FFmpeg version (need 4.3+)
2. Review logs for error messages
3. Test with simple transitions first
4. Verify B-roll plan timing is correct

For advanced customization, see `src/modules/transitions.py` for full implementation.
