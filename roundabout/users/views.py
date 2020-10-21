"""
# Copyright (C) 2019-2020 Woods Hole Oceanographic Institution
#
# This file is part of the Roundabout Database project ("RDB" or
# "ooicgsn-roundabout").
#
# ooicgsn-roundabout is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# ooicgsn-roundabout is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ooicgsn-roundabout in the COPYING.md file at the project root.
# If not, see <http://www.gnu.org/licenses/>.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import View, DetailView, ListView, RedirectView, UpdateView, CreateView, FormView, DeleteView
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.forms import AdminPasswordChangeForm
from rest_framework.authtoken.models import Token

from .forms import UserAdminCreateForm, UserAdminUpdateForm
User = get_user_model()


class UserDetailView(LoginRequiredMixin, DetailView):

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super(UserDetailView, self).get_context_data(**kwargs)

        token, created = Token.objects.get_or_create(user=self.object)
        print(token)
        context.update({
            'token': token.key,
        })
        return context

user_detail_view = UserDetailView.as_view()


class UserListView(LoginRequiredMixin, ListView):

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_list_view = UserListView.as_view()


class UserUpdateView(LoginRequiredMixin, UpdateView):

    model = User
    fields = ["name"]

    def get_success_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})

    def get_object(self):
        return User.objects.get(username=self.request.user.username)


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):

    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()

class UserAdminDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = User
    template_name='users/user_admin_detail.html'
    permission_required = 'users.add_user'


class UserAdminCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = User
    form_class = UserAdminCreateForm
    template_name='users/user_admin_form.html'
    permission_required = 'users.add_user'

    def get_success_url(self):
        return reverse('users:user_admin_detail', args=(self.object.id, ))

    def form_valid(self, form):
        self.object = form.save()
        self.object.password = make_password(self.object.password)
        self.object.save()

        return HttpResponseRedirect(self.get_success_url())


class UserAdminUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = User
    form_class = UserAdminUpdateForm
    context_object_name = 'user_admin'
    template_name='users/user_admin_form.html'
    permission_required = 'users.add_user'

    def get_success_url(self):
        return reverse('users:user_admin_detail', args=(self.object.id, ))


class UserAdminPasswordChangeView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    form_class = AdminPasswordChangeForm
    context_object_name = 'user_admin'
    template_name='users/user_admin_password_form.html'
    permission_required = 'users.add_user'
    redirect_field_name = 'home'

    def get_form_kwargs(self):
        kwargs = super(UserAdminPasswordChangeView, self).get_form_kwargs()
        kwargs['user'] = User.objects.get(id=self.kwargs['pk'])
        return kwargs

    def form_valid(self, form):
        form.save()
        return super(UserAdminPasswordChangeView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(UserAdminPasswordChangeView, self).get_context_data(**kwargs)
        # Add Parts list to context to build form filter
        context.update({
            'user_admin': User.objects.get(id=self.kwargs['pk'])
        })
        return context

    def get_success_url(self):
        return reverse('users:user_admin_detail', args=(self.kwargs['pk'], ))


class UserAdminDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = User
    template_name='users/user_confirm_delete.html'
    success_url = reverse_lazy('users:list')
    permission_required = 'users.add_user'


# View to Suspend User by deactivating them
class UserAdminSuspendView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs['pk'])
        user.is_active = False
        user.save()
        # Remove API token if it exists
        try:
            Token.objects.get(user=user).delete()
        except Token.DoesNotExist:
            pass
        return reverse('users:user_admin_detail', args=(self.kwargs['pk'], ))


# View to Activate User who has been suspended
class UserAdminActivateView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs['pk'])
        user.is_active = True
        user.save()
        return reverse('users:user_admin_detail', args=(self.kwargs['pk'], ))


# View for API Token reset
class UserTokenResetView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs['pk'])
        Token.objects.get(user=user).delete()
        new_token = Token.objects.create(user=user)
        return reverse('users:detail', args=(user.username, ))
