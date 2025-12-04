# Webapp Deployment Win: When Cloud Run Just Works

**Date**: 2025-12-04 17:00
**Severity**: Low (Success)
**Component**: Deployment Pipeline
**Status**: Live in Production

## What Happened

Deployed the search comparison webapp to Firebase Hosting + Cloud Run. First deployment attempt worked. No debugging. No environment variable hell. No Docker issues. Just:

```bash
firebase deploy
```

And 2 minutes later: live webapp at a public URL showing side-by-side query comparisons.

## The Brutal Truth (But This Time It's Good)

After yesterday's test framework showing 20% pass rates and this morning's strategic planning anxiety, this is exactly the kind of small win that keeps momentum going.

**What works**:
- Frontend: React app on Firebase Hosting
- Backend: Flask API on Cloud Run (containerized)
- Integration: CORS configured correctly, API routes responding
- Performance: No latency issues (even with PubMed API calls)

**What's surprisingly smooth**:
- Docker build (no dependency conflicts)
- Cloud Run deployment (auto-scaling works)
- Firebase hosting (static files cached properly)
- Cost: $0 (under free tier limits)

## Technical Details

**Architecture**:
```
Firebase Hosting (React frontend)
    ↓ CORS request
Cloud Run (Flask backend)
    ↓ API calls
[PubTator → UMLS → PubMed]
    ↓ results
Frontend renders side-by-side comparison
```

**Configuration files**:
- `firebase.json` - Hosting + Cloud Run integration
- `Dockerfile` - Flask app containerization
- `.firebaserc` - Project ID mapping
- Environment variables: None needed (APIs don't require auth for POC)

**Deployment metrics**:
- Build time: ~90 seconds
- Deploy time: ~30 seconds
- Cold start: <2 seconds
- Warm latency: ~15 seconds (PubMed bottleneck)

## What We Tried

This was actually straightforward. The webapp code was already tested locally, so deployment was just:
1. Add Firebase config files
2. Write Dockerfile
3. Run `firebase deploy`
4. Verify endpoints respond

No iteration. No debugging. Which is suspicious and makes me wonder what I forgot to test.

## Root Cause Analysis

**Why this worked smoothly when other things didn't**:

1. **Stateless API**: No database persistence, no session management - just request/response
2. **Standard tools**: Flask + Docker + Firebase are well-worn paths
3. **Simple requirements**: Python dependencies are stable (no version conflicts)
4. **No auth complexity**: Public APIs don't need API keys or OAuth for POC
5. **Local testing first**: Everything worked on `localhost:5000` before deployment

**The insight**: Deployment pain is usually a proxy for architectural complexity. Simple stateless APIs deploy easily. Complex stateful services don't.

## Lessons Learned

1. **Firebase makes this easy**: Hosting + Cloud Run integration handles CORS, routing, SSL automatically
2. **Containerization is worth it**: Docker ensures prod matches local (no "works on my machine")
3. **Stateless wins**: No database means no migration hell, no backup strategy, no connection pooling
4. **Test locally first**: `docker build && docker run` catches issues before GCP sees them
5. **Free tiers are generous**: Firebase Hosting + Cloud Run = $0 for POC traffic

## The Satisfying Part

There's something deeply pleasing about:
```
$ firebase deploy
✓ Build complete
✓ Deploying to Cloud Run
✓ Frontend deployed to Firebase Hosting
✨ Done!
```

No errors. No warnings. No "did you forget to..." messages. Just success.

## Next Steps

1. ✅ Webapp live at public URL
2. Test with real users (send link to James?)
3. Add more configs to comparison (currently 2, want 5)
4. Implement result saving (local storage for now)
5. Add loading states (15s latency feels longer without feedback)

## Emotional Footnote

After a week of:
- Test framework failures (20% pass rate)
- API disambiguation errors (TMS → tetramethylsilane)
- Strategic uncertainty (what to build next?)
- Threshold tuning (is 1,943 results "too many"?)

It's genuinely refreshing to have something Just Work™ on the first try.

Small wins matter when you're debugging big architectural questions.

**Commit**: `692f329 feat: deploy search comparison tool to Firebase + Cloud Run`

**Live URL**: [redacted in journal - see Firebase console]
