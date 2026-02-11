"""
Business Recommendation Engine - Vercel Serverless Function
Matches user quiz responses with business opportunities using weighted scoring
Works with Supabase PostgreSQL database
"""

from http.server import BaseHTTPRequestHandler
import openai
import json
from typing import Dict, List, Any, Tuple
import os
from supabase import create_client, Client

# Initialize clients lazily to avoid crashing on import if env vars are missing
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_KEY')
openai.api_key = os.environ.get('OPENAI_API_KEY')

_supabase_client = None

def get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        if not supabase_url or not supabase_key:
            raise ValueError('SUPABASE_URL and SUPABASE_KEY environment variables are required')
        _supabase_client = create_client(supabase_url, supabase_key)
    return _supabase_client

# Scoring weights
WEIGHTS = {
    'startup_cost': 0.25,
    'time_commitment': 0.20,
    'skill_match': 0.20,
    'schedule_fit': 0.10,
    'risk_tolerance': 0.10,
    'tech_comfort': 0.08,
    'task_preference': 0.07
}


def parse_cost_range(cost_str: str) -> Tuple[int, int]:
    """Extract min and max from cost string like '$1,000–$3,000'"""
    if not cost_str:
        return 0, 0
    
    cost_str = cost_str.replace('$', '').replace(',', '').strip()
    
    for separator in ['–', '-', 'to']:
        if separator in cost_str:
            parts = cost_str.split(separator)
            if len(parts) == 2:
                try:
                    min_val = int(parts[0].strip())
                    max_val = int(parts[1].strip())
                    return min_val, max_val
                except (ValueError, AttributeError):
                    pass
    
    try:
        single_val = int(cost_str)
        return single_val, single_val
    except:
        return 0, 0


def score_startup_cost(user_budget: int, business_cost_str: str) -> float:
    """Score based on whether user can afford the business"""
    min_cost, max_cost = parse_cost_range(business_cost_str)
    
    if min_cost == 0 and max_cost == 0:
        return 0.8
    
    avg_cost = (min_cost + max_cost) / 2
    
    if user_budget >= avg_cost:
        return 1.0
    elif user_budget >= min_cost:
        return 0.7
    elif user_budget >= min_cost * 0.5:
        return 0.4
    else:
        return 0.1


def score_time_commitment(user_hours: int, business_level: str) -> float:
    """Score based on time availability vs business requirements"""
    hours_map = {0: 5, 1: 10, 2: 20, 3: 30}
    actual_hours = hours_map.get(user_hours, 10)
    
    level_hours = {
        'Beginner': 10,
        'Intermediate': 15,
        'Beginner to Intermediate': 12,
        'Advanced': 20,
        '': 15
    }
    
    required_hours = level_hours.get(business_level, 15)
    
    if actual_hours >= required_hours * 1.5:
        return 1.0
    elif actual_hours >= required_hours:
        return 0.9
    elif actual_hours >= required_hours * 0.7:
        return 0.6
    else:
        return 0.3


def score_skill_match_ai(user_background: str, user_skills: List[str], 
                         business_industries: List[str], business_title: str,
                         business_description: str, willing_to_learn: str) -> float:
    """Use AI to score skill match between user and business"""
    
    skills_text = ', '.join(user_skills) if user_skills else 'None specified'
    industries_text = ', '.join(business_industries) if business_industries else 'Various'
    
    prompt = f"""Rate the skill match between this user and business on a 0-1 scale.

USER PROFILE:
- Background: {user_background}
- Skills: {skills_text}
- Willing to learn new skills: {willing_to_learn}

BUSINESS:
- Title: {business_title}
- Industries: {industries_text}
- Description: {business_description[:400] if business_description else 'No description available'}

Consider:
1. Direct skill overlap (0.4 weight)
2. Transferable skills (0.3 weight)
3. Learning curve feasibility based on willingness to learn (0.3 weight)

Return ONLY a decimal number between 0.0 and 1.0, like: 0.75"""
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a career matching expert. Return only a decimal number between 0.0 and 1.0."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=10
        )
        
        score_text = response.choices[0].message.content.strip()
        score = float(score_text)
        return max(0.0, min(1.0, score))
    except Exception as e:
        print(f"AI scoring error: {e}")
        return basic_skill_match(user_background, user_skills, business_title, business_industries)


def basic_skill_match(background: str, skills: List[str], title: str, industries: List[str]) -> float:
    """Fallback keyword-based skill matching"""
    background_lower = background.lower() if background else ''
    title_lower = title.lower() if title else ''
    industries_lower = [ind.lower() for ind in industries] if industries else []
    skills_lower = [skill.lower() for skill in skills] if skills else []
    
    matches = 0
    
    for ind in industries_lower:
        if ind in background_lower:
            matches += 1
    
    for skill in skills_lower:
        if skill in title_lower or any(skill in ind for ind in industries_lower):
            matches += 1
    
    title_words = title_lower.split()
    for word in title_words:
        if len(word) > 4 and word in background_lower:
            matches += 0.5
    
    return min(1.0, matches * 0.25)


def score_schedule_fit(user_schedule: str, business_industries: List[str]) -> float:
    """Score based on schedule compatibility"""
    if not business_industries:
        return 0.7
    
    weekend_businesses = ['Events', 'Event Planning', 'Street Vending', 'Hospitality']
    flexible_businesses = ['E-Commerce', 'Print-on-Demand', 'Technology', 'Online Services']
    weekday_businesses = ['B2B Services', 'Automotive', 'Consulting']
    
    if user_schedule == 'flexible':
        return 1.0
    elif user_schedule == 'weekends':
        return 0.9 if any(ind in weekend_businesses for ind in business_industries) else 0.5
    elif user_schedule == 'weekdays':
        return 0.9 if any(ind in weekday_businesses for ind in business_industries) else 0.6
    elif user_schedule == 'evenings':
        return 0.8 if any(ind in flexible_businesses for ind in business_industries) else 0.5
    elif user_schedule == 'early':
        return 0.7
    
    return 0.6


def score_risk_tolerance(user_risk: str, business_profit_str: str, business_cost_str: str) -> float:
    """Score based on risk alignment"""
    min_profit, max_profit = parse_cost_range(business_profit_str)
    min_cost, max_cost = parse_cost_range(business_cost_str)
    
    if min_profit == 0 or min_cost == 0:
        return 0.6
    
    avg_cost = (min_cost + max_cost) / 2
    avg_profit = (min_profit + max_profit) / 2
    
    months_to_break_even = avg_cost / avg_profit if avg_profit > 0 else 12
    
    if months_to_break_even <= 1:
        business_risk = 'low'
    elif months_to_break_even <= 3:
        business_risk = 'moderate'
    elif months_to_break_even <= 6:
        business_risk = 'high'
    else:
        business_risk = 'very_high'
    
    risk_levels = ['very_low', 'low', 'moderate', 'high', 'very_high']
    
    try:
        user_level = risk_levels.index(user_risk)
    except ValueError:
        user_level = 2
    
    try:
        business_level = risk_levels.index(business_risk)
    except ValueError:
        business_level = 2
    
    diff = abs(user_level - business_level)
    
    if diff == 0:
        return 1.0
    elif diff == 1:
        return 0.7
    elif diff == 2:
        return 0.4
    else:
        return 0.2


def score_tech_comfort(user_tech: str, business_industries: List[str], business_title: str) -> float:
    """Score based on technology requirements"""
    if not business_industries:
        return 0.7
    
    high_tech = ['E-Commerce', 'Technology', 'Print-on-Demand', 'Digital Services', 'AI']
    moderate_tech = ['Marketing', 'Retail', 'Hospitality', 'Consulting']
    low_tech = ['Street Vending', 'Food & Beverage', 'Physical Services', 'Cleaning']
    
    if any(ind in high_tech for ind in business_industries):
        business_tech_level = 3
    elif any(ind in moderate_tech for ind in business_industries):
        business_tech_level = 2
    elif any(ind in low_tech for ind in business_industries):
        business_tech_level = 1
    else:
        business_tech_level = 2
    
    user_tech_map = {'very': 3, 'moderate': 2, 'minimal': 1, 'none': 0}
    user_tech_level = user_tech_map.get(user_tech, 2)
    
    diff = abs(user_tech_level - business_tech_level)
    
    if diff == 0:
        return 1.0
    elif diff == 1:
        return 0.7
    elif diff == 2:
        return 0.4
    else:
        return 0.1


def score_task_preference(user_preference: str, business_industries: List[str],
                          business_description: str) -> float:
    """Score based on task type preferences"""
    if not business_industries:
        return 0.7
    
    if user_preference == 'creative':
        preferred = ['E-Commerce', 'Marketing', 'Apparel', 'Technology', 'Design', 'Content']
    elif user_preference == 'structured':
        preferred = ['B2B Services', 'Automotive', 'Maintenance', 'Cleaning', 'Bookkeeping']
    elif user_preference == 'analytical':
        preferred = ['Technology', 'Retail', 'E-Commerce', 'Data', 'Consulting']
    elif user_preference == 'social':
        preferred = ['Events', 'Hospitality', 'Street Vending', 'Sales', 'Coaching']
    else:
        return 0.8
    
    match_count = sum(1 for ind in business_industries if ind in preferred)
    
    if match_count >= 2:
        return 1.0
    elif match_count == 1:
        return 0.7
    else:
        return 0.4


def check_avoidance_criteria(user_avoidances: List[str], business_industries: List[str],
                             business_title: str, business_description: str) -> bool:
    """Check if business conflicts with what user wants to avoid"""
    if not user_avoidances or 'none' in user_avoidances:
        return True
    
    avoidance_map = {
        'door': ['Sales', 'Door-to-Door', 'door-to-door', 'canvassing'],
        'heavy': ['Physical Services', 'Heavy Labor', 'Construction', 'Moving', 'labor'],
        'nights': ['Street Vending', 'Events', 'late night', 'nightclub'],
        'delivery': ['Delivery', 'Mobile Services', 'courier', 'food delivery'],
        'children': ['Child Care', 'Education', 'Kids', 'Tutoring', 'children']
    }
    
    combined_text = ' '.join(business_industries).lower() + ' ' + business_title.lower()
    if business_description:
        combined_text += ' ' + business_description[:200].lower()
    
    for avoidance in user_avoidances:
        conflicting_terms = avoidance_map.get(avoidance, [])
        for term in conflicting_terms:
            if term.lower() in combined_text:
                return False
    
    return True


def calculate_business_score(user_data: Dict, business: Dict, use_ai: bool = True) -> Dict[str, Any]:
    """Calculate comprehensive score for a business"""
    
    user_hours = user_data.get('weekly_hours', 1)
    user_budget = user_data.get('investment_budget', 0)
    user_schedule = user_data.get('work_schedule', 'flexible')
    user_risk = user_data.get('risk_tolerance', 'moderate')
    user_tech = user_data.get('tech_comfort', 'moderate')
    user_background = user_data.get('background', '')
    user_skills = user_data.get('skills', [])
    user_task_pref = user_data.get('task_preference', 'mixed')
    user_avoidances = user_data.get('avoidances', [])
    willing_to_learn = user_data.get('willing_to_learn', 'possible')
    
    business_cost = business.get('startup_cost', '$0')
    business_profit = business.get('estimated_monthly_profit', '$0')
    business_level = business.get('skill_level', 'Intermediate')
    business_industries = business.get('industry', []) if business.get('industry') else []
    business_title = business.get('title', '')
    business_description = business.get('description', '')
    
    if not check_avoidance_criteria(user_avoidances, business_industries, business_title, business_description):
        return {
            'business_id': str(business.get('id')),
            'business_title': business_title,
            'total_score': 0.0,
            'match_reason': 'Conflicts with user preferences',
            'breakdown': {},
            'estimated_profit': business_profit,
            'startup_cost': business_cost,
            'thumbnail_url': business.get('thumbnail_url'),
            'video_link': business.get('video_link'),
            'summary': business.get('summary')
        }
    
    scores = {
        'startup_cost': score_startup_cost(user_budget, business_cost),
        'time_commitment': score_time_commitment(user_hours, business_level),
        'skill_match': score_skill_match_ai(user_background, user_skills, 
                                           business_industries, business_title, 
                                           business_description, willing_to_learn) if use_ai 
                       else basic_skill_match(user_background, user_skills, business_title, business_industries),
        'schedule_fit': score_schedule_fit(user_schedule, business_industries),
        'risk_tolerance': score_risk_tolerance(user_risk, business_profit, business_cost),
        'tech_comfort': score_tech_comfort(user_tech, business_industries, business_title),
        'task_preference': score_task_preference(user_task_pref, business_industries, 
                                                 business_description)
    }
    
    total_score = sum(scores[key] * WEIGHTS[key] for key in scores)
    
    top_factors = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    strong_matches = [f[0].replace('_', ' ') for f in top_factors if f[1] > 0.7]
    match_reason = f"Strong match in: {', '.join(strong_matches)}" if strong_matches else "Moderate fit overall"
    
    return {
        'business_id': str(business.get('id')),
        'business_title': business_title,
        'total_score': round(total_score, 3),
        'match_reason': match_reason,
        'breakdown': {k: round(v, 2) for k, v in scores.items()},
        'estimated_profit': business_profit,
        'startup_cost': business_cost,
        'thumbnail_url': business.get('thumbnail_url'),
        'video_link': business.get('video_link'),
        'summary': business.get('summary')
    }


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""
    
    def _set_cors_headers(self):
        """Set CORS headers for cross-origin requests"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '3600')
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests - returns API status and usage info"""
        self.send_response(200)
        self._set_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        env_ok = bool(supabase_url and supabase_key and openai.api_key)
        response = {
            'status': 'running',
            'endpoint': '/api/recommend',
            'method': 'POST',
            'env_configured': env_ok,
            'usage': {
                'method': 'POST',
                'body': {
                    'user_id': '(required) UUID of user with quiz responses',
                    'limit': '(optional) max recommendations, default 10',
                    'min_score': '(optional) minimum match score 0-1, default 0.3',
                    'use_ai': '(optional) use AI skill matching, default true'
                }
            }
        }
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            request_data = json.loads(body.decode('utf-8'))
            
            if 'user_id' not in request_data:
                self.send_response(400)
                self._set_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'user_id required'}).encode())
                return
            
            user_id = request_data['user_id']
            limit = request_data.get('limit', 10)
            min_score = request_data.get('min_score', 0.3)
            use_ai = request_data.get('use_ai', True)
            
            # Get user quiz data from Supabase
            sb = get_supabase()
            user_response = sb.table('users').select('quiz_responses').eq('id', user_id).execute()
            
            if not user_response.data or len(user_response.data) == 0:
                self.send_response(404)
                self._set_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'User not found'}).encode())
                return
            
            user_data = user_response.data[0].get('quiz_responses', {})
            
            # Get all published businesses from Supabase
            businesses_response = sb.table('blueprints').select('*').eq('published', True).execute()
            
            if not businesses_response.data:
                self.send_response(404)
                self._set_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No businesses found'}).encode())
                return
            
            businesses = businesses_response.data
            
            # Score all businesses
            scored_businesses = []
            for business in businesses:
                score_data = calculate_business_score(user_data, business, use_ai=use_ai)
                if score_data['total_score'] >= min_score:
                    scored_businesses.append(score_data)
            
            # Sort by score and limit
            scored_businesses.sort(key=lambda x: x['total_score'], reverse=True)
            recommendations = scored_businesses[:limit]
            
            # Cache results in Supabase
            cache_data = {
                'user_id': user_id,
                'recommendations': recommendations,
                'total_analyzed': len(businesses),
                'updated_at': 'now()'
            }
            
            try:
                sb.table('recommendations_cache').upsert(cache_data, on_conflict='user_id').execute()
            except Exception as cache_error:
                print(f"Cache error (non-critical): {cache_error}")
            
            # Send success response
            response_data = {
                'success': True,
                'user_id': user_id,
                'recommendations': recommendations,
                'total_analyzed': len(businesses),
                'total_matches': len(recommendations)
            }
            
            self.send_response(200)
            self._set_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            self.send_response(500)
            self._set_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
