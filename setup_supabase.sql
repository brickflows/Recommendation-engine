-- ============================================
-- Recommendation Engine Database Setup
-- Run this in Supabase SQL Editor (one time only)
-- ============================================

-- Create users table (if not exists) for storing quiz responses
CREATE TABLE IF NOT EXISTS public.users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT,
  quiz_responses JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add quiz_responses column if table already exists
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'users' AND column_name = 'quiz_responses'
  ) THEN
    ALTER TABLE public.users ADD COLUMN quiz_responses JSONB;
  END IF;
END $$;

-- Create recommendations_cache table for storing computed recommendations
CREATE TABLE IF NOT EXISTS public.recommendations_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  recommendations JSONB NOT NULL,
  total_analyzed INTEGER,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  CONSTRAINT unique_user_cache UNIQUE (user_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_quiz_responses ON public.users USING GIN (quiz_responses);
CREATE INDEX IF NOT EXISTS idx_recommendations_cache_user_id ON public.recommendations_cache (user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_cache_updated_at ON public.recommendations_cache (updated_at);

-- Create function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON public.users;
CREATE TRIGGER update_users_updated_at
  BEFORE UPDATE ON public.users
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for recommendations_cache table
DROP TRIGGER IF EXISTS update_cache_updated_at ON public.recommendations_cache;
CREATE TRIGGER update_cache_updated_at
  BEFORE UPDATE ON public.recommendations_cache
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (optional - adjust based on your needs)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendations_cache ENABLE ROW LEVEL SECURITY;

-- Example RLS policy: Users can only read their own data
-- IMPORTANT: Adjust these policies based on your authentication setup
CREATE POLICY "Users can view own data" ON public.users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own data" ON public.users
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own recommendations" ON public.recommendations_cache
  FOR SELECT USING (auth.uid() = user_id);

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE ON public.users TO authenticated, anon;
GRANT SELECT, INSERT, UPDATE ON public.recommendations_cache TO authenticated, anon;

-- ============================================
-- SUCCESS!
-- ============================================
-- Tables created:
-- 1. users (with quiz_responses JSONB column)
-- 2. recommendations_cache (for caching scored results)
--
-- Next steps:
-- 1. Update deploy.sh with your Supabase credentials
-- 2. Deploy the Cloud Function: ./deploy.sh
-- 3. Test with a sample user
-- ============================================
