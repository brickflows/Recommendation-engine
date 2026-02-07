# Vercel Deployment Steps

## 🔑 Login to Vercel

The deployment process has started. Follow these steps:

### Step 1: Login

When Vercel prompts "Please log in:", choose one of:
- **GitHub** (recommended if you use GitHub)
- **GitLab**
- **Email**

This will open your browser for authentication.

### Step 2: Configure Project

After logging in, Vercel will ask:

1. **"Set up and deploy?"** → Answer: **Y** (Yes)
2. **"Which scope?"** → Choose your account/team
3. **"Link to existing project?"** → Answer: **N** (No, create new)
4. **"What's your project's name?"** → Press Enter (use default) or type a name
5. **"In which directory is your code located?"** → Press Enter (current directory)

### Step 3: Wait for Deployment

Vercel will:
- ✓ Build your project
- ✓ Deploy to production
- ✓ Give you a URL like: `https://blueprintver1.vercel.app`

### Step 4: Add Environment Variables (CRITICAL!)

After deployment, you MUST add these in Vercel dashboard:

1. Go to https://vercel.com/dashboard
2. Click on your project
3. Go to **Settings** → **Environment Variables**
4. Add these three variables:

| Name | Value | Where to find |
|------|-------|---------------|
| `SUPABASE_URL` | `https://xxx.supabase.co` | Supabase → Settings → API |
| `SUPABASE_KEY` | `eyJhbG...` | Supabase → Settings → API → **service_role** key |
| `OPENAI_API_KEY` | `sk-proj-...` | OpenAI dashboard |

5. Click **Save**
6. Go to **Deployments** tab
7. Click the **...** menu on latest deployment → **Redeploy**

### Step 5: Test Your API

Once redeployed with env variables:

```bash
curl -X POST https://your-project.vercel.app/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-id", "limit": 5}'
```

## ⚠️ Important Notes

- The first deployment will FAIL because environment variables aren't set yet
- You MUST add the env variables and redeploy for it to work
- Use the **service_role** key from Supabase, NOT the anon key

## 📍 Current Status

✅ Vercel CLI installed  
🔄 Waiting for you to complete login in the terminal  
⏳ Will deploy after login is complete  
