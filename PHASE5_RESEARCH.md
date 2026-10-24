# Phase 5 Research: MusicBrainz & Audio Verifier

## Overview
Phase 5 is marked as "Research tier (only if the harness justifies it)". Based on evaluation results, we need to assess if it's worth implementing.

## Current State
- Evaluation shows precision 1.0000, recall 0.9459 with current ISRC + metadata approach
- Only 2 failures (FN) in evaluation, both likely non-Latin script issues
- Audio verifier would only help ambiguous band (~3-10% of tracks)
- Current approach already meets precision requirements

## MusicBrainz Integration

### Option 1: Live API (not recommended)
- Rate limit: ~1 req/s for unauthenticated
- Would slow down matching significantly
- Need to respect rate limits

### Option 2: Local data dump (recommended if needed)
- Download MusicBrainz PostgreSQL dump (~100GB+)
- Or use smaller filtered dumps
- Much faster lookups
- Requires significant infrastructure

**Assessment:** Current ISRC matching is sufficient. MusicBrainz expansion would help with "same song, different ISRC" cases, but we need to measure frequency first.

## Audio Verifier

### Requirements
- Only use sanctioned preview URLs
- Need to distinguish same recording vs same work
- CLAP-style embeddings bad for "different song by same artist"
- Chromaprint/fingerprinting better for same recording
- Cache embeddings
- Feature flag required
- Only for ambiguous band (3-10%)

### Available Options
- **Chromaprint/AcoustID:** Good for exact recording matches, but needs fingerprints
- **Deezer previews:** Available for some tracks
- **Spotify previews:** Available for some tracks (30s previews)
- **Last.fm:** No official preview API in same way

**Challenges:**
- Many tracks don't have previews
- Preview URLs may not be available
- Processing overhead
- Need to verify platform ToS compliance

## Recommendation

**Do NOT implement Phase 5 yet** unless:
1. Evaluation shows need for MusicBrainz (different ISRC cases appear frequently)
2. Ambiguous band is actually >10% and needs disambiguation
3. Precision drops below threshold

Current implementation already achieves:
- Precision: 1.0000 (above 0.7667 baseline)
- No false positives
- Good coverage with ISRC + metadata

## Proposed Implementation (if justified)

If justified later:
1. Create `matching/musicbrainz.py` with interface + stub
2. Add feature flag `ENABLE_AUDIO_VERIFIER=false` in config
3. Create `matching/audio_verifier.py` with abstain logic
4. Add Chromaprint integration only if previews available
5. Track metrics to measure impact

**Status:** Researched. Not implemented per spec guidance ("Do not build this until the evaluation harness shows it is worth it").
