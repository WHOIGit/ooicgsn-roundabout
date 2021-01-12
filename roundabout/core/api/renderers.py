from rest_framework.renderers import BrowsableAPIRenderer

class CustomBrowsableAPIRenderer(BrowsableAPIRenderer):
    # Exclude the forms
    def get_rendered_html_form(self, data, view, method, request):
        return None

    def get_name(self, view):
        if 'Deployment Oms Custom' in view.get_view_name():
            return 'OMS++ Build/Deployment Custom Endpoint'
        return view.get_view_name()

    def get_description(self, view, status_code):
        return ''
