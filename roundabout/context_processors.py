# Set sitewide template variable for headings/labels display

# Check the Site domain, set Moorings app labels
def template_app_labels(request):
    from django.contrib.sites.models import Site
    current_site = Site.objects.get_current()

    if current_site.domain == 'obs-rdb.whoi.edu':
        label_moorings_app_plural = 'Instruments'
        label_moorings_app_singular = 'Instrument'

        label_deployments_app_plural = 'Experiments'
        label_deployments_app_singular = 'Experiment'
    else:
        label_moorings_app_plural = 'Moorings'
        label_moorings_app_singular = 'Mooring'

        label_deployments_app_plural = 'Deployments'
        label_deployments_app_singular = 'Deployment'


    return {
            'label_moorings_app_plural': label_moorings_app_plural,
            'label_moorings_app_singular': label_moorings_app_singular,
            'label_deployments_app_plural': label_deployments_app_plural,
            'label_deployments_app_singular': label_deployments_app_singular,

           }
