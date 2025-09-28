from rest_framework import viewsets
from .models import SpaceWeatherData, Subscription
from django.http import JsonResponse
import google.generativeai as genai
from django.conf import settings
from gtts import gTTS
import os
from django.core.mail import send_mail
import threading
from .serializers import SpaceWeatherSerializer, SubscriptionSerializer

class SpaceWeatherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SpaceWeatherData.objects.all().order_by('-timestamp')[:20]
    serializer_class = SpaceWeatherSerializer

class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

    def perform_create(self, serializer):
        
        subscription = serializer.save()

        if subscription.email:
            subject = "Successfully Registered! 🌞 Welcome to Space Weather Dashboard! 🚀"
            message = f"""
            Hello {subscription.username} 👋,

            Welcome aboard Space Weather Dashboard! 🌌

            Thank you for registering. You're now part of our mission to monitor the Sun and stay ahead of space weather. ⚡

            Explore real-time solar flares, geomagnetic storms, and auroras, and see how they might affect life on Earth. 🌍

            Keep your eyes on the sky! 🌟
"""
            recipient_list = [subscription.email] 

            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                recipient_list,
                fail_silently=False
            )

genai.configure(api_key="AIzaSyDwc7rPa1I3AJfuEPIapL3MHi7NyS0ALak")


def generate_story(request):
    risk_score = request.GET.get("risk_score", 50)
    kp_index = request.GET.get("kp_index", 3)
    flare_class = request.GET.get("flare_class", "C")
    character = request.GET.get("character", "Farmer Jane")
    topic= request.GET.get('topic')

    prompt = f"""
        Write a short, fun, and kid-friendly story about{topic} in space weather,in easy to understand language, you need to explain and teach it to students who want to learn about {topic}. 
        The character is {character}. Today's space weather has:
        - Kp index: {kp_index}
        - Flare class: {flare_class}
        - Risk score: {risk_score}

        Make the story:
        1. Easy to read in plain text (no extra punctuation or markdown)
        2. Engaging and visual, so kids can imagine what is happening
        3. Use short sentences and emojis to illustrate events (like 🌞 for the Sun, ⚡ for solar flares, 🌌 for auroras)
        4. Keep it under 10 - 15 sentences

        Do not add extra commas, stars, or bullet points in the final story text.
        """


    model = genai.GenerativeModel("gemini-2.5-pro")
    story_response = model.generate_content(prompt)
    story_text = story_response.text.strip()

    audio_dir = os.path.join(settings.MEDIA_ROOT, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    filename = f"story_{character.replace(' ', '_')}.mp3"
    audio_file_path = os.path.join(audio_dir, filename)

    def generate_audio():
        tts = gTTS(text=story_text, lang='en')
        tts.save(audio_file_path)

    threading.Thread(target=generate_audio).start()

    audio_url = f"{settings.MEDIA_URL}audio/{filename}"

    return JsonResponse({
        "story": story_text,
        "audio_url": audio_url
    })
