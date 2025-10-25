from django.contrib import admin
from .models import EventType, Category, Event, Participant, Registration, Attachment

@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 1

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "event_type", "category", "active", "main_date")
    list_filter = ("event_type", "category", "active")
    search_fields = ("title", "description")
    inlines = [AttachmentInline]

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "chat_id", "contact", "major", "created_at")
    search_fields = ("full_name", "chat_id", "contact")



@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("id", "participant", "event", "attendance", "created_at")
    list_filter = ("attendance", "event")
    search_fields = ("participant__full_name", "event__title")

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "description", "file", "uploaded_at")
