from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from common.util.mixins import AjaxFormMixin
from .models import Build, BuildAction
from .forms import *
from roundabout.locations.models import Location
from roundabout.inventory.models import Inventory, Action

# Load the javascript navtree
def load_builds_navtree(request):
    locations = Location.objects.exclude(root_type='Retired').prefetch_related('builds').prefetch_related('inventory__part__part_type')
    return render(request, 'builds/ajax_build_navtree.html', {'locations': locations})

## CBV views for Builds app ##

# Landing page for Builds
class BuildHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'builds/build_list.html'
    context_object_name = 'builds'

    def get_context_data(self, **kwargs):
        context = super(BuildHomeView, self).get_context_data(**kwargs)
        context.update({
            'node_type': 'builds',
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


# Detail view for builds
class BuildAjaxDetailView(LoginRequiredMixin, DetailView):
    model = Build
    context_object_name = 'build'
    template_name='builds/ajax_build_detail.html'


# Create view for assemblies
class BuildAjaxCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    model = Build
    form_class = BuildForm
    context_object_name = 'build'
    template_name='builds/ajax_build_form.html'

    def form_valid(self, form):
        self.object = form.save()

        action_record = BuildAction.objects.create(action_type='buildadd', detail='Build created.', location=self.object.location,
                                                   user=self.request.user, build=self.object)

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse('builds:ajax_builds_detail', args=(self.object.id,))


# Update view for builds
class BuildAjaxUpdateView(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    model = Build
    form_class = BuildForm
    context_object_name = 'build'
    template_name='builds/ajax_build_form.html'

    def form_valid(self, form):
        self.object = form.save()

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
            }
            return JsonResponse(data)
        else:
            return response

    def get_success_url(self):
        return reverse('builds:ajax_builds_detail', args=(self.object.id,))


# Action view to handle discrete form actions
class BuildAjaxActionView(BuildAjaxUpdateView):

    def get_form_class(self):
        ACTION_FORMS = {
            "locationchange" : BuildActionLocationChangeForm,

        }
        action_type = self.kwargs['action_type']
        form_class_name = ACTION_FORMS[action_type]

        return form_class_name

    def form_valid(self, form):
        if self.kwargs['action_type'] == 'locationchange':
            # Find previous location to add to Detail field text
            old_location_pk = self.object.tracker.previous('location')
            if old_location_pk:
                old_location = Location.objects.get(pk=old_location_pk)
                if old_location.name != self.object.location.name:
                    self.object.detail = 'Moved to %s from %s. ' % (self.object.location.name, old_location) + self.object.detail

            # Get any subassembly children items, move their location sto match parent and add Action to history
            subassemblies = self.object.inventory.all()
            mooring_parts_added = []
            for item in subassemblies:
                if self.object.mooring_part_id:
                    sub_mooring_parts = MooringPart.objects.get(id=self.object.mooring_part_id).get_descendants()
                    sub_mooring_part = sub_mooring_parts.filter(part=item.part)
                    for sub in sub_mooring_part:
                        if sub.id not in mooring_parts_added:
                            item.mooring_part = sub
                            mooring_parts_added.append(sub.id)
                            break
                else:
                    item.mooring_part = None

                item.location = self.object.location
                if old_location.name != self.object.location.name:
                    item.detail = 'Moved to %s from %s' % (self.object.location.name, old_location.name)
                else:
                    item.detail = 'Parent Inventory Change'
                item.save()
                action_record = Action.objects.create(action_type=self.kwargs['action_type'], detail=item.detail, location=item.location,
                                                      user=self.request.user, inventory=item)

        if self.kwargs['action_type'] == 'removefromdeployment':
            # Find Deployment it was removed from
            old_deployment_pk = self.object.tracker.previous('deployment')
            if old_deployment_pk:
                old_deployment = Deployment.objects.get(pk=old_deployment_pk)
                self.object.detail = ' Removed from %s.' % (old_deployment.get_deployment_label()) + self.object.detail

            # Get any subassembly children items, add Action to history
            subassemblies = Inventory.objects.get(id=self.object.id).get_descendants()
            for item in subassemblies:
                item.mooring_part = None
                item.deployment = None
                item.location = self.object.location
                item.detail = ' Removed from %s.' % (old_deployment.get_deployment_label())
                item.save()
                action_record = Action.objects.create(action_type=self.kwargs['action_type'], detail=item.detail, location_id=item.location_id,
                                                      user_id=self.request.user.id, inventory_id=item.id)

        if self.kwargs['action_type'] == 'removedest':
            self.object.detail = 'Destination Assignment removed.'
            # Get any subassembly children items, add Action to history
            subassemblies = Inventory.objects.get(id=self.object.id).get_descendants()
            for item in subassemblies:
                item.mooring_part = None
                item.assigned_destination_root = None
                item.detail = 'Destination Assignment removed.'
                item.save()
                action_record = Action.objects.create(action_type=self.kwargs['action_type'], detail=item.detail, location_id=item.location_id,
                                                      user_id=self.request.user.id, inventory_id=item.id)

        elif self.kwargs['action_type'] == 'test':
            self.object.detail = '%s: %s. ' % (self.object.get_test_type_display(), self.object.get_test_result_display()) + self.object.detail

        #elif self.kwargs['action_type'] == 'flag':
            #self.kwargs['action_type'] = self.object.get_flag_display()

        elif self.kwargs['action_type'] == 'subchange':
            # Find previous parent to add to Detail field text
            old_parent_pk = self.object.tracker.previous('parent')
            if old_parent_pk:
                old_parent = Inventory.objects.get(pk=old_parent_pk)
                parent_detail = 'Subassembly %s removed. ' % (self.object) + self.object.detail
                self.object.detail = 'Removed from %s. ' % (old_parent) + self.object.detail

                # Add Action Record for Parent Assembly
                action_record = Action.objects.create(action_type=self.kwargs['action_type'], detail=parent_detail, location_id=self.object.location_id,
                                                      user_id=self.request.user.id, inventory_id=old_parent_pk)

            # Find previous location to add to Detail field text
            old_location_pk = self.object.tracker.previous('location')
            if old_location_pk:
                old_location = Location.objects.get(pk=old_location_pk)
                if self.object.deployment:
                    self.object.detail = 'Moved to %s from %s' % (self.object.deployment, old_location.name) + self.object.detail
                elif old_location.name != self.object.location.name:
                    self.object.detail = 'Moved to %s from %s. ' % (self.object.location.name, old_location) + self.object.detail

            # Get any subassembly children items, move their location to match parent and add Action to history
            subassemblies = Inventory.objects.get(id=self.object.id).get_descendants()
            mooring_parts_added = []
            for item in subassemblies:
                if self.object.mooring_part_id:
                    sub_mooring_parts = MooringPart.objects.get(id=self.object.mooring_part_id).get_descendants()
                    sub_mooring_part = sub_mooring_parts.filter(part=item.part)
                    for sub in sub_mooring_part:
                        if sub.id not in mooring_parts_added:
                            item.mooring_part = sub
                            mooring_parts_added.append(sub.id)
                            break
                else:
                    item.mooring_part = None

                item.location = self.object.location
                item.deployment = self.object.deployment
                item.assigned_destination_root = self.object.assigned_destination_root

                if self.object.deployment:
                    item.detail = 'Moved to %s from %s' % (self.object.deployment, old_location.name)
                elif old_location.name != self.object.location.name:
                    item.detail = 'Moved to %s from %s' % (self.object.location.name, old_location.name)
                else:
                    item.detail = 'Parent Inventory Change'
                item.save()
                action_record = Action.objects.create(action_type=self.kwargs['action_type'], detail=item.detail, location_id=item.location_id,
                                                      user_id=self.request.user.id, inventory_id=item.id)

        action_form = form.save()
        action_record = BuildAction.objects.create(action_type=self.kwargs['action_type'], detail=self.object.detail, location=self.object.location,
                                              user=self.request.user, build=self.object)

        response = HttpResponseRedirect(self.get_success_url())

        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'object_id': self.object.id,
                'location_id': self.object.location.id,
            }
            return JsonResponse(data)
        else:
            return response
