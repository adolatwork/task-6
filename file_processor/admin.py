from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from datetime import timedelta

from .models import TaskLog, TaskProgress, TaskEventLog


class StatusFilter(SimpleListFilter):
    """Custom filter for task status"""
    title = 'Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return [
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
            ('retry', 'Retry'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class TaskTypeFilter(SimpleListFilter):
    """Custom filter for task type"""
    title = 'Task Type'
    parameter_name = 'task_type'

    def lookups(self, request, model_admin):
        return [
            ('image', 'Image'),
            ('video', 'Video'),
            ('document', 'Document'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(task_type=self.value())
        return queryset


class RecentTasksFilter(SimpleListFilter):
    """Filter for recent tasks"""
    title = 'Created Date'
    parameter_name = 'created_date'

    def lookups(self, request, model_admin):
        return [
            ('today', 'Today'),
            ('week', 'Last 7 days'),
            ('month', 'Last 30 days'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'today':
            return queryset.filter(created_at__date=timezone.now().date())
        elif self.value() == 'week':
            return queryset.filter(created_at__gte=timezone.now() - timedelta(days=7))
        elif self.value() == 'month':
            return queryset.filter(created_at__gte=timezone.now() - timedelta(days=30))
        return queryset


class TaskProgressInline(admin.TabularInline):
    """Inline admin for TaskProgress"""
    model = TaskProgress
    extra = 0
    readonly_fields = ('progress', 'message', 'data', 'created_at')
    can_delete = False
    fields = ('progress', 'message', 'created_at')
    ordering = ('-created_at',)
    
    def has_add_permission(self, request, obj=None):
        return False


class TaskEventLogInline(admin.TabularInline):
    """Inline admin for TaskEventLog"""
    model = TaskEventLog
    extra = 0
    readonly_fields = ('event_type', 'message', 'metadata', 'created_at')
    can_delete = False
    fields = ('event_type', 'message', 'created_at')
    ordering = ('-created_at',)
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(TaskLog)
class TaskLogAdmin(admin.ModelAdmin):
    """Admin interface for TaskLog model"""
    
    list_display = (
        'id_short',
        'file_name_display',
        'task_type',
        'status_badge',
        'progress_bar',
        'user_id',
        'retry_info',
        'created_at',
        'elapsed_time_display',
        'actions_column',
    )
    
    list_filter = (
        StatusFilter,
        TaskTypeFilter,
        RecentTasksFilter,
        'created_at',
        'status',
        'task_type',
    )
    
    search_fields = (
        'file_name',
        'celery_task_id',
        'file_path',
        'error_message',
        'error_code',
    )
    
    readonly_fields = (
        'id',
        'celery_task_id',
        'created_at',
        'started_at',
        'completed_at',
        'cancelled_at',
        'elapsed_time_display',
        'is_cancellable_display',
        'is_retryable_display',
        'progress_history_count',
        'events_count',
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'celery_task_id', 'task_type', 'status', 'user_id')
        }),
        ('File Information', {
            'fields': ('file_name', 'file_path', 'file_size')
        }),
        ('Progress & Status', {
            'fields': (
                'progress',
                'elapsed_time_display',
                'is_cancellable_display',
                'is_retryable_display',
            )
        }),
        ('Retry Information', {
            'fields': ('retry_count', 'max_retries')
        }),
        ('Results & Errors', {
            'fields': ('result', 'error_message', 'error_code'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('tags', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'started_at',
                'completed_at',
                'cancelled_at',
            )
        }),
        ('Statistics', {
            'fields': ('progress_history_count', 'events_count'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TaskProgressInline, TaskEventLogInline]
    
    date_hierarchy = 'created_at'
    
    ordering = ('-created_at',)
    
    list_per_page = 50
    
    actions = ['cancel_selected_tasks', 'retry_failed_tasks', 'mark_as_completed']
    
    def id_short(self, obj):
        """Display shortened UUID"""
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    id_short.admin_order_field = 'id'
    
    def file_name_display(self, obj):
        """Display file name with truncation"""
        if len(obj.file_name) > 30:
            return obj.file_name[:30] + '...'
        return obj.file_name
    file_name_display.short_description = 'File Name'
    file_name_display.admin_order_field = 'file_name'
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': 'gray',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'orange',
            'retry': 'yellow',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def progress_bar(self, obj):
        """Display progress as a progress bar"""
        color = 'green' if obj.progress == 100 else 'blue'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px; '
            'height: 20px; position: relative;">'
            '<div style="width: {}%; background-color: {}; height: 100%; '
            'border-radius: 3px; text-align: center; line-height: 20px; '
            'color: white; font-size: 11px; font-weight: bold;">{}%</div>'
            '</div>',
            obj.progress,
            color,
            obj.progress
        )
    progress_bar.short_description = 'Progress'
    progress_bar.admin_order_field = 'progress'
    
    def retry_info(self, obj):
        """Display retry information"""
        if obj.retry_count > 0:
            return format_html(
                '<span style="color: orange;">{} / {}</span>',
                obj.retry_count,
                obj.max_retries
            )
        return f'0 / {obj.max_retries}'
    retry_info.short_description = 'Retries'
    
    def elapsed_time_display(self, obj):
        """Display elapsed time"""
        elapsed = obj.get_elapsed_time()
        if elapsed is not None:
            if elapsed < 60:
                return f"{elapsed:.1f}s"
            elif elapsed < 3600:
                return f"{elapsed / 60:.1f}m"
            else:
                return f"{elapsed / 3600:.1f}h"
        return "N/A"
    elapsed_time_display.short_description = 'Elapsed Time'
    
    def is_cancellable_display(self, obj):
        """Display if task is cancellable"""
        if obj.is_cancellable():
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    is_cancellable_display.short_description = 'Cancellable'
    
    def is_retryable_display(self, obj):
        """Display if task is retryable"""
        if obj.is_retryable():
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    is_retryable_display.short_description = 'Retryable'
    
    def progress_history_count(self, obj):
        """Display count of progress history entries"""
        count = obj.progress_history.count()
        if count > 0:
            return format_html(
                '<a href="{}?task__id__exact={}">{} entries</a>',
                reverse('admin:file_processor_taskprogress_changelist'),
                obj.id,
                count
            )
        return '0 entries'
    progress_history_count.short_description = 'Progress History'
    
    def events_count(self, obj):
        """Display count of event log entries"""
        count = obj.events.count()
        if count > 0:
            return format_html(
                '<a href="{}?task__id__exact={}">{} entries</a>',
                reverse('admin:file_processor_taskeventlog_changelist'),
                obj.id,
                count
            )
        return '0 entries'
    events_count.short_description = 'Event Logs'
    
    def actions_column(self, obj):
        """Display action links"""
        links = []
        if obj.is_cancellable():
            links.append(
                format_html(
                    '<a href="{}" style="color: orange;">Cancel</a>',
                    reverse('admin:file_processor_tasklog_change', args=[obj.pk])
                )
            )
        if obj.is_retryable():
            links.append(
                format_html(
                    '<a href="{}" style="color: blue;">Retry</a>',
                    reverse('admin:file_processor_tasklog_change', args=[obj.pk])
                )
            )
        return format_html(' | '.join(links)) if links else '-'
    actions_column.short_description = 'Actions'
    
    def cancel_selected_tasks(self, request, queryset):
        """Admin action to cancel selected tasks"""
        cancelled = 0
        for task in queryset:
            if task.is_cancellable():
                try:
                    from celery.app import current_app
                    current_app.control.revoke(task.celery_task_id, terminate=True)
                    task.status = 'cancelled'
                    task.cancelled_at = timezone.now()
                    task.save()
                    cancelled += 1
                except Exception as e:
                    self.message_user(
                        request,
                        f"Error cancelling task {task.id}: {str(e)}",
                        level='ERROR'
                    )
        self.message_user(
            request,
            f"Successfully cancelled {cancelled} task(s).",
            level='SUCCESS'
        )
    cancel_selected_tasks.short_description = "Cancel selected tasks"
    
    def retry_failed_tasks(self, request, queryset):
        """Admin action to retry failed tasks"""
        retried = 0
        for task in queryset.filter(status__in=['failed', 'retry']):
            if task.is_retryable():
                try:
                    from .celery_tasks import process_file
                    task.status = 'retry'
                    task.retry_count += 1
                    task.save()
                    process_file.delay(
                        celery_task_id=task.celery_task_id,
                        file_path=task.file_path,
                        task_type=task.task_type
                    )
                    retried += 1
                except Exception as e:
                    self.message_user(
                        request,
                        f"Error retrying task {task.id}: {str(e)}",
                        level='ERROR'
                    )
        self.message_user(
            request,
            f"Successfully retried {retried} task(s).",
            level='SUCCESS'
        )
    retry_failed_tasks.short_description = "Retry failed tasks"
    
    def mark_as_completed(self, request, queryset):
        """Admin action to mark tasks as completed"""
        updated = queryset.update(
            status='completed',
            completed_at=timezone.now(),
            progress=100
        )
        self.message_user(
            request,
            f"Successfully marked {updated} task(s) as completed.",
            level='SUCCESS'
        )
    mark_as_completed.short_description = "Mark selected tasks as completed"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related().prefetch_related('progress_history', 'events')


@admin.register(TaskProgress)
class TaskProgressAdmin(admin.ModelAdmin):
    """Admin interface for TaskProgress model"""
    
    list_display = (
        'id',
        'task_link',
        'progress',
        'message_short',
        'created_at',
    )
    
    list_filter = (
        'created_at',
        'progress',
    )
    
    search_fields = (
        'task__file_name',
        'task__celery_task_id',
        'message',
    )
    
    readonly_fields = ('task', 'progress', 'message', 'data', 'created_at')
    
    fieldsets = (
        ('Task Information', {
            'fields': ('task',)
        }),
        ('Progress Information', {
            'fields': ('progress', 'message', 'data', 'created_at')
        }),
    )
    
    date_hierarchy = 'created_at'
    
    ordering = ('-created_at',)
    
    list_per_page = 50
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def task_link(self, obj):
        """Link to related task"""
        url = reverse('admin:file_processor_tasklog_change', args=[obj.task.pk])
        return format_html('<a href="{}">{}</a>', url, obj.task.file_name)
    task_link.short_description = 'Task'
    task_link.admin_order_field = 'task__file_name'
    
    def message_short(self, obj):
        """Display truncated message"""
        if obj.message and len(obj.message) > 50:
            return obj.message[:50] + '...'
        return obj.message or '-'
    message_short.short_description = 'Message'


@admin.register(TaskEventLog)
class TaskEventLogAdmin(admin.ModelAdmin):
    """Admin interface for TaskEventLog model"""
    
    list_display = (
        'id',
        'task_link',
        'event_type_badge',
        'message_short',
        'created_at',
    )
    
    list_filter = (
        'event_type',
        'created_at',
    )
    
    search_fields = (
        'task__file_name',
        'task__celery_task_id',
        'message',
        'event_type',
    )
    
    readonly_fields = ('task', 'event_type', 'message', 'metadata', 'created_at')
    
    fieldsets = (
        ('Task Information', {
            'fields': ('task',)
        }),
        ('Event Information', {
            'fields': ('event_type', 'message', 'metadata', 'created_at')
        }),
    )
    
    date_hierarchy = 'created_at'
    
    ordering = ('-created_at',)
    
    list_per_page = 50
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def task_link(self, obj):
        """Link to related task"""
        url = reverse('admin:file_processor_tasklog_change', args=[obj.task.pk])
        return format_html('<a href="{}">{}</a>', url, obj.task.file_name)
    task_link.short_description = 'Task'
    task_link.admin_order_field = 'task__file_name'
    
    def event_type_badge(self, obj):
        """Display event type with color coding"""
        colors = {
            'created': 'blue',
            'started': 'green',
            'progress': 'cyan',
            'paused': 'yellow',
            'resumed': 'green',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'orange',
            'retried': 'purple',
        }
        color = colors.get(obj.event_type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_event_type_display()
        )
    event_type_badge.short_description = 'Event Type'
    event_type_badge.admin_order_field = 'event_type'
    
    def message_short(self, obj):
        """Display truncated message"""
        if obj.message and len(obj.message) > 50:
            return obj.message[:50] + '...'
        return obj.message or '-'
    message_short.short_description = 'Message'


admin.site.site_header = "Celery Task Queue Administration"
admin.site.site_title = "Task Queue Admin"
admin.site.index_title = "Welcome to Task Queue Administration"

