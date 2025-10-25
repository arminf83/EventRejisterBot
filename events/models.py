from django.db import models

class EventType(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = models.ForeignKey(EventType, on_delete=models.SET_NULL, null=True, related_name="events")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="events")
    active = models.BooleanField(default=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    main_date = models.DateTimeField(null=True, blank=True)
    banner = models.ImageField(upload_to="event_files/", null=True, blank=True)
    reminder_sent = models.BooleanField(default=False)
    reminder_message = models.TextField(blank=True, null=True)
    reminder_image = models.ImageField(upload_to="event_files/", blank=True, null=True)

    def __str__(self):
        return self.title


class Participant(models.Model):
    chat_id = models.CharField(max_length=100, unique=True)
    full_name = models.CharField(max_length=200, blank=True)
    contact = models.CharField(max_length=200, blank=True)
    know_us = models.CharField(max_length=200, blank=True)
    related_experiences = models.CharField(max_length=200, blank=True)
    major = models.CharField(max_length=200, blank=True)  # رشته تحصیلی
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.full_name or self.chat_id


class Registration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='registrations')
    created_at = models.DateTimeField(auto_now_add=True)
    reminder_sent = models.BooleanField(default=False)

    attendance = models.CharField(
        max_length=10,
        blank=True,
        choices=[('present', '✅ حاضر'), ('absent', '❌ غایب'), ('unknown', '⏳ نامشخص')],
        default='unknown'
    )

    def __str__(self):
        return f"{self.participant} -> {self.event.title}"


class Attachment(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='event_files/', blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event.title} - {self.description or 'فایل'}"
