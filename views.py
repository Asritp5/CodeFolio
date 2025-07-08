from collections import defaultdict
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from .email_utlility import send_email_CodeFolio,send_email_User,send_email_OTP    
from .db_utility import db
from argon2 import PasswordHasher
from firebase_admin import firestore
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re
import secrets
from django.urls import reverse
from .custom_classes import user
from .profile_utils import fetch_platform_data, store_verified_platform
from .utils import get_leetcode_real_name, get_gfg_full_name, get_codeforces_first_name
import random
import string
from datetime import datetime, timedelta   

def clear_session(request):
    keys=['otp' ,'otp_success','pswd_otp','pswd_otp_success','docid']
    for key in keys:
        request.session.pop(key, None)
    

def features_view(request):
    clear_session(request)
    context = {'exclude_auth_buttons': True}
    return render(request, 'features_page.html', context)

def home_view(request):
    clear_session(request)
    return render(request, 'home.html') 

def login_view(request):
    clear_session(request)
    if request.session.get('userid'): # Check if user is already logged in
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email').lower().strip()
        password = request.POST.get('password')

        users=db.collection('User').where('Email', '==',email).get()

        if not users:
            messages.error(request, 'Invalid credentials')
            return render(request, 'login.html')

        pw=PasswordHasher()
    
        user = users[0]
        stored_hashed_password = user.get('Password')

        try:
            pw.verify(stored_hashed_password, password)
            request.session.cycle_key()
            request.session['userid'] = user.id
            request.session['username'] = user.get('Name')
            request.session['email'] = user.get('Email')
            
            return redirect('profile')  # reroute to register or dashboard page
        except Exception:
            messages.error(request, 'Invalid credentials')
            return render(request, 'login.html')

    return render(request, 'login.html')

def signup_view(request):
    
    #clear only reset_pswd sessions
    keys=['pswd_otp','pswd_otp_success','docid']
    for key in keys:
        request.session.pop(key, None)
    
    if request.session.get('userid'): # Check if user is already logged in
        return redirect('home')
    
    if request.method == 'POST':
        if not request.session.get('otp'):
            username = request.POST.get('username')

            if username:
                username = username.strip().title()

            email = request.POST.get('email')

            if email:
                email = email.strip().lower()
        
            users=db.collection('User').where('Email', '==', email).get()

            if users:
                messages.error(request, 'Email already exists.Try logging in')
                return render(request, 'signup.html')
            
            users=db.collection('User').where('Name', '==', username).get()

            if users:
                messages.error(request, 'Username already exists.Try a different username')
                return render(request, 'signup.html')
            
            #checks if mail is valid and exists
            no_exception,otp=send_email_OTP(username, email,"OTP for CodeFolio Registration")
            if not no_exception:
                messages.error(request, 'Failed to send OTP. Please try again later.')
                return render(request, 'signup.html')
            
            request.session['otp'] =otp
            request.session['email'] = email
            request.session['username'] = username

        else:
            if not request.session.get('otp_success'):
                if request.POST.get('otp')!=request.session.get('otp'):
                    messages.error(request, 'Invalid OTP')
                    return render(request, 'signup.html')
                # OTP verification successful, proceed with registration
                request.session['otp_success'] =True
            else:

                password1 = request.POST.get('password1')
                password2 = request.POST.get('password2')
                
                if password1:
                    password1 = password1.strip()
                if password2:
                    password2 = password2.strip()    

                if password1 != password2:
                    messages.error(request, 'Passwords do not match')
                    return render(request, 'signup.html')
                
                try:
                    validate_password(password1, user=None)  
                    if not re.search(r'\d', password1):
                        raise ValidationError(("Password must contain at least one digit."),\
                                              code='password_no_number',)
                    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\'\\:"|<>,./?]', password1):
                        raise ValidationError(("Password must contain at least one special character."),\
                code='password_no_special',)
            
                except ValidationError as e:
                    for error in e.messages:
                        messages.error(request, error)
                    return render(request, 'signup.html')
                    
                profile_visibility = request.POST.get('profile_visibility')
        
                
                pw=PasswordHasher()
                hashed_password = pw.hash(password1)
                
                #  proceed with registration
                
                user={
                    'Name': request.session.get('username'),
                    'Email': request.session.get('email'),
                    'Registered': False,    # This field is for profile information of platforms
                    'Profile_Visibility':profile_visibility,
                    'Profile_list': [],
                    'Created': firestore.SERVER_TIMESTAMP,
                    'Last_Updated': firestore.SERVER_TIMESTAMP,
                    'Password': hashed_password,
                    'Current_Streak':0,
                    'Max_Streak':0
                    }
                
                timestamp,doc = db.collection('User').add(user)
                old_username=request.session.get('username')
                old_email=request.session.get('email')
                request.session.cycle_key() #prevent session fixation attacks
                request.session['userid'] = doc.id
                request.session['username'] = old_username
                request.session['email'] = old_email
                

                
                keys=['otp' ,'otp_success']
                for key in keys:
                    request.session.pop(key, None)
                messages.success(request,"Register your details")    
                return redirect('profile') # Redirect to the register page
        
    return render(request, 'signup.html')

def contact_view(request):
    clear_session(request)
    if request.method == 'POST':
        if request.session.get('userid'): # Check if user is already logged in
            name = request.session.get('username')
            email = request.session.get('email')
        else:
            name = request.POST.get('name')
            if name:
                name = name.strip().title()
            email = request.POST.get('email')
            if email:
                email = email.strip().lower()
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        
        email_sent = send_email_CodeFolio(name, email, subject, message)

        if not email_sent:
            messages.error(request, 'Failed to send email. Please try again later.')
            return render(request, 'contact.html')
        
        email_sent_user=send_email_User(name, email, subject)
        if email_sent_user:
            messages.success(request, 'Your message has been sent!')
        else:
            messages.success(request, 'Our team will get back to you soon.') #mail already sent to CodeFolio but not to user

    return render(request, 'contact.html')


def logout_view(request):
    clear_session(request)
    if not request.session.get('userid'): # Check if user is not logged in
        messages.error(request, 'You are not logged in')
        return redirect('login')
    
    keys=['userid' ,'username','email']
    for key in keys:
        request.session.pop(key, None)
    return redirect('home')  # Redirect to the home page after logout

#---------------------- profile or home-------------------------------------

def profile_view(request):
    """Display the user's profile and verification status for each platform."""
    clear_session(request)
    if not request.session.get('userid'):
        messages.error(request,"Login first to view your profile.")
        return redirect('login')

    
    user_id = request.session['userid']
    profile_url=request.build_absolute_uri(reverse('dashboard', args=[user_id]))
    user_doc = db.collection('User').document(user_id).get()
    if not user_doc.exists:
        messages.error(request,"Invalid access.")
        return redirect('login')

    user_data = user_doc.to_dict()
    profile_list = user_data.get('Profile_list', [])
    default_platforms = ["leetcode", "gfg", "codeforces"]

    # Map platform names to their profile entries
    platforms = {p['name']: p for p in profile_list}

    display_platforms = []
    for name in default_platforms:
        entry = platforms.get(name, {})
        display_platforms.append({
            'name': name,
            'username': entry.get('username', ''),
            'verified': entry.get('verified', False)
        })

    # Retrieve and clear verification session variables
    verification_code = request.session.pop('verification_code', None)
    platform_name = request.session.pop('platform_name', None)
    entered_username = request.session.pop('entered_username', '')

    visibility = user_data.get('Profile_Visibility', 'private')

    return render(request, 'profile.html', {
        'platforms': display_platforms,
        'visibility': visibility,
        'verification_code': verification_code,
        'platform_name': platform_name,
        'entered_username': entered_username,
        'profile_url':profile_url,
    })


PLATFORM_CONFIG = {
    'leetcode': {
        'fetch_name': get_leetcode_real_name,
        'session_code_key': 'verification_code_leetcode',
        'display_name': 'LeetCode',
        'code_prefix': 'LC'
    },
    'gfg': {
        'fetch_name': get_gfg_full_name,
        'session_code_key': 'verification_code_gfg',
        'display_name': 'GFG',
        'code_prefix': 'GFG'
    },
    'codeforces': {
        'fetch_name': get_codeforces_first_name,
        'session_code_key': 'verification_code_codeforces',
        'display_name': 'Codeforces',
        'code_prefix': 'CF'
    }
}

def generate_verification_code(length=10):
    chars = string.ascii_uppercase
    return ''.join(random.choices(chars, k=length))

def verify_platform(request, platform_name):
    clear_session(request)
    if platform_name not in PLATFORM_CONFIG:
        messages.error(request, "Invalid platform.")
        return redirect('profile')

    if not request.session.get('userid'):
        messages.error(request,"Login first to register your details.")
        return redirect('login')

    user_id = request.session['userid']
    user_ref = db.collection('User').document(user_id)

    config = PLATFORM_CONFIG[platform_name]
    fetch_name_func = config['fetch_name']
    session_code_key = config['session_code_key']

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        all_users = db.collection('User').get()
        for user in all_users:
            if user.id == user_id:
                continue  # Skip current user
            profile_list = user.to_dict().get('Profile_list', [])
            for p in profile_list:
                if p.get('name') == platform_name and p.get('username') == username:
                    messages.error(
                        request,
                        f"The username '{username}' is already registered on {platform_name.title()} by another user."
                    )
                    return redirect('profile')
        code_entered = request.POST.get('verification_code', '').strip()
        expected_code = request.session.get(session_code_key)

        # Step 2: User submits the code for verification
        if expected_code and code_entered:
            if code_entered != expected_code:
                messages.error(request, "Verification code incorrect.")
                return redirect('profile')

            profile_name = fetch_name_func(username)
            if profile_name and expected_code == profile_name.strip():
                performance = fetch_platform_data(platform_name, username)
                
                if performance:  # Always check if performance data is valid before storing
                    store_verified_platform(user_id, platform_name, username, performance)
                    user_ref = db.collection('User').document(user_id)
                    user_doc = user_ref.get()
                    profile_list = user_doc.to_dict().get('Profile_list', [])
                    registered = bool(profile_list)  # True if at least one platform
                    user_ref.update({'Registered': registered})
                    
                    request.session.pop(session_code_key, None)
                    
                    messages.success(request, f"{config['display_name']} verified successfully!")
                else:
                    messages.error(request, f"Failed to verify {config['display_name']}. Invalid or unreachable profile.")

                return redirect('profile')


            else:
                messages.error(request, f"Verification code not found in your {config['display_name']} profile. Please paste the code exactly and try again.")
            return redirect('profile')

        # Step 1: Generate and provide verification code
        code = generate_verification_code(10)
        request.session[session_code_key] = code
        request.session['platform_name'] = platform_name
        request.session['entered_username'] = username
        request.session['verification_code'] = code
        messages.info(request, f"Verification code generated for {config['display_name']}. Please paste it in your profile and click 'I’ve Added the Code – Verify Now'.")
        return redirect('profile')

def update_visibility(request):
    clear_session(request)
    if not request.session.get('userid'):
        messages.error(request,"Login first to update your profile details.")
        return redirect('login')

    if request.method == 'POST':
        visibility = request.POST.get('profile_visibility', 'private')
        user_id = request.session['userid']
        db.collection('User').document(user_id).update({
            'Profile_Visibility': visibility,
            'Last_Updated': firestore.SERVER_TIMESTAMP,
        })
    messages.success(request,"Updated profile visibility")
    return redirect('profile')


def update_username(request):
    clear_session(request)
    if not request.session.get('userid'):
        messages.error(request,"Login first to  update your profile.")
        return redirect('login')

    if request.method == 'POST':
        username = request.POST.get('username')
        username=username.strip().title()
        
        if username=='':
            messages.error(request, 'Username can\'t be blank')
            return render(request, 'profile.html')
        
        if username!=request.session.get('username'):
            users=db.collection('User').where('Name', '==', username).get()

            if users:
                messages.error(request, 'Username already exists.Try a different username')
                return render(request, 'profile.html')
    
            user_id = request.session['userid']
            db.collection('User').document(user_id).update({
                'Name': username,
                'Last_Updated': firestore.SERVER_TIMESTAMP,
            })
            request.session['username']=username
            messages.success(request,"Updated username")

    return redirect('profile')

def delete_platform(request, platform_name):
    clear_session(request)
    if not request.session.get('userid'):
        messages.error(request,"Login first to update your profile.")
        return redirect('login')

    if request.method == 'POST':
        user_id = request.session['userid']
        user_ref = db.collection('User').document(user_id)
        user_doc = user_ref.get()

        profile_list = user_doc.to_dict().get('Profile_list', [])
        updated_list = [p for p in profile_list if p['name'] != platform_name]

        user_ref.update({
            'Profile_list': updated_list,
            f"profileList.{platform_name}": firestore.DELETE_FIELD,
            'Last_Updated': firestore.SERVER_TIMESTAMP
        })

        user_ref.collection('performance').document(platform_name).delete()
        registered = bool(updated_list)  # True if at least one platform remains
        user_ref.update({'Registered': registered})
        messages.success(request, f"{platform_name.title()} removed.")
        return redirect('profile')

#---------------------------------------#############----------------------------------------------#
def about_view(request):
    clear_session(request)
    return render(request, 'about.html')  # Render the about page

def terms_view(request):
    clear_session(request)
    return render(request, 'terms.html')  # Render the terms and conditions page

def error_view(request,exception):
    clear_session(request)
    return render(request, '404.html')  # Render the 404 error page

def reset_password_view(request):

    #clear only signup related sessions
    keys=['otp' ,'otp_success']
    for key in keys:
        request.session.pop(key, None)

    if request.session.get('userid'): # Check if user is already logged in
        messages.error(request, 'You are already logged in')
        return redirect('home')
    
    if request.method == 'POST':
        if not request.session.get('pswd_otp'):
            email = request.POST.get('email')
            if email:
                email = email.strip().lower()
        
            users=db.collection('User').where('Email', '==', email).get()

            if not users:
                messages.error(request, 'Invalid credentials')
                return render(request, 'resetPassword.html')
            
            username=users[0].get('Name')
                    
            no_exception,otp=send_email_OTP(username, email,"OTP for CodeFolio password reset")
            if not no_exception:
                messages.error(request, 'Failed to send OTP. Please try again later.')
                return render(request, 'resetPassword.html')
            request.session['pswd_otp'] =otp
            request.session['docid'] = users[0].id
        else:
            if not request.session.get('pswd_otp_success'):
                if request.POST.get('otp')==None:
                    messages.error(request, 'Please enter the OTP')
                    return render(request, 'resetPassword.html')
                
                if request.POST.get('otp')!=request.session.get('pswd_otp'):
                    messages.error(request, 'Invalid OTP')
                    return render(request, 'resetPassword.html')
                
                # OTP verification successful, proceed with password reset
                request.session['pswd_otp_success'] =True
            else:

                password1 = request.POST.get('password1')
                password2 = request.POST.get('password2')
                
                if password1:
                    password1 = password1.strip()
                if password2:
                    password2 = password2.strip()    

                if password1 != password2:
                    messages.error(request, 'Passwords do not match')
                    return render(request, 'resetPassword.html')
                
                try:
                    validate_password(password1, user=None)  
                    if not re.search(r'\d', password1):
                        raise ValidationError(("Password must contain at least one digit."),\
                                              code='password_no_number',)
                    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\'\\:"|<>,./?]', password1):
                        raise ValidationError(("Password must contain at least one special character."),\
                code='password_no_special',)
            
                except ValidationError as e:
                    for error in e.messages:
                        messages.error(request, error)
                    return render(request, 'resetPassword.html')
                
                pw=PasswordHasher()
                hashed_password = pw.hash(password1)
                
                user={
                    'Last_Updated': firestore.SERVER_TIMESTAMP,
                    'Password': hashed_password,
                    }
                
                user_id = request.session.get('docid')
                db.collection('User').document(user_id).update(user)
                  
                keys=['pswd_otp' ,'pswd_otp_success','docid']
                for key in keys:
                    request.session.pop(key, None)

                messages.success(request, 'Password reset successfully. Please log in with your new password.')
                return redirect('login')
    return render(request, 'resetPassword.html')

def search(request):
    clear_session(request)
    if not request.session.get('userid'):
        messages.error(request,"Please login first to search profiles")
        return redirect('login')
    
    context={}
    reqd_users=None
    
    if request.method=="POST":
        key=request.POST.get('search')
        key=key.strip().lower()
        if key:
            reqd_users=get_data(key)
        else:
            messages.error(request,"Please enter a value to search")
            return render(request,'search.html')    

        if not reqd_users:
            messages.error(request,"No users found")
            return render(request,'search.html')    

    context['reqd_users']=reqd_users
    return render(request,'search.html',context)

def get_data(key):
    users=db.collection('User').get()
    users_list=[]
    if users:
        for user1 in users:
            user_doc=user1.to_dict()
            name=user_doc.get('Name').lower()
            email=user_doc.get('Email')
            if key in name or key in email:
                if user_doc.get('Registered'):
                    if user_doc.get('Profile_Visibility')=='public':
                        user_id=user1.id
                    else:
                        user_id=None
                    rqd_user=user(name,user_id)
                    users_list.append(rqd_user)           
        return users_list                
    else:
        return None
    
def delete_user(request,id):
    clear_session(request)
    if not request.session.get('userid'): # Check if user is not logged in
        messages.error(request, 'You are not logged in')
        return redirect('login')
        
    if not id:
        messages.error(request,"User not found")
        return render(request,"profile.html")
    
    if request.session.get('userid') != id:
        messages.error(request, "Unauthorized action")
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    
    user_ref = db.collection('User').document(id)
    user_doc=user_ref.get()
    
    if not user_doc.exists:
        messages.error(request,"User not found")
        return render(request,'profile.html')
    
    user_doc=user_doc.to_dict()
    
    if request.method=='POST':
        name=request.POST.get('username')
        name=name.strip().lower()

        if name=='':
            messages.error(request,"Enter username")
            return render(request,'delete_account.html')
        
        actual_username=user_doc.get('Name').lower()

        if name!=actual_username:
            messages.error(request,"Username does not match!")
            return render(request,'delete_account.html')
        
        if user_doc.get("Registered")==True:
            perf_collection = user_ref.collection('performance').get()
            for perf_doc in perf_collection:
                perf_doc.reference.delete()
        
        user_ref.delete()
        messages.success(request,"Account Deleted")
        return redirect('logout')
    
    return render(request,'delete_account.html')

def retrieve_user_data_from_firestore(user_id):
    user_ref = db.collection("User").document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return None, None, True

    user_data = user_doc.to_dict()
    profile_list = user_data.get("Profile_list", [])

    performance_data = {}
    fetch_failed = False

    for entry in profile_list:
        platform = entry.get("name")
        username = entry.get("username")
        if not platform or not username:
            continue
        try:
            perf = fetch_platform_data(platform, username)
            performance_data[platform] = perf
        except Exception as e:
            #print(f"Error fetching data for {platform}: {e}")
            fetch_failed = True
            continue

    return user_data, performance_data, fetch_failed

def process_user_data( performance_data):
    profile_data = {
        "leetcode": performance_data.get("leetcode", {}),
        "gfg": performance_data.get("gfg", {}),
        "codeforces": performance_data.get("codeforces", {}),
    }

    activity_agg = defaultdict(int)
    heatmap_calendar = defaultdict(int)
    badges = []
    leetcode_username = ""

    platforms_per_day = defaultdict(list)

    for platform, perf in profile_data.items():
        cal = {}
        if platform == "leetcode":
            leetcode_username = perf.get("username", "")
            cal = perf.get('calendar', {}).get('submissionCalendar', {})
            badges.extend(perf.get("badges", []))
        elif platform == "gfg":
            cal = perf.get("calendar", {})
        elif platform == "codeforces":
            for upd in perf.get("rating_history", []):
                date_key = datetime.fromtimestamp(
                    upd.get("ratingUpdateTimeSeconds", 0)
                ).strftime("%Y-%m-%d")
                cal[date_key] = 1

        for date_str, value in cal.items():
            if value is not None:
                activity_agg[date_str] += value
                heatmap_calendar[date_str] += value
                if platform not in platforms_per_day[date_str]:
                    platforms_per_day[date_str].append(platform)

    # Calculate current streak and max streak
    all_dates = sorted(activity_agg.keys())
    date_set = set(all_dates)

    current_streak = 0
    max_streak = 0
    temp_streak = 0

    today = datetime.today().date()
    day_ptr = today

    # Calculate current streak
    while True:
        day_str = day_ptr.strftime("%Y-%m-%d")
        if day_str in activity_agg:
            current_streak += 1
            day_ptr -= timedelta(days=1)
        else:
            break

    # Calculate max streak
    if date_set:
        first_date = min(date_set)
        last_date = max(date_set)
        check_date = datetime.strptime(first_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(last_date, "%Y-%m-%d").date()

        while check_date <= end_date:
            date_str = check_date.strftime("%Y-%m-%d")
            if date_str in activity_agg:
                temp_streak += 1
                max_streak = max(max_streak, temp_streak)
            else:
                temp_streak = 0
            check_date += timedelta(days=1)

    return {
        "leetcode": profile_data["leetcode"],
        "gfg": profile_data["gfg"],
        "codeforces": profile_data["codeforces"],
        "activity": dict(activity_agg),
        "badges": badges,
        "leetcode_username": leetcode_username,
        "heatmap_calendar": dict(heatmap_calendar),
        "streak": {
            "current": current_streak,
            "max": max_streak,
            "platforms_per_day": dict(platforms_per_day)
        }
    }

def dashboard_view(request,rqd_user_id):
    if not request.session.get("userid"):
        messages.error(request, "You are not logged in. Please log in to access the dashboard page.")
        return redirect("login")

    if not rqd_user_id:
        messages.error(request, "Invalid request")
        return redirect("search")
    
    user_doc = db.collection('User').document(rqd_user_id).get()
    if user_doc.exists:
        rqd_user_data = user_doc.to_dict()
        if request.session.get('userid')!=rqd_user_id and rqd_user_data.get("Profile_Visibility")=='private':
            messages.error(request, "Profile marked as private can\'t access data.")
            return redirect("search")
    else:
        messages.error(request, "Invalid access request.User does not exist.")
        return redirect("search")
    
    user_data, performance_data, fetch_failed = retrieve_user_data_from_firestore(rqd_user_id)
    if not fetch_failed:
    # ✅ Store new data per platform using your existing function
        for platform, data in performance_data.items():
            username = data.get("username")
            if username:
                store_verified_platform(rqd_user_id, platform, username, data)
    else:
        # ⚠️ Fetch failed – fallback to cached data
        performance_data = {}
        for entry in user_data.get("Profile_list", []):
            platform = entry.get("name")
            if not platform:
                continue
            cached_doc = (
                db.collection("User")
                .document(rqd_user_id)
                .collection("performance")
                .document(platform)
                .get()
            )
            if cached_doc.exists:
                performance_data[platform] = cached_doc.to_dict()
    if not user_data:
        messages.error(request, "Invalid request! User data not found")
        return redirect("login")

    if not performance_data:
        messages.error(request, "No cached performance data found.")
        return redirect("profile")
    
    if not user_data.get("Registered", False):
        messages.error(request, "User did not register any platform data.")   
        return redirect("profile")

    processed_data = process_user_data( performance_data)
    #print("current:", processed_data["streak"]["current"])
    context = {
        "name":user_data.get('Name'),
        "email": user_data.get('Email'),
        "is_latest": not fetch_failed,
        "current_streak": processed_data["streak"]["current"],
        "max_streak": processed_data["streak"]["max"],
        "platforms_per_day": json.dumps(processed_data["streak"]["platforms_per_day"]),
        "heatmap_json": json.dumps(processed_data["activity"]),
        "codeforces": json.dumps(processed_data["codeforces"]),
        "leetcode": json.dumps(processed_data["leetcode"]),
        "gfg": json.dumps(processed_data["gfg"]),
        "leetcode_username": processed_data["leetcode_username"],
        "badges": processed_data["badges"],
        "has_codeforces": bool(processed_data["codeforces"]),
        "has_leetcode": bool(processed_data["leetcode"]),
        "has_gfg": bool(processed_data["gfg"]),
        "leetcode_calendar_json": processed_data["heatmap_calendar"],
    }

    return render(request, "dashboard.html", context)