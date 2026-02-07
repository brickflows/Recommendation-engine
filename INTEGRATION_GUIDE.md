# Recommendation Engine Integration Guide

Complete guide to deploying and integrating the side hustle recommendation system with your Supabase database.

## 📋 Prerequisites

- Google Cloud Platform account
- Supabase project with `blueprints` table populated
- OpenAI API key (for AI-powered skill matching)
- `gcloud` CLI installed ([Install guide](https://cloud.google.com/sdk/docs/install))

## 🚀 Quick Start (15 Minutes)

### Step 1: Set Up Database

1. Open Supabase SQL Editor
2. Copy and paste the contents of `setup_supabase.sql`
3. Execute the script

This creates:
- `users` table with `quiz_responses` column
- `recommendations_cache` table for performance
- Indexes and triggers

### Step 2: Configure Deployment

Edit `deploy.sh` and update these variables:

```bash
PROJECT_ID="your-gcp-project-id"           # Your GCP project
SUPABASE_URL="https://xxx.supabase.co"     # From Supabase settings
SUPABASE_KEY="eyJhbG..."                   # Service role key (not anon key!)
OPENAI_API_KEY="sk-proj-..."               # From OpenAI dashboard
```

> [!IMPORTANT]
> Use the **service role key**, not the anon key! Found in Supabase → Settings → API

### Step 3: Deploy to Google Cloud

```bash
# Make script executable (Mac/Linux)
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will output your Cloud Function URL. Copy it!

### Step 4: Test the API

```bash
# Test with curl
curl -X POST https://REGION-PROJECT.cloudfunctions.net/recommend-businesses \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "your-test-user-uuid",
    "limit": 5,
    "min_score": 0.3
  }'
```

## 🔗 Frontend Integration

### Saving Quiz Responses

When user completes the quiz, save to Supabase:

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

async function saveQuizResponses(userId, quizData) {
  const { data, error } = await supabase
    .from('users')
    .upsert({
      id: userId,
      quiz_responses: {
        background: quizData.background,
        skills: quizData.skills,
        willing_to_learn: quizData.willingToLearn,
        weekly_hours: quizData.weeklyHours,        // 0, 1, 2, or 3
        work_schedule: quizData.schedule,          // flexible, weekends, etc.
        earning_urgency: quizData.urgency,         // weeks, months, months+
        task_preference: quizData.taskPreference,  // creative, structured, etc.
        avoidances: quizData.avoidances,           // ['heavy', 'delivery']
        investment_budget: quizData.budget,        // in dollars
        risk_tolerance: quizData.risk,             // low, moderate, high
        tech_comfort: quizData.tech                // very, moderate, minimal, none
      }
    })
  
  return { data, error }
}
```

### Getting Recommendations

Call the Cloud Function after saving quiz:

```javascript
async function getRecommendations(userId, limit = 10) {
  const response = await fetch(
    'https://REGION-PROJECT.cloudfunctions.net/recommend-businesses',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        limit: limit,
        min_score: 0.3,    // Only show 30%+ matches
        use_ai: true        // Set to false to skip AI (faster but less accurate)
      })
    }
  )
  
  const result = await response.json()
  return result.recommendations
}
```

### Displaying Results

```javascript
function RecommendationCard({ recommendation }) {
  const matchPercentage = Math.round(recommendation.total_score * 100)
  
  return (
    <div className="recommendation-card">
      <h3>{recommendation.business_title}</h3>
      <div className="match-score">{matchPercentage}% Match</div>
      
      <p>{recommendation.summary}</p>
      
      <div className="details">
        <span>💰 Profit: {recommendation.estimated_profit}</span>
        <span>💵 Cost: {recommendation.startup_cost}</span>
      </div>
      
      <p className="match-reason">{recommendation.match_reason}</p>
      
      {/* Score breakdown */}
      <div className="breakdown">
        {Object.entries(recommendation.breakdown).map(([factor, score]) => (
          <div key={factor}>
            <span>{factor.replace('_', ' ')}</span>
            <progress value={score} max="1" />
          </div>
        ))}
      </div>
    </div>
  )
}
```

## 📊 Quiz Data Format

Your quiz responses should match this structure:

```typescript
interface QuizResponses {
  // Professional background (free text)
  background: string
  
  // Skills array (e.g., ['web_development', 'writing'])
  skills: string[]
  
  // Willingness to learn: 'yes' | 'no' | 'possible'
  willing_to_learn: string
  
  // Weekly hours available: 0=5hrs, 1=10hrs, 2=20hrs, 3=30hrs
  weekly_hours: 0 | 1 | 2 | 3
  
  // Work schedule: 'flexible' | 'weekends' | 'weekdays' | 'evenings' | 'early'
  work_schedule: string
  
  // Earning urgency: 'weeks' | 'months' | 'months+'
  earning_urgency: string
  
  // Task preference: 'creative' | 'structured' | 'analytical' | 'social' | 'mixed'
  task_preference: string
  
  // Things to avoid: ['door', 'heavy', 'nights', 'delivery', 'children', 'none']
  avoidances: string[]
  
  // Investment budget in dollars (0, 100, 500, 1500, 2500)
  investment_budget: number
  
  // Risk tolerance: 'very_low' | 'low' | 'moderate' | 'high'
  risk_tolerance: string
  
  // Tech comfort: 'very' | 'moderate' | 'minimal' | 'none'
  tech_comfort: string
}
```

## 🎯 API Reference

### Request

```
POST /recommend-businesses
Content-Type: application/json

{
  "user_id": "uuid",      // Required: User ID in Supabase
  "limit": 10,            // Optional: Max recommendations (default: 10)
  "min_score": 0.3,       // Optional: Minimum match score (default: 0.3)
  "use_ai": true          // Optional: Use AI for skill matching (default: true)
}
```

### Response

```json
{
  "success": true,
  "user_id": "uuid",
  "recommendations": [
    {
      "business_id": "uuid",
      "business_title": "AI-Powered T-Shirt Business",
      "total_score": 0.947,
      "match_reason": "Strong match in: skill match, tech comfort, startup cost",
      "breakdown": {
        "startup_cost": 1.0,
        "time_commitment": 1.0,
        "skill_match": 0.85,
        "schedule_fit": 1.0,
        "risk_tolerance": 0.7,
        "tech_comfort": 1.0,
        "task_preference": 1.0
      },
      "estimated_profit": "$1,000–$10,000",
      "startup_cost": "$100–$500",
      "thumbnail_url": "https://...",
      "video_link": "https://...",
      "summary": "Brief description..."
    }
  ],
  "total_analyzed": 150,
  "total_matches": 10
}
```

## ⚡ Caching Strategy

The system automatically caches results in `recommendations_cache` table:

- **First request**: Scores all blueprints (~3-5 seconds)
- **Cached requests**: Instant retrieval from cache
- **Cache invalidation**: Update `updated_at` to force recalculation

### Forcing Fresh Recommendations

```javascript
// Option 1: Delete cache entry
await supabase
  .from('recommendations_cache')
  .delete()
  .eq('user_id', userId)

// Then request again (will recalculate)

// Option 2: Daily batch recalculation (recommended)
// Use Google Cloud Scheduler to trigger daily at 2am
```

## 💰 Cost Breakdown

### Google Cloud Functions
- **Free tier**: 2M invocations/month
- **After free tier**: $0.40 per million invocations
- **Your cost**: ~$0 for <2M users/month

### OpenAI API (GPT-4o-mini)
- **Input tokens**: ~300 tokens per business
- **Cost per request**: ~$0.0001 per business
- **Total per user**: ~$0.015 (for 150 businesses)
- **1,000 users**: ~$15/month

### Supabase
- **Free tier**: 500MB database, 2GB file storage
- **Your cost**: ~$0 initially

**Total for 1,000 users/day: ~$35/month**

## 🧪 Testing

### Local Testing (No API Calls)

```bash
python test_local.py
```

Tests all scoring functions with sample data.

### Production Testing

```bash
# Create a test user
curl -X POST https://YOUR-SUPABASE-URL/rest/v1/users \
  -H "apikey: YOUR-ANON-KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-user-123",
    "quiz_responses": {
      "background": "Web developer",
      "skills": ["programming"],
      "weekly_hours": 2,
      "investment_budget": 1000,
      "work_schedule": "flexible",
      "risk_tolerance": "moderate",
      "tech_comfort": "very",
      "task_preference": "creative",
      "avoidances": ["heavy"],
      "willing_to_learn": "yes"
    }
  }'

# Get recommendations
curl -X POST https://YOUR-FUNCTION-URL \
  -d '{"user_id": "test-user-123"}'
```

## 🐛 Troubleshooting

### "User not found" Error

**Cause**: No quiz data in `users` table for that user ID

**Fix**: Ensure quiz responses are saved before requesting recommendations

```javascript
// Save quiz first
await saveQuizResponses(userId, quizData)

// Then get recommendations
const recommendations = await getRecommendations(userId)
```

### "No businesses found" Error

**Cause**: No published blueprints in database

**Fix**: Ensure `published = true` for blueprints you want to recommend

```sql
UPDATE blueprints SET published = true WHERE id = '...';
```

### Slow Response Times

**Cause**: AI skill matching for 100+ businesses

**Solutions**:
1. Reduce `limit` parameter (only score top candidates)
2. Set `use_ai: false` to skip AI (instant but less accurate)
3. Implement caching (already included)
4. Pre-calculate recommendations daily (batch job)

### OpenAI Rate Limits

**Cause**: Too many concurrent requests

**Fix**: Implement request queuing or reduce `max_instances` in `deploy.sh`

## 🔄 Daily Batch Updates (Advanced)

For better performance, pre-calculate recommendations daily:

1. Create Cloud Scheduler job:

```bash
gcloud scheduler jobs create http daily-recommendations \
  --schedule="0 2 * * *" \
  --uri="https://YOUR-FUNCTION-URL/batch-update" \
  --http-method=POST
```

2. Add batch endpoint to `recommendation_engine.py`:

```python
@functions_framework.http
def batch_update_recommendations(request):
    """Pre-calculate recommendations for all users"""
    users = supabase.table('users').select('id, quiz_responses').execute()
    
    for user in users.data:
        # Calculate and cache
        # ... (similar to recommend_businesses)
    
    return {'success': True, 'processed': len(users.data)}
```

## 📞 Support

- Check existing blueprints: `SELECT COUNT(*) FROM blueprints WHERE published = true`
- View cached recommendations: `SELECT * FROM recommendations_cache WHERE user_id = '...'`
- Monitor Cloud Functions: [GCP Console](https://console.cloud.google.com/functions)
- Check OpenAI usage: [OpenAI Dashboard](https://platform.openai.com/usage)

---

**Ready to launch?** Follow the Quick Start and you'll be live in 15 minutes! 🚀
