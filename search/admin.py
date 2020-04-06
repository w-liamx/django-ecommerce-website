from django.contrib import admin
from .models import SearchTerm

# Register your models here.
class SearchTermAdmin(admin.ModelAdmin):
    list_display = ('query', 'ip_address', 'search_date')
    list_filter = ('ip_address', 'user', 'query')
    exclude = ('user',)

admin.site.register(SearchTerm, SearchTermAdmin)