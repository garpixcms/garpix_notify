from django.contrib import admin


class MainAdmin(admin.ModelAdmin):

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        seo_fields = [field for field in fields if field.startswith('seo')]
        non_seo_fields = [field for field in fields if not field.startswith('seo')]
        fields = non_seo_fields + seo_fields
        m2m_fields = [field.name for field in self.model._meta.concrete_model._meta.many_to_many]
        self.filter_horizontal = [field for field in m2m_fields if field in fields]
        return fields