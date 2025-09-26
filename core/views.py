# core/views.py
# core/views.py (at the top)
# core/views.py (add to existing imports)
# core/views.py (add to imports)
from django.utils.translation import gettext as _
import random 
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.db.models import Count
from django.utils import timezone
from .models import WaterQualityReport # Import the WaterQualityReport model
import json # Make sure json is imported
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from .models import HealthReport # Make sure HealthReport is imported
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import CustomUser
# core/views.py
from django.http import HttpResponse
from django.conf import settings
import os

def service_worker_view(request):
    sw_path = os.path.join(settings.BASE_DIR, 'serviceworker.js')
    with open(sw_path, 'r') as f:
        return HttpResponse(f.read(), content_type='application/javascript')

# This will be our main view for handling login and signup display
def auth_view(request):
    # If the user is already logged in, redirect them to their dashboard
    if request.user.is_authenticated:
        if request.user.role == 'worker':
            return redirect('worker_dashboard')
        elif request.user.role == 'official':
            return redirect('official_dashboard')
            
    # If it's a POST request, it means a form is being submitted
    if request.method == 'POST':
        # Check which form was submitted
        form_type = request.POST.get('form_type')
        
        if form_type == 'login':
            return login_view(request)
        elif form_type == 'signup':
            return signup_view(request)

    # If it's a GET request, just show the auth page
    return render(request, 'core/auth.html')


def login_view(request):
    identifier = request.POST.get('identifier')
    password = request.POST.get('password')
    user = None

    # Try to authenticate with the identifier as a username (for phone numbers)
    user = authenticate(request, username=identifier, password=password)

    # If that fails, try to authenticate with it as an email (for officials)
    if user is None:
        try:
            # Find the user by email
            user_by_email = CustomUser.objects.get(email=identifier)
            # Then authenticate with their username
            user = authenticate(request, username=user_by_email.username, password=password)
        except CustomUser.DoesNotExist:
            user = None

    if user is not None:
        login(request, user)
        # Redirect based on role after successful login
        if user.role == 'worker':
            return redirect('worker_dashboard')
        else:
            return redirect('official_dashboard')
    else:
        # If authentication fails, show an error message
        messages.error(request, _('Invalid phone number/email or password.'))
        return redirect('auth_page')


def signup_view(request):
    identifier = request.POST.get('identifier')
    password = request.POST.get('password')
    role = request.POST.get('role')

    # Basic Validation
    if len(password) < 6:
        messages.error(request, 'Password must be at least 6 characters long.')
        return redirect('auth_page')

    try:
        if role == 'worker':
            # For workers, the identifier is a phone number. We use it as the username.
            # We create a "dummy" email to satisfy Django's requirements.
            if CustomUser.objects.filter(username=identifier).exists():
                messages.error(request, 'This phone number is already registered.')
                return redirect('auth_page')
            
            user = CustomUser.objects.create_user(
                username=identifier, # Phone number as username
                email=f'{identifier}@worker.aquaalert.com', # Dummy email
                password=password,
                role='worker',
                phone_number=identifier
            )
        else: # role == 'official'
            # For officials, the identifier is their email. We'll use the part before the '@' as their username.
            if CustomUser.objects.filter(email=identifier).exists():
                messages.error(request, 'This email is already registered.')
                return redirect('auth_page')

            username = identifier.split('@')[0]
            # Ensure username is unique
            if CustomUser.objects.filter(username=username).exists():
                username = f"{username}{CustomUser.objects.count()}" # Append count to make it unique

            user = CustomUser.objects.create_user(
                username=username,
                email=identifier,
                password=password,
                role='official'
            )
        
        # Log the new user in and redirect
        login(request, user)
        if user.role == 'worker':
            return redirect('worker_dashboard')
        else:
            return redirect('official_dashboard')

    except Exception as e:
        messages.error(request, f'An error occurred: {e}')
        return redirect('auth_page')

def logout_view(request):
    logout(request)
    return redirect('auth_page')


# Placeholder views for the dashboards
# We will add logic to these later. For now, they just render a template.
# core/views.py

@login_required(login_url='auth_page') # Redirect to login if not authenticated
def worker_dashboard_view(request):
    # Security check: Ensure user is a worker
    if request.user.role != 'worker':
        return redirect('auth_page') # Or show an unauthorized page

    # This view's main job is just to render the page. 
    # The form data will be sent to a different API view via JavaScript.
    return render(request, 'core/worker_dashboard.html')
# core/views.py

# core/views.py
# Make sure to import 'random' at the top of the file

@login_required(login_url='auth_page')
def official_dashboard_view(request):
    if request.user.role != 'official':
        return redirect('auth_page')

    # This view now only renders the initial page.
    # The live data will be fetched by a new API view.
    return render(request, 'core/official_dashboard.html')


# This is our new, dedicated API view for the live dashboard data
def dashboard_data_api(request):
    # --- 1. Data Fetching & "AI" Analysis ---
    forty_eight_hours_ago = timezone.now() - timedelta(hours=48)
    recent_reports = HealthReport.objects.filter(timestamp__gte=forty_eight_hours_ago)

    all_villages = [
        'mawlynnong_meghalaya', 'ziro_arunachal', 'majuli_assam',
        'khonoma_nagaland', 'moirang_manipur', 'pelling_sikkim',
        'champhai_mizoram', 'unakoti_tripura'
    ]
    village_coordinates = {
        'mawlynnong_meghalaya': {'lat': 25.195, 'lng': 92.019, 'name': 'Mawlynnong'},
        'ziro_arunachal': {'lat': 27.63, 'lng': 93.83, 'name': 'Ziro'},
        'majuli_assam': {'lat': 26.91, 'lng': 94.13, 'name': 'Majuli'},
        'khonoma_nagaland': {'lat': 25.67, 'lng': 94.01, 'name': 'Khonoma'},
        'moirang_manipur': {'lat': 24.50, 'lng': 93.77, 'name': 'Moirang'},
        'pelling_sikkim': {'lat': 27.32, 'lng': 88.24, 'name': 'Pelling'},
        'champhai_mizoram': {'lat': 23.46, 'lng': 93.33, 'name': 'Champhai'},
        'unakoti_tripura': {'lat': 24.08, 'lng': 92.07, 'name': 'Unakoti'}
    }

    # --- FIX FOR PREDICTIVE ALERTS ---
    village_case_counts = {village: 0 for village in all_villages}
    for report in recent_reports:
        if report.village in village_case_counts:
            village_case_counts[report.village] += 1

    alerts = []
    villages_with_outbreak_alerts = set()

    # First, process outbreak-level alerts
    for village_id, count in village_case_counts.items():
        if count > 4:
            village_name = village_coordinates.get(village_id, {}).get('name', 'Unknown')
            latest_water_report = WaterQualityReport.objects.filter(village=village_id).last()
            is_water_contaminated = latest_water_report and latest_water_report.turbidity > 5.0

            alert_type = 'critical'
            message = f"OUTBREAK: {count} cases reported in {village_name}. Immediate action required."
            if is_water_contaminated:
                alert_type = 'critical-water'
                message = f"CRITICAL: Outbreak in {village_name} ({count} cases) linked to contaminated water (Turbidity: {latest_water_report.turbidity})."

            alerts.append({'type': alert_type, 'message': message, 'village_id': village_id})
            villages_with_outbreak_alerts.add(village_id)

    # Now, process predictive alerts for all other villages
    for village_id in all_villages:
        if village_id not in villages_with_outbreak_alerts:
            latest_water_report = WaterQualityReport.objects.filter(village=village_id).last()
            if latest_water_report and latest_water_report.turbidity > 5.0:
                village_name = village_coordinates.get(village_id, {}).get('name', 'Unknown')
                alerts.append({
                    'type': 'predictive',
                    'message': f"PREDICTIVE: Water in {village_name} is contaminated (Turbidity: {latest_water_report.turbidity}). High risk of an outbreak.",
                    'village_id': village_id
                })

    # --- FIX FOR MAP DOTS ---
    map_report_data = []
    for report in recent_reports:
        coords = village_coordinates.get(report.village)
        if coords:
            # Add a small random offset (jitter) to each coordinate
            jitter_lat = random.uniform(-0.005, 0.005)
            jitter_lng = random.uniform(-0.005, 0.005)
            map_report_data.append({
                'lat': coords['lat'] + jitter_lat,
                'lng': coords['lng'] + jitter_lng,
                'village': coords['name'],
                'symptoms': ', '.join(report.symptoms)
            })

    # Prepare chart data based on the processed counts
    sorted_counts = sorted(village_case_counts.items(), key=lambda item: item[1], reverse=True)
    chart_data = {
        "labels": [village_coordinates.get(v[0], {}).get('name', v[0]) for v in sorted_counts],
        "datasets": [{"name": "Cases", "values": [v[1] for v in sorted_counts]}]
    }

    # Consolidate all data into one JSON response
    data = {
        'alerts': alerts,
        'map_report_data': map_report_data,
        'chart_data': chart_data
    }
    return JsonResponse(data)

# core/views.py (add at the end)

@login_required
def submit_health_report_api(request):
    if request.method == 'POST' and request.user.role == 'worker':
        try:
            data = json.loads(request.body)
            report = HealthReport.objects.create(
                reported_by=request.user,
                village=data.get('village'),
                age_group=data.get('ageGroup'),
                symptoms=data.get('symptoms')
            )
            return JsonResponse({'status': 'success', 'message': 'Report saved.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)

# core/views.py (add at the end)

@csrf_exempt # Disable CSRF for this API endpoint
def water_quality_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            WaterQualityReport.objects.create(
                village=data.get('village'),
                ph=data.get('ph'),
                turbidity=data.get('turbidity'),
                contaminants=data.get('contaminants', {})
            )
            return JsonResponse({'status': 'success', 'message': 'Water quality data received.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

# core/views.py (add at the end)

@login_required
def session_status_api(request):
    """
    A simple API to report the current user's authentication status and role.
    """
    return JsonResponse({
        'authenticated': True,
        'role': request.user.role
    })