from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView, RedirectView, UpdateView, CreateView, FormView, DeleteView
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.forms import AdminPasswordChangeForm

from .forms import UserAdminCreateForm, UserAdminUpdateForm
User = get_user_model()


class UserDetailView(LoginRequiredMixin, DetailView):

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


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
