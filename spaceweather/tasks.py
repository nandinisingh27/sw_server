from celery import shared_task
import requests
from dateutil.parser import parse
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
from .models import SpaceWeatherData, Subscription
from django.utils.timezone import is_aware, make_naive, make_aware
import traceback
import certifi
from django.conf import settings as django_settings


NOAA_KP = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
NOAA_WIND = "https://services.swpc.noaa.gov/products/solar-wind/plasma-1-day.json"
NOAA_FLARE = "https://services.swpc.noaa.gov/json/goes/primary/xray-flares-latest.json" 
ALWAYS_INSERT = False  


def safe_get_json(url, timeout=10):
    try:
        resp = requests.get(url, timeout=timeout, verify=certifi.where())
        if resp.status_code == 200 and resp.text.strip():
            try:
                return resp.json()
            except ValueError:
                print(f"Invalid JSON from {url}: {resp.text[:200]}")
                return None
        else:
            print(f"Request to {url} failed: {resp.status_code}")
            return None
    except requests.exceptions.SSLError:
        print(f"SSL Error while fetching {url}. Update certifi or fix cert chain.")
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def compute_risk(kp, flare_class):
    score = 0
    if kp >= 7:
        score += 50
    if flare_class.startswith('X'):
        score += 50
    return min(score, 100)


def send_alert(subscription, score):
    message = f"Space Weather Alert! Risk Score: {score}"
    if subscription.email:
        send_mail("Space Weather Alert", message, settings.EMAIL_HOST_USER, [subscription.email])
  


@shared_task(bind=True, max_retries=3)
def fetch_space_weather(self):
    try:
        kp_data = safe_get_json(NOAA_KP)
        if not kp_data:
            print("No Kp data, skipping this run.")
            return

        latest_kp = kp_data[-1]
        kp_value = latest_kp.get("kp_index")
        timestamp = latest_kp.get("time_tag")
        if kp_value is None or not timestamp:
            print("Incomplete Kp data, skipping this run.")
            return

        dt = parse(timestamp)
        if dt.tzinfo is None:
            dt = make_aware(dt)

        if not getattr(django_settings, "USE_TZ", True):
            if is_aware(dt):
                dt = make_naive(dt)

        wind_data = safe_get_json(NOAA_WIND)
        if not wind_data or len(wind_data) < 2:
            solar_wind_speed = 400.0  
        else:
            try:
                solar_wind_speed = float(wind_data[-1][1])
            except (ValueError, IndexError):
                solar_wind_speed = 400.0

        flare_data = safe_get_json(NOAA_FLARE)
        if flare_data and isinstance(flare_data, list) and len(flare_data) > 0:
            flare_class = flare_data[-1].get('max_class', "C")
        else:
            flare_class = "C"  
        risk_score = compute_risk(kp_value, flare_class)

        if ALWAYS_INSERT:
            SpaceWeatherData.objects.create(
                timestamp=dt,
                kp_index=kp_value,
                solar_wind_speed=solar_wind_speed,
                flare_class=flare_class,
                risk_score=risk_score
            )
            print(f"Data saved (forced insert): {dt} | Kp={kp_value} | Wind={solar_wind_speed} | Flare={flare_class} | Risk={risk_score}")
        else:
            if not SpaceWeatherData.objects.filter(timestamp=dt).exists():
                SpaceWeatherData.objects.create(
                    timestamp=dt,
                    kp_index=kp_value,
                    solar_wind_speed=solar_wind_speed,
                    flare_class=flare_class,
                    risk_score=risk_score
                )
                print(f"Data saved: {dt} | Kp={kp_value} | Wind={solar_wind_speed} | Flare={flare_class} | Risk={risk_score}")
            else:
                print(f"Data for {dt} already exists. Skipping insert.")

        for sub in Subscription.objects.all():
            if risk_score >= sub.threshold:
                send_alert(sub, risk_score)

    except Exception as e:
        print("Error in fetch_space_weather:", e)
        traceback.print_exc()
        raise self.retry(exc=e, countdown=60)
