# Vercel Deployment Guide

## 🚀 Quick Deploy (5 Minutes)

### Option 1: Deploy via Web UI (Easiest)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Add recommendation engine"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
   git push -u origin main
   ```

2. **Import to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "Add New Project"
   - Import your GitHub repository
   - Vercel will auto-detect it as a Python project

3. **Add Environment Variables**
   In Vercel project settings → Environment Variables, add:
   - `SUPABASE_URL` = `https://your-project.supabase.co`
   - `SUPABASE_KEY` = `your-service-role-key`
   - `OPENAI_API_KEY` = `sk-proj-...`

4. **Deploy**
   - Click "Deploy"
   - Wait ~2 minutes
   - You'll get a URL like `https://your-project.vercel.app`

### Option 2: Deploy via CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod

# Add environment variables when prompted:
# - SUPABASE_URL
# - SUPABASE_KEY
# - OPENAI_API_KEY
```

## 📡 Using Your API

Your endpoint will be:
```
https://your-project.vercel.app/api/recommend
```

### Example Request

```javascript
const response = await fetch('https://your-project.vercel.app/api/recommend', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user-uuid-here',
    limit: 10,
    min_score: 0.3
  })
})

const { recommendations } = await response.json()
```

## ✅ Benefits of Vercel

- ✨ **Simpler deployment** - Just `git push` or one command
- 🌍 **Global CDN** - Fast worldwide
- 🔄 **Auto-deploys** - Every git push deploys automatically
- 💰 **Generous free tier** - 100GB bandwidth, unlimited functions
- 🔗 **Easy integration** - Perfect if you're using Next.js/React

## 📝 File Structure

```
blueprintver1/
├── api/
│   └── recommend.py          # Vercel serverless function
├── requirements-vercel.txt   # Python dependencies
├── vercel.json               # Vercel config
└── setup_supabase.sql        # Database setup (run in Supabase)
```

## 🧪 Testing

After deployment, test with:

```bash
curl -X POST https://your-project.vercel.app/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-id",
    "limit": 5
  }'
```

## 🔧 Updating Your Function

Just push changes to GitHub:

```bash
git add api/recommend.py
git commit -m "Updated scoring algorithm"
git push
```

Vercel will automatically redeploy! 🎉

## ⚙️ Advanced: Custom Domain

In Vercel dashboard:
1. Go to project → Settings → Domains
2. Add your domain (e.g., `api.yourdomain.com`)
3. Follow DNS instructions
4. Access at `https://api.yourdomain.com/api/recommend`

## 💡 Tips

- **View Logs**: Vercel dashboard → Deployments → [latest] → Runtime Logs
- **Monitor Usage**: Dashboard → Usage tab
- **Environment Variables**: Can be different for Production/Preview/Development

---

**Ready?** Run `vercel` in your terminal and you'll be live in 2 minutes! 🚀
