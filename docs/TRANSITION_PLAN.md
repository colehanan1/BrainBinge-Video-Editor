# Video Transition Implementation Plan

> Adding smooth transitions between avatar and B-roll footage using FFmpeg's xfade filter

## Overview

**Goal**: Add professional transitions when switching between avatar footage and B-roll clips (and vice versa) for TikTok-style videos.

**Technology**: FFmpeg `xfade` filter - provides 44 built-in transition effects without requiring external assets.

---

## Available Transition Effects (44 Total)

### ⭐ Recommended for Social Media

| Transition | Style | Best For | Duration |
|------------|-------|----------|----------|
| **fade** | Smooth crossfade | Professional, subtle | 0.3-0.5s |
| **dissolve** | Gradual blend | Smooth, seamless | 0.4-0.6s |
| **slideright** | Swipe right → | Dynamic, TikTok-style | 0.3-0.4s |
| **slideleft** | Swipe ← left | Dynamic, TikTok-style | 0.3-0.4s |
| **circleopen** | Circle expands | Dramatic reveal | 0.5-0.7s |
| **zoomin** | Zoom in effect | Energetic | 0.3-0.5s |
| **pixelize** | Glitch/pixel | Modern, edgy | 0.2-0.3s |

### Full List (44 Effects)

**Basic Fades:**
- fade, fadeblack, fadewhite, fadegrays, dissolve

**Wipes (4 directions):**
- wipeleft, wiperight, wipeup, wipedown
- wipetl, wipetr, wipebl, wipebr (diagonal wipes)

**Slides (4 directions):**
- slideleft, slideright, slideup, slidedown

**Smooth (4 directions):**
- smoothleft, smoothright, smoothup, smoothdown

**Circles:**
- circleopen, circleclose, circlecrop

**Rectangles:**
- rectcrop, vertopen, vertclose, horzopen, horzclose

**Slices:**
- hlslice, hrslice, vuslice, vdslice

**Diagonal:**
- diagtl, diagtr, diagbl, diagbr

**Squeeze:**
- squeezeh, squeezev

**Advanced:**
- distance, radial, hblur, zoomin, pixelize, custom

---

## Technical Implementation

### Current Architecture Challenge

**Problem**: Our current pipeline uses fullframe B-roll as overlays on a single continuous avatar video. The xfade filter requires **two separate video streams** to transition between.

**Current Flow**:
```
Avatar video → Scale → Header → B-roll overlay (enable=t) → Captions
```

**Required for xfade**:
```
Video1 → xfade(transition=fade) → Video2
```

### Implementation Strategy

**Option 1: Segment-Based Approach (Recommended)**

1. **Split video into segments**:
   - Avatar intro (0s - 3s)
   - B-roll 1 (3s - 6.5s)
   - Avatar middle (6.5s - 8s)
   - B-roll 2 (8s - 11s)
   - ... etc.

2. **Apply xfade between each segment**:
   ```bash
   segment1 → xfade(fade, 0.3s) → segment2 → xfade(fade, 0.3s) → segment3
   ```

3. **Add captions/header as final overlay**

**Implementation Steps**:
- Modify `composer.py` to generate segment list from B-roll plan
- Create segment trimming logic (avatar video at specific times)
- Build xfade filter chain with all segments
- Apply captions/header on final merged video

**Pros**:
- ✅ True transitions between footage
- ✅ Professional appearance
- ✅ Uses FFmpeg native filters

**Cons**:
- ⚠️ More complex filter graph
- ⚠️ Longer processing time
- ⚠️ Requires architecture refactor

---

**Option 2: Fade-Only Approach (Simpler)**

Keep current overlay approach but add fade in/out at B-roll boundaries.

**Current B-roll**: Already has fade in/out (0.3s duration)
```python
.filter('fade', type='in', duration=self.fade_duration)
.filter('fade', type='out', start_time=duration - self.fade_duration)
```

**Enhancement**: Simultaneously fade out avatar during B-roll
- Add opacity reduction to avatar during B-roll segments
- Creates smoother blending effect
- Less jarring than hard cuts

**Implementation Steps**:
- Add alpha channel manipulation to avatar video
- Reduce opacity during B-roll segments using `geq` or `colorchannelmixer`
- Results in cross-fade effect

**Pros**:
- ✅ Simpler to implement
- ✅ Works with current architecture
- ✅ Faster processing

**Cons**:
- ⚠️ Limited to fade transitions only
- ⚠️ Not true xfade (both videos visible during transition)

---

## Recommended Approach

### Phase 1: Enhanced Fades (Quick Win)

Improve current fade implementation:

1. **Adjust fade duration** for smoother transitions:
   ```python
   self.fade_duration = 0.5  # Increase from 0.3s to 0.5s
   ```

2. **Add avatar opacity fade** during B-roll:
   - When B-roll appears, fade avatar to 30% opacity
   - When B-roll ends, fade avatar back to 100%
   - Creates professional cross-fade effect

3. **Timing adjustment**:
   - Start B-roll fade 0.2s before actual B-roll start
   - End B-roll fade 0.2s after B-roll ends
   - Overlap creates smoother transition

**Effort**: Low (2-4 hours)
**Impact**: Medium (noticeably smoother)

### Phase 2: True xfade Transitions (Future Enhancement)

Implement segment-based approach with full xfade support:

1. **Segment generation module**:
   - Parse B-roll plan
   - Generate segment list with transition points
   - Trim avatar and B-roll into segments

2. **xfade chain builder**:
   - Dynamically build xfade filter complex
   - Support multiple transition types
   - Configurable per-segment

3. **Configuration**:
   ```yaml
   transitions:
     enabled: true
     default_type: "fade"  # or slideright, dissolve, etc.
     duration: 0.5
     per_segment:
       - segment: 0  # Avatar → B-roll 1
         type: "slideright"
         duration: 0.4
       - segment: 1  # B-roll 1 → Avatar
         type: "fade"
         duration: 0.5
   ```

**Effort**: High (1-2 days)
**Impact**: High (professional-grade transitions)

---

## Perplexity AI Prompt (Alternative Research)

If you want more detailed research, use this prompt with Perplexity AI:

```
Research FFmpeg xfade filter transitions for TikTok-style social media videos:

1. Find the most popular transition effects used in viral TikTok/Instagram Reels content (2024)
2. Identify best practices for transition timing (duration, overlap)
3. Locate examples of implementing xfade in Python ffmpeg-python library
4. Find any pre-built transition libraries or tools that work with FFmpeg
5. Compare xfade performance vs other transition methods
6. Look for examples of dynamic multi-segment video stitching with transitions

Focus on:
- Transition types that feel modern and engaging
- Implementation complexity vs visual impact
- Processing speed considerations for 60-second videos
- Best practices from video editing professionals

Provide code examples if available.
```

---

## Implementation Checklist

### Phase 1 (Recommended - Start Here)
- [ ] Increase fade duration to 0.5s for smoother transitions
- [ ] Test current fade appearance on sample video
- [ ] Document fade timing adjustments
- [ ] Add configuration option for fade duration

### Phase 2 (Future - Full Transitions)
- [ ] Design segment generation algorithm
- [ ] Implement video segment trimming
- [ ] Build xfade filter chain dynamically
- [ ] Add transition type configuration
- [ ] Test with multiple transition effects
- [ ] Optimize processing performance
- [ ] Document transition customization guide

---

## Example xfade Commands

### Two Videos with Fade
```bash
ffmpeg -i avatar.mp4 -i broll.mp4 \
  -filter_complex "[0][1]xfade=transition=fade:duration=0.5:offset=5.5" \
  output.mp4
```

### Multiple Segments with Different Transitions
```bash
ffmpeg -i seg1.mp4 -i seg2.mp4 -i seg3.mp4 \
  -filter_complex "\
    [0][1]xfade=transition=slideright:duration=0.4:offset=2.6[v01];\
    [v01][2]xfade=transition=fade:duration=0.5:offset=5.6[out]" \
  -map "[out]" output.mp4
```

### With Audio Crossfade
```bash
ffmpeg -i video1.mp4 -i video2.mp4 \
  -filter_complex "\
    [0:v][1:v]xfade=transition=fade:duration=0.5:offset=5.5[vout];\
    [0:a][1:a]acrossfade=d=0.5[aout]" \
  -map "[vout]" -map "[aout]" output.mp4
```

---

## Resources

- [FFmpeg xfade documentation](https://ffmpeg.org/ffmpeg-filters.html#xfade)
- [OTTVerse xfade guide](https://ottverse.com/crossfade-between-videos-ffmpeg-xfade-filter/)
- [xfade-easing GitHub](https://github.com/scriptituk/xfade-easing) - Advanced transitions
- [FFmpeg filter gallery](https://trac.ffmpeg.org/wiki/Xfade) - Visual examples

---

## Questions & Considerations

1. **Which transition style do you prefer?**
   - Smooth fades (professional)
   - Slide/swipe (dynamic, TikTok-style)
   - Circle/zoom (dramatic)
   - Glitch/pixelize (edgy)

2. **Same transition throughout or varied?**
   - Consistent: Same transition for all B-roll changes
   - Varied: Different transitions per segment

3. **Processing time vs. effect quality?**
   - Phase 1 (enhanced fades): Fast processing
   - Phase 2 (true xfade): Slower but more professional

4. **Transition timing?**
   - Short (0.2-0.3s): Snappy, energetic
   - Medium (0.4-0.5s): Balanced
   - Long (0.6-0.8s): Smooth, cinematic

---

**Next Steps**:
1. Review this plan
2. Choose Phase 1 (quick) or Phase 2 (full implementation)
3. Select preferred transition types
4. Approve implementation approach
