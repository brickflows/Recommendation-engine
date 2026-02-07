# Side Hustle Recommendation Engine

AI-powered recommendation system that matches users with side hustles based on their quiz responses.

## 🎯 What It Does

Scores each business opportunity using 7 factors:
- **Startup Cost** (25%) - Affordability check
- **Time Available** (20%) - Hours needed vs available
- **Skill Match** (20%) - AI-powered skill alignment via GPT-4o-mini
- **Schedule Fit** (10%) - Work timing compatibility
- **Risk Tolerance** (10%) - Investment risk matching
- **Tech Comfort** (8%) - Technology requirements
- **Task Preference** (7%) - Type of work alignment

## 🚀 Quick Start

### Choose Your Deployment

**Option 1: Vercel (Recommended - Simpler)** ⭐
```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Deploy
vercel --prod

# 3. Add environment variables when prompted
# Done! Get URL instantly
```

[Full Vercel Guide →](VERCEL_DEPLOY.md)

**Option 2: Google Cloud Functions (More control)**
```bash
# 1. Edit deploy.sh with credentials
# 2. Run deployment
./deploy.sh
```

[Full GCP Guide →](INTEGRATION_GUIDE.md)

## 📊 Deployment Comparison

| Feature | Vercel | Google Cloud |
|---------|--------|--------------|
| **Setup Time** | 2 minutes | 10 minutes |
| **Deployment** | `vercel` or git push | `./deploy.sh` |
| **Free Tier** | 100GB/mo, unlimited functions | 2M requests/mo |
| **Auto-deploy** | ✅ On git push | ❌ Manual |
| **Custom domains** | ✅ Easy | ✅ Requires config |
| **Logs** | Dashboard | Cloud Console |
| **Best for** | Quick start, Next.js apps | Enterprise, GCP ecosystem |

## 📁 Files

### For Vercel Deployment
- `api/recommend.py` - Serverless function
- `requirements-vercel.txt` - Dependencies
- `vercel.json` - Configuration
- `VERCEL_DEPLOY.md` - Deployment guide

### For Google Cloud Deployment
- `recommendation_engine.py` - Cloud Function
- `requirements.txt` - Dependencies
- `deploy.sh` - Deployment script
- `INTEGRATION_GUIDE.md` - Full guide

### Shared Files
- `setup_supabase.sql` - Database migration (run once)
- `test_local.py` - Local testing utility

## 🧪 Test Locally

```bash
pip install -r requirements-vercel.txt
python test_local.py
```

## 📡 API Usage

### Save Quiz to Supabase

```javascript
await supabase.from('users').upsert({
  id: userId,
  quiz_responses: {
    background: "Software developer",
    skills: ["programming"],
    weekly_hours: 2,           // 0/1/2/3 = 5/10/20/30 hrs
    investment_budget: 1500,
    work_schedule: "flexible",
    risk_tolerance: "moderate",
    tech_comfort: "very",
    task_preference: "creative",
    avoidances: ["heavy"],
    willing_to_learn: "yes"
  }
})
```

### Get Recommendations

```javascript
const res = await fetch('https://your-deployment-url/api/recommend', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: userId,
    limit: 10,
    min_score: 0.3
  })
})

const { recommendations } = await res.json()
```

### Response Format

```json
{
  "success": true,
  "recommendations": [
    {
      "business_title": "AI-Powered T-Shirt Business",
      "total_score": 0.947,
      "match_reason": "Strong match in: skill match, tech comfort, startup cost",
      "breakdown": {
        "startup_cost": 1.0,
        "time_commitment": 1.0,
        "skill_match": 0.85,
        ...
      },
      "estimated_profit": "$1,000–$10,000",
      "startup_cost": "$100–$500"
    }
  ]
}
```

## 💰 Costs

**Vercel**: FREE for most use cases (100GB bandwidth/month)  
**Google Cloud**: FREE under 2M requests/month  
**OpenAI API**: ~$0.015 per user (for 150 businesses)

**Total for 1,000 users/day**: ~$15-35/month

## 🔧 Environment Variables

All deployment options need:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Service role key (not anon key!)
- `OPENAI_API_KEY` - OpenAI API key

## 📚 Documentation

- [Vercel Deployment Guide](VERCEL_DEPLOY.md) - Simplest option
- [Google Cloud Guide](INTEGRATION_GUIDE.md) - Full control option
- [Implementation Walkthrough](walkthrough.md) - How it works

## ✅ What's Tested

- ✓ All 7 scoring factors validated
- ✓ Avoidance filters working correctly
- ✓ Cost parsing handles multiple formats
- ✓ AI skill matching with fallback
- ✓ Supabase caching for performance

## 🎉 Next Steps

1. Choose deployment platform (Vercel recommended)
2. Run `setup_supabase.sql` in Supabase
3. Deploy using guide for your chosen platform
4. Test with `curl` or Postman
5. Integrate into your frontend

---

**Ready to deploy?** Start with [VERCEL_DEPLOY.md](VERCEL_DEPLOY.md) for the fastest path! 🚀
