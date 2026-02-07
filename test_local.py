"""
Standalone Local Testing Utility for Recommendation Engine
Tests the scoring algorithm without needing Supabase or OpenAI API calls
NOTE: This version copies the scoring functions to avoid Supabase initialization
"""

import json


# ===== COPIED SCORING FUNCTIONS FROM recommendation_engine.py =====

def parse_cost_range(cost_str: str):
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
    """Score based on time availability"""
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


def basic_skill_match(background: str, skills: list, title: str, industries: list) -> float:
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


def score_schedule_fit(user_schedule: str, business_industries: list) -> float:
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


def score_tech_comfort(user_tech: str, business_industries: list, business_title: str) -> float:
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


def score_task_preference(user_preference: str, business_industries: list, business_description: str) -> float:
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


def check_avoidance_criteria(user_avoidances: list, business_industries: list,
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


def calculate_business_score(user_data: dict, business: dict) -> dict:
    """Calculate comprehensive score for a business"""
    WEIGHTS = {
        'startup_cost': 0.25,
        'time_commitment': 0.20,
        'skill_match': 0.20,
        'schedule_fit': 0.10,
        'risk_tolerance': 0.10,
        'tech_comfort': 0.08,
        'task_preference': 0.07
    }
    
    user_hours = user_data.get('weekly_hours', 1)
    user_budget = user_data.get('investment_budget', 0)
    user_schedule = user_data.get('work_schedule', 'flexible')
    user_risk = user_data.get('risk_tolerance', 'moderate')
    user_tech = user_data.get('tech_comfort', 'moderate')
    user_background = user_data.get('background', '')
    user_skills = user_data.get('skills', [])
    user_task_pref = user_data.get('task_preference', 'mixed')
    user_avoidances = user_data.get('avoidances', [])
    
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
            'startup_cost': business_cost
        }
    
    scores = {
        'startup_cost': score_startup_cost(user_budget, business_cost),
        'time_commitment': score_time_commitment(user_hours, business_level),
        'skill_match': basic_skill_match(user_background, user_skills, business_title, business_industries),
        'schedule_fit': score_schedule_fit(user_schedule, business_industries),
        'risk_tolerance': score_risk_tolerance(user_risk, business_profit, business_cost),
        'tech_comfort': score_tech_comfort(user_tech, business_industries, business_title),
        'task_preference': score_task_preference(user_task_pref, business_industries, business_description)
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
        'breakdown ': {k: round(v, 2) for k, v in scores.items()},
        'estimated_profit': business_profit,
        'startup_cost': business_cost
    }


# ===== TEST SUITE =====

def test_scoring_algorithm():
    """Test the recommendation engine with various user profiles and businesses"""
    
    print("=" * 60)
    print("RECOMMENDATION ENGINE - LOCAL TESTING")
    print("=" * 60)
    print()
    
    # Test Case 1: Tech-savvy developer with good budget
    print("📊 TEST CASE 1: Tech-savvy developer")
    print("-" * 60)
    
    user1 = {
        'weekly_hours': 2,  # 20 hours/week
        'investment_budget': 1500,
        'work_schedule': 'flexible',
        'risk_tolerance': 'moderate',
        'tech_comfort': 'very',
        'background': 'Software developer with 5 years experience in web development',
        'skills': ['web_development', 'programming', 'javascript'],
        'task_preference': 'creative',
        'avoidances': ['heavy', 'delivery'],
        'willing_to_learn': 'yes'
    }
    
    business1 = {
        'id': 'test-1',
        'title': 'AI-Powered T-Shirt Business',
        'startup_cost': '$100–$500',
        'estimated_monthly_profit': '$1,000–$10,000',
        'skill_level': 'Beginner',
        'industry': ['E-Commerce', 'Apparel', 'Print-on-Demand', 'Technology'],
        'description': 'Use AI tools like MidJourney to design unique T-shirts and sell them online through print-on-demand services like Printful.'
    }
    
    result1 = calculate_business_score(user1, business1)
    print_result(result1)
    
    # Test Case 2: Low budget, minimal tech skills
    print("\n📊 TEST CASE 2: Low budget beginner")
    print("-" * 60)
    
    user2 = {
        'weekly_hours': 0,  # 5 hours/week
        'investment_budget': 0,
        'work_schedule': 'weekends',
        'risk_tolerance': 'very_low',
        'tech_comfort': 'minimal',
        'background': 'Looking for simple side income, no special skills',
        'skills': [],
        'task_preference': 'structured',
        'avoidances': ['door', 'nights'],
        'willing_to_learn': 'possible'
    }
    
    business2 = {
        'id': 'test-2',
        'title': 'Weekend Farmers Market Stand',
        'startup_cost': '$50–$200',
        'estimated_monthly_profit': '$500–$2,000',
        'skill_level': 'Beginner',
        'industry': ['Street Vending', 'Food & Beverage', 'Retail'],
        'description': 'Sell homemade goods or resell products at weekend farmers markets.'
    }
    
    result2 = calculate_business_score(user2, business2)
    print_result(result2)
    
    # Test Case 3: Should be filtered out (avoidance match)
    print("\n📊 TEST CASE 3: Avoidance filter test")
    print("-" * 60)
    
    user3 = {
        'weekly_hours': 2,
        'investment_budget': 500,
        'work_schedule': 'flexible',
        'risk_tolerance': 'moderate',
        'tech_comfort': 'moderate',
        'background': 'Various skills',
        'skills': ['driving'],
        'task_preference': 'mixed',
        'avoidances': ['delivery', 'heavy'],
        'willing_to_learn': 'yes'
    }
    
    business3 = {
        'id': 'test-3',
        'title': 'Food Delivery Driver',
        'startup_cost': '$200–$500',
        'estimated_monthly_profit': '$2,000–$5,000',
        'skill_level': 'Beginner',
        'industry': ['Delivery', 'Food & Beverage', 'Mobile Services'],
        'description': 'Deliver food for DoorDash, Uber Eats, or similar platforms.'
    }
    
    result3 = calculate_business_score(user3, business3)
    print_result(result3)
    
    # Test individual scoring functions
    print("\n" + "=" * 60)
    print("INDIVIDUAL SCORING TESTS")
    print("=" * 60)
    
    print("\n💰 Startup Cost Scoring:")
    print(f"  Budget $1,500 vs Cost '$100–$500': {score_startup_cost(1500, '$100–$500'):.2f}")
    print(f"  Budget $500 vs Cost '$1,000–$3,000': {score_startup_cost(500, '$1,000–$3,000'):.2f}")
    print(f"  Budget $0 vs Cost '$0': {score_startup_cost(0, '$0'):.2f}")
    
    print("\n⏰ Time Commitment Scoring:")
    print(f"  20hrs/week (user=2) vs Beginner (10hrs): {score_time_commitment(2, 'Beginner'):.2f}")
    print(f"  5hrs/week (user=0) vs Advanced (20hrs): {score_time_commitment(0, 'Advanced'):.2f}")
    print(f"  30hrs/week (user=3) vs Intermediate (15hrs): {score_time_commitment(3, 'Intermediate'):.2f}")
    
    print("\n📅 Schedule Fit Scoring:")
    print(f"  Flexible user vs E-Commerce: {score_schedule_fit('flexible', ['E-Commerce']):.2f}")
    print(f"  Weekends user vs Events: {score_schedule_fit('weekends', ['Events']):.2f}")
    print(f"  Weekdays user vs Street Vending: {score_schedule_fit('weekdays', ['Street Vending']):.2f}")
    
    print("\n🎲 Risk Tolerance Scoring:")
    print(f"  Moderate risk, $500 cost, $2k profit: {score_risk_tolerance('moderate', '$2,000–$5,000', '$500–$1,000'):.2f}")
    print(f"  Low risk, $10k cost, $2k profit: {score_risk_tolerance('low', '$2,000–$5,000', '$10,000–$20,000'):.2f}")
    
    print("\n💻 Tech Comfort Scoring:")
    print(f"  Very comfortable vs Technology: {score_tech_comfort('very', ['Technology'], 'AI Tool'):.2f}")
    print(f"  Minimal vs Street Vending: {score_tech_comfort('minimal', ['Street Vending'], 'Market Stand'):.2f}")
    print(f"  None vs E-Commerce: {score_tech_comfort('none', ['E-Commerce'], 'Online Store'):.2f}")
    
    print("\n🎨 Task Preference Scoring:")
    print(f"  Creative vs E-Commerce: {score_task_preference('creative', ['E-Commerce', 'Marketing'], 'Design Shop'):.2f}")
    print(f"  Structured vs B2B Services: {score_task_preference('structured', ['B2B Services'], 'Bookkeeping'):.2f}")
    print(f"  Social vs Events: {score_task_preference('social', ['Events', 'Hospitality'], 'Party Planning'):.2f}")
    
    print("\n🚫 Avoidance Filter:")
    print(f"  Avoid delivery, business is Delivery: {check_avoidance_criteria(['delivery'], ['Delivery'], 'Food Delivery', '')}")
    print(f"  Avoid heavy, business is Tech: {check_avoidance_criteria(['heavy'], ['Technology'], 'Web App', '')}")
    print(f"  No avoidances: {check_avoidance_criteria(['none'], ['Any'], 'Anything', '')}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 60)


def print_result(result: dict):
    """Pretty print a scoring result"""
    print(f"Business: {result['business_title']}")
    print(f"Total Score: {result['total_score']:.3f} ({result['total_score']*100:.1f}%)")
    print(f"Match Reason: {result['match_reason']}")
    
    if result.get('breakdown'):
        print("\nScore Breakdown:")
        for factor, score in result['breakdown'].items():
            bar = "█" * int(score * 20)
            print(f"  {factor:20s}: {score:.2f} {bar}")
    
    print(f"\nProfit: {result['estimated_profit']}")
    print(f"Cost: {result['startup_cost']}")


if __name__ == '__main__':
    test_scoring_algorithm()
