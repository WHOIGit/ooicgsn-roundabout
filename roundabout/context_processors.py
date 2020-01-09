# make thes App, Namespace, URL names available for templates
def template_resolver_names(request):
    # variable to identify if app is a "Template" app or "Real Thing" app
    template_app_list =['parts', 'assemblies', 'locations']

    if request.resolver_match.app_name in template_app_list:
        template_app_mode = True
    else:
        template_app_mode = False

    return {
        'app_name': request.resolver_match.app_name,
        'namespace': request.resolver_match.namespace,
        'url_name': request.resolver_match.url_name,
        'template_app_mode': template_app_mode,
    }

# Set sitewide template variable for headings/labels display

# Check the Site domain, set Moorings app labels
def template_app_labels(request):
    from django.contrib.sites.models import Site
    current_site = Site.objects.get_current()

    if current_site.domain == 'obs-rdb.whoi.edu':
        label_assemblies_app_plural = 'Instruments'
        label_assemblies_app_singular = 'Instrument'

        label_deployments_app_plural = 'Experiments'
        label_deployments_app_singular = 'Experiment'
    else:
        label_assemblies_app_plural = 'Assemblies'
        label_assemblies_app_singular = 'Assemblies'

        label_deployments_app_plural = 'Deployments'
        label_deployments_app_singular = 'Deployment'


    return {
            'label_assemblies_app_plural': label_assemblies_app_plural,
            'label_assemblies_app_singular': label_assemblies_app_singular,
            'label_deployments_app_plural': label_deployments_app_plural,
            'label_deployments_app_singular': label_deployments_app_singular,
           }
