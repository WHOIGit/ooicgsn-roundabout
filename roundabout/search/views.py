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

import json
import operator
from fnmatch import fnmatch
from functools import reduce
from urllib.parse import unquote

import django_tables2 as tables
from django.contrib.auth.mixins import LoginRequiredMixin
#from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Q, Count, OuterRef, Subquery
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import mark_safe
from django_tables2 import SingleTableView

from roundabout.assemblies.models import Assembly
from roundabout.builds.models import Build
from roundabout.calibrations.models import CalibrationEvent, CoefficientValueSet
from roundabout.configs_constants.models import ConfigEvent, ConfigValue
from roundabout.inventory.models import Inventory, Action
from roundabout.parts.models import Part
from roundabout.search.mixins import ExportStreamMixin
from roundabout.userdefinedfields.models import Field
from roundabout.users.models import User
from .tables import InventoryTable, PartTable, BuildTable, AssemblyTable, ActionTable, CalibrationTable, \
    ConfigConstTable, UDF_Column


def rgetattr(obj, attr, *args):
    """Recursive getattr(), where attr is dot.separated"""
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))

def searchbar_redirect(request):
    model = request.GET.get('model')
    url = 'search:'+model
    resp = redirect(url)

    query = request.GET.get('query')
    if query:
        if model=='inventory':      getstr = '?f=.0.part__name&f=.0.part__friendly_name&f=.0.serial_number&f=.0.old_serial_number&f=.0.location__name&l=.0.icontains&q=.0.{query}'
        elif model=='calibrations':
            if fnmatch(query.strip(),'????-??-??'):
                query = query.strip()
                getstr = '?f=.0.calibration_event__calibration_date&l=.0.date&q=.0.{query}'
            else: getstr = '?f=.0.calibration_event__inventory__serial_number&f=.0.calibration_event__inventory__part__name&f=.0.coefficient_name__calibration_name&f=.0.calibration_event__user_approver__any__username&f=.0.calibration_event__user_draft__any__username&f=.0.notes&l=.0.icontains&q=.0.{query}'
        elif model == 'configconsts':
            if fnmatch(query.strip(), '????-??-??'):
                query = query.strip()
                getstr = '?f=.0.config_event__configuration_date&l=.0.date&q=.0.{query}'
            else:
                getstr = '?f=.0.config_event__inventory__serial_number&f=.0.config_event__inventory__part__name&f=.0.config_name__name&f=.0.config_event__user_approver__any__username&f=.0.config_event__user_draft__any__username&f=.0.notes&l=.0.icontains&q=.0.{query}'
        elif model=='part':         getstr = '?f=.0.part_number&f=.0.name&f=.0.friendly_name&l=.0.icontains&q=.0.{query}'
        elif model == 'build':      getstr = '?f=.0.build_number&f=.0.assembly__name&f=.0.assembly__assembly_type__name&f=.0.assembly__description&f=.0.build_notes&f=.0.location__name&l=.0.icontains&q=.0.{query}'
        elif model == 'assembly':   getstr = '?f=.0.assembly_number&f=.0.name&f=.0.assembly_type__name&f=.0.description&l=.0.icontains&q=.0.{query}'
        elif model == 'action':     getstr = '?f=.0.action_type&f=.0.user__name&f=.0.detail&f=.0.location__name&f=.0.inventory__serial_number&f=.0.inventory__part__name&l=.0.icontains'+'&q=.0.{query}'
        elif model == 'user':       getstr = '?ccc_role=both&ccc_status=all'+'&q={query}'
        getstr = getstr.format(query=query)
        resp['Location'] += getstr
    return resp


class GenericSearchTableView(LoginRequiredMixin,ExportStreamMixin,SingleTableView):
    model = None
    table_class = None
    context_object_name = 'query_objs'
    template_name = 'search/adv_search.html'
    exclude_columns = []
    query_prefetch = []
    choice_fields = {}

    def get_search_cards(self):
        fields = self.request.GET.getlist('f')
        lookups = self.request.GET.getlist('l')
        queries = self.request.GET.getlist('q')
        negas = self.request.GET.getlist('n')

        # the +['t'] corresponds to the t of "... for c,r,v,t in ..." below
        fields = [unquote(f).split('.',2)+['f'] for f in fields]
        lookups = [unquote(l).split('.',2)+['l'] for l in lookups]
        queries = [unquote(q).split('.',2)+['q'] for q in queries]
        negas = [unquote(n).split('.',2)+['n'] for n in negas]

        all_things = fields+lookups+queries+negas

        cards = [] # card.row.value.type(flqnc)
        card_IDs = sorted(set([c for c,r,v,t in all_things]))
        for card_id in card_IDs:
            card_things = [(c,r,v,t) for c,r,v,t in all_things if c==card_id]
            row_IDs = sorted(set([r for c,r,v,t in card_things]))
            rows = []
            secret_rows_ANDed =[]
            for row_id in row_IDs:
                row_items = [(v,t) for c,r,v,t in card_things if r==row_id]
                print(row_items)
                fields = [v for v,t in row_items if t=='f']
                lookup = [v for v,t in row_items if t=='l']
                query = [v for v,t in row_items if t=='q']
                nega = [v for v,t in row_items if t=='n']
                try:
                    assert len(fields) >= 1
                    assert len(lookup) == 1
                    assert len(query) == 1
                    assert len(nega) <= 1
                    lookup,query = lookup[0],query[0]
                    multi_bool = len(fields) > 1
                except AssertionError:
                    continue #skip

                # Searching for Null/None field values
                if lookup == 'isnull':
                    query = True if query == 'True' else False

                # querying for empty strings
                if query == '' and lookup not in ['exact','iexact']:
                    continue #skip empty

                # hack: implicitly search for usernames in addition to a user's name
                for f in fields[:]:
                    if 'user__name' in f:
                        extra_f = f.replace('user__name','user__username')
                        fields.append(extra_f)

                row = dict( #row_id=row_id,
                    fields=fields,
                    lookup=lookup,
                    query=query,
                    nega=bool(nega),
                    multi=multi_bool)
                rows.append(row)

                # choice field hack
                for field in self.choice_fields:
                    if field in fields:
                        rows[-1]['secret_subrows'] = [dict(field=field, lookup='exact', query=None)] #ensure at least one, albeit bogus, query
                        for k,v in self.choice_fields[field]:
                            if (lookup[0]=='exact' and query[0]==v) or\
                               (lookup[0]=='icontains' and query[0].lower() in v.lower()):
                                rows[-1]['secret_subrows'].append(dict(field=field, lookup='exact', query=k))

            # TODO placeholder to add more values to given card, like name
            cards.append(dict(card_id=card_id, rows=rows))
        return cards

    def get_queryset(self):
        def userlist_Qkwarg(field,row):
            approver_or_draft = field.split('__')[-3]
            Q_username = Q(**{'username__{}'.format(row['lookup']): row['query']})
            Q_userName = Q(**{'name__{}'.format(row['lookup']): row['query']})
            matching_user_IDs = User.objects.filter(Q_username|Q_userName).values_list('id', flat=True)
            if field.startswith('calibration_events__latest__'):
                cals_with_matching_users__qs = CalibrationEvent.objects.filter(**{approver_or_draft+'__in':matching_user_IDs})
                inv_latest_cal__subQ = Subquery(CalibrationEvent.objects.filter(inventory=OuterRef('pk')).values('pk')[:1])
                all_inv_latest_cal_IDs = Inventory.objects.all().annotate(latest_calib=inv_latest_cal__subQ).values_list('latest_calib', flat=True)
                latest_cals_with_matching_users = cals_with_matching_users__qs.filter(id__in=all_inv_latest_cal_IDs)
                inventory_IDs_for__latest_cals_with_matching_users = latest_cals_with_matching_users.values_list('inventory__pk', flat=True)
                Q_kwarg = {'id__in': inventory_IDs_for__latest_cals_with_matching_users}
                return Q_kwarg

            else:
                calib_or_conf = field.split('__')[0]
                Q_kwarg = { '{}__{}__in'.format(calib_or_conf,approver_or_draft) : matching_user_IDs }
                return Q_kwarg

        def make_Qkwarg(field,row):
            select_ones = ['__latest__', '__last__', '__earliest__', '__first__']
            select_one = [s1 for s1 in select_ones if s1 in field]
            select_one = select_one[0] if select_one else None

            userlist_cases = ['calibration_events__latest__user_approver__any__username',
                              'calibration_events__latest__user_draft__any__username',
                              'calibration_event__user_approver__any__username',
                              'calibration_event__user_draft__any__username',
                              'config_event__user_approver__any__username',
                              'config_event__user_draft__any__username']

            if field in userlist_cases:
                return userlist_Qkwarg(field,row)

            elif not select_one:
                # default
                Q_kwarg = {'{field}__{lookup}'.format(field=field, lookup=row['lookup']): row['query']}
                if field.endswith('__count'):
                    # if field is a count, make sure model_objects is anottated appropriately
                    accessor = field.rsplit('__count', 1)[0]
                    annote_obj = {field: Count(accessor)}
                    self.model.objects = self.model.objects.annotate(**annote_obj)
                    Q_kwarg = {'{field}__{lookup}'.format(field=field, lookup=row['lookup']): int(float(row['query']))}
                return Q_kwarg

            else:
                # sometimes we want to query on the latest or first or last value of a list of values.
                # eg. get inventory where inventory.latest_action.user == 'bob'. This is how we do that.

                # TODO: consider implementing "is_current" field for actions+calibrations, similar to UDF.FieldValue.is_current
                # TODO: see https://simpleisbetterthancomplex.com/tips/2016/08/16/django-tip-11-custom-manager-with-chainable-querysets.html
                accessor, subfields = field.split(select_one)
                Accessor = getattr(self.model, accessor).field.model
                reverse_accessor = getattr(self.model, accessor).field.name
                fetch_me = ['__'.join(subfields.split('__')[:i]) for i in range(1, len(subfields.split('__')))]
                fetch_me += [reverse_accessor]

                inv_actions = Accessor.objects.filter(**{reverse_accessor: OuterRef('pk')})
                if select_one in ['__first__', '__latest__']:
                    # latest is not actually checked against, only model.Meta.ordering order matters
                    inv_actions_subquery = Subquery(inv_actions.values('pk')[:1])
                else:  # __last__ or __earliest__
                    inv_actions_subquery = Subquery(inv_actions.reverse().values('pk')[:1])
                all_model_objs = self.model.objects.all().prefetch_related(accessor)
                all_latest_action_IDs = all_model_objs.annotate(latest_action=inv_actions_subquery).values_list(
                    'latest_action', flat=True)
                all_latest_actions = Accessor.objects.filter(pk__in=all_latest_action_IDs).prefetch_related(*fetch_me)
                matching_latest_actions = all_latest_actions.filter(
                    **{'{}__{}'.format(subfields, row['lookup']): row['query']})
                matched_model_IDs = matching_latest_actions.values_list(reverse_accessor+'__pk', flat=True)

                Q_kwarg = {'id__in': matched_model_IDs}
                return Q_kwarg

        cards = self.get_search_cards()

        final_Qs = []
        for card in cards:
            print('CARD:', card)
            card_Qs = []
            for row in card['rows']:
                Q_kwargs = []
                for field in row['fields']:
                    # eg: Q(<field>__<lookup>=<query>) where eg: field = "part__part_number" and lookup = "icontains"
                    if field in self.choice_fields: continue # handled by secret_subrows
                    Q_kwarg = make_Qkwarg(field,row)
                    Q_kwargs.append(Q_kwarg)

                # choice fields
                if 'secret_subrows' in row:
                    for subrow in row['secret_subrows']:
                        Q_kwarg = make_Qkwarg(subrow['field'], subrow)
                        Q_kwargs.append(Q_kwarg)

                if len(Q_kwargs) > 1:
                    row_Q = reduce(operator.or_,[Q(**Q_kwarg) for Q_kwarg in Q_kwargs])
                elif Q_kwargs:
                    row_Q = Q(**Q_kwargs[0])
                else:
                    row_Q = None
                if row['nega'] and row_Q:
                    row_Q = operator.inv(row_Q)
                if row_Q:
                    card_Qs.append(row_Q)
                # ROW DONE
            if len(card_Qs) > 1:
                card_Q = reduce(operator.and_,card_Qs)
            elif card_Qs:
                card_Q = card_Qs[0]
            else:
                card_Q = None
            if card_Q:
                final_Qs.append(card_Q)
            # CARD DONE

        if len(final_Qs) > 1:
            final_Q = reduce(operator.or_,final_Qs)
        elif final_Qs:
            final_Q = final_Qs[0]
        else:
            final_Q = None

        if final_Q:
            return self.model.objects.filter(final_Q).distinct().prefetch_related(*self.query_prefetch)
        else:
            #if there are no search terms
            return self.model.objects.all().prefetch_related(*self.query_prefetch)


    def get_context_data(self, **kwargs):
        context = super(GenericSearchTableView, self).get_context_data(**kwargs)

        # Cards to initiate previous columns
        cards = self.get_search_cards()
        context['prev_cards'] = json.dumps(cards)
        context['model'] = self.model.__name__

        avail_lookups = [dict(value='icontains',text='Contains'),
                         dict(value='exact',    text='Exact'),
                         dict(value='date',     text='Date'),
                         dict(value='gte',      text='>='),
                         dict(value='lte',      text='<='),
                         dict(value='isnull',   text='Is-Null')]
        context['avail_lookups'] = json.dumps(avail_lookups)

        lcats = dict(
            STR_LOOKUP  = ['contains', 'exact', 'startswith', 'endswith', 'regex',
                           'icontains','iexact','istartswith','iendswith','iregex'],
            NUM_LOOKUP  = ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
            DATE_LOOKUP = ['date', 'year', 'iso_year', 'month', 'day', 'week',
                           'week_day', 'quarter', 'time', 'hour', 'minute', 'second'] +
                           ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
            ITER_LOOKUP=['in']+['icontains', 'exact'],
            EXACT_LOOKUP = ['exact'],
            BOOL_LOOKUP = ['exact','iexact'], )
        lcats = {k:v+['isnull'] for k,v in lcats.items()}
        context['lookup_categories'] = json.dumps(lcats)

        avail_fields_sans_col_args = self.get_avail_fields()
        [field.pop('col_args', None) for field in avail_fields_sans_col_args]
        context['avail_fields'] = json.dumps(avail_fields_sans_col_args)

        # Setting default shown columns based on table_class's Meta.base_shown_cols attrib,
        # and "searchcol-" extra_columns (see get_table_kwargs())
        # For Parts and Inventory, set_column_default_show is overwritten
        # such as to hide UDF colums that don't belong / dont have data.
        context['table'].set_column_default_show(self.get_table_data())

        return context

    @staticmethod
    def get_avail_fields():
        # default, this should be overwritten by non-generic search class views
        avail_fields = [dict(value="id", text="Database ID", legal_lookup='EXACT_LOOKUP')]
        return avail_fields

    def get_table_kwargs(self, field_exceptions=[]):
        # Provides additional parameters to table_class upon instantiation.
        # in this case, adds columns from get_avail_fields().
        # Queried fields are prefixed with "searchcol-"
        # such that they will be shown by default by set_column_default_show

        # exclude cols from download
        try: self.exclude_columns = self.request.GET.get('excluded_columns').strip('"').split(',')
        except AttributeError: self.exclude_columns = []

        extra_cols = []
        queried_fields = []

        for card in self.get_search_cards():
            for row in card['rows']:
                for field in row['fields']:
                    if field not in field_exceptions:
                        queried_fields.append(field)
        queried_fields = set(queried_fields)

        for field in self.get_avail_fields():
            if field['value'] is not None \
               and field['value'] not in field_exceptions \
               and field['value'] not in self.table_class.Meta.fields:
                if field['value'] in queried_fields:
                    safename = 'searchcol-{}'.format(field['value'])
                else:
                    if 'extracol' in self.request.GET.getlist('skipcol'): continue
                    #safename = 'extracol-{}'.format(field['value'])
                    safename = '{}'.format(field['value'])

                col_args = field['col_args'] if 'col_args' in field else {}
                if 'verbose_name' not in col_args:
                    col_args['verbose_name'] = field['text']

                render_func = col_args.pop('render',None)

                if 'DATE_LOOKUP' == field['legal_lookup']:
                    col = tables.DateTimeColumn(accessor=field['value'], **col_args)
                elif 'BOOL_LOOKUP' == field['legal_lookup']:
                    col = tables.BooleanColumn(accessor=field['value'], **col_args)
                elif 'ITER_LOOKUP' == field['legal_lookup']:
                    acc,atts = field['value'].split('__any__',1)
                    atts = atts.replace('__','.')
                    col = tables.ManyToManyColumn(accessor=acc, **col_args, default='',
                            transform=lambda x: rgetattr(x,atts))
                else:
                    col = tables.Column(accessor=field['value'], **col_args)

                if render_func:
                    col.render = render_func

                extra_cols.append( (safename,col) )

        return {'extra_columns':extra_cols}


class InventoryTableView(GenericSearchTableView):
    model = Inventory
    table_class = InventoryTable
    query_prefetch = ['fieldvalues', 'fieldvalues__field', 'part', 'actions', 'actions__user', 'actions__location']
    avail_udf = set()
    choice_fields = {'actions__latest__action_type': Action.ACTION_TYPES}

    @staticmethod
    def get_avail_fields():
        avail_fields = [dict(value="part__name",                     text="Name", legal_lookup='STR_LOOKUP'),
                        dict(value="part__friendly_name",   text="Friendly Name", legal_lookup='STR_LOOKUP'),
                        dict(value="serial_number",         text="Serial Number", legal_lookup='STR_LOOKUP',
                             col_args=dict(attrs={'style':'white-space: nowrap;'},
                                           linkify=dict(viewname="inventory:inventory_detail", args=[tables.A('pk')]))),
                        dict(value="old_serial_number", text="Old Serial Number", legal_lookup='STR_LOOKUP'),
                        dict(value="location__name",             text="Location", legal_lookup='STR_LOOKUP'),
                        dict(value="build__assembly__name",         text="Build", legal_lookup='STR_LOOKUP'),
                        dict(value="created_at",             text="Date Created", legal_lookup='DATE_LOOKUP'),
                        dict(value="updated_at",            text="Date Modified", legal_lookup='DATE_LOOKUP'),

                        dict(value=None, text="--Part--", disabled=True),
                        dict(value="part__part_number",        text="Part Number", legal_lookup='STR_LOOKUP',
                             col_args=dict(verbose_name='Part Number', attrs={'style':'white-space: nowrap;'},
                                           linkify=dict(viewname="parts:parts_detail", args=[tables.A('part__pk')]))),
                        dict(value="part__part_type__name",    text="Part Type",   legal_lookup='STR_LOOKUP'),
                        dict(value="part__revision",         text="Part Revision", legal_lookup='STR_LOOKUP'),
                        dict(value="part__unit_cost",          text="Unit Cost",   legal_lookup='NUM_LOOKUP'),
                        dict(value="part__refurbishment_cost", text="Refurb Cost", legal_lookup='NUM_LOOKUP'),

                        dict(value=None, text="--User-Defined-Fields--", disabled=True),
                        dict(value="fieldvalues__field__field_name", text="UDF Name",  legal_lookup='STR_LOOKUP'),
                        dict(value="fieldvalues__field_value",       text="UDF Value", legal_lookup='STR_LOOKUP'),

                        dict(value=None, text="--Actions--", disabled=True),
                        dict(value="actions__latest__action_type",    text="Latest Action",           legal_lookup='STR_LOOKUP',
                             col_args=dict(render=lambda value: dict(Action.ACTION_TYPES).get(value,value) )),
                        dict(value="actions__latest__user__name",     text="Latest Action: User",     legal_lookup='STR_LOOKUP'),
                        dict(value="actions__latest__created_at",     text="Latest Action: Time",     legal_lookup='DATE_LOOKUP'),
                        dict(value="actions__latest__location__name", text="Latest Action: Location", legal_lookup='STR_LOOKUP'),
                        dict(value="actions__latest__detail",         text="Latest Action: Notes",    legal_lookup='STR_LOOKUP',
                             col_args=dict(render=lambda value: mark_safe(value) )),
                        dict(value="actions__count",                  text="Total Action Count",      legal_lookup='NUM_LOOKUP'),

                        dict(value=None, text="--Calibrations--", disabled=True),
                        dict(value="calibration_events__latest__calibration_date", text="Latest Calibration Event: Date", legal_lookup='DATE_LOOKUP',
                             col_args = dict(format='Y-m-d', linkify=lambda record,value: reverse(viewname="exports:calibration",
                                                                args=[record.calibration_events.latest().pk]) if value else None)),
                        dict(value="calibration_events__latest__user_approver__any__username", text="Latest Calibration Event: Approvers", legal_lookup='ITER_LOOKUP'),
                        dict(value="calibration_events__latest__user_draft__any__username", text="Latest Calibration Event: Reviewers", legal_lookup='ITER_LOOKUP'),
                        dict(value="calibration_events__latest__approved", text="Latest Calibration Event: Approved", legal_lookup='BOOL_LOOKUP'),

                        ]
        return avail_fields

    def get_queryset(self):
        qs = super().get_queryset()
        if not 'on' in self.request.GET.getlist('trashtog'):
            qs = qs.exclude(location__root_type='Trash')
        self.avail_udf.clear()
        [[self.avail_udf.add(fv.field.id) for fv in q.fieldvalues.all()] for q in qs]
        return qs

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs(field_exceptions=self.table_class.Meta.udf_accessors)

        if 'udf' in self.request.GET.getlist('skipcol'):
            return kwargs

        ## UDF ##
        udfname_queries = []
        udfvalue_queries = []
        for card in self.get_search_cards():
            for row in card['rows']:
                if 'fieldvalues__field__field_name' in row['fields']:
                    udfname_queries.append(row['query'])  # capture this row's query
                #elif 'fieldvalues__field_value' in row['fields']:
                #    udfvalue_queries.append(row['query']) # TODO show all UDF that match this ?? How??

        # UDF Cols: these have to be added before the table is made
        # see table_class.set_column_default_show for more
        for udf in Field.objects.all().order_by('id'):

            # don't make a column if no data available for this udf
            if udf.id not in self.avail_udf: continue

            safename =  UDF_Column.prefix+'{:03}'.format(udf.id)
            if any([qry.lower() in udf.field_name.lower() for qry in udfname_queries]):
                safename = 'searchcol-'+safename

            footer_count = 'show-udf-footer-count' in self.request.GET
            bound_coltup = (safename, UDF_Column(udf, accessor='fieldvalues', accessor_type='FieldValue', footer_count=footer_count))
            kwargs['extra_columns'].append( bound_coltup )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trashtog = 'checked' if 'on' in self.request.GET.getlist('trashtog') else 'unchecked'
        context['trashtog'] = json.dumps(trashtog)
        return context

class PartTableView(GenericSearchTableView):
    model = Part
    table_class = PartTable
    avail_udf = set()
    query_prefetch = ['user_defined_fields','part_type']

    @staticmethod
    def get_avail_fields():
        avail_fields = [dict(value="name",                        text="Name", legal_lookup='STR_LOOKUP'),
                        dict(value="friendly_name",      text="Friendly Name", legal_lookup='STR_LOOKUP'),
                        dict(value="part_number",          text="Part Number", legal_lookup='STR_LOOKUP',
                             col_args=dict(verbose_name='Part Number', attrs={'style':'white-space: nowrap;'},
                                           linkify=dict(viewname='parts:parts_detail',args=[tables.A('pk')]))),
                        dict(value="part_type__name",        text="Part Type", legal_lookup='STR_LOOKUP',
                             col_args=dict(verbose_name='Type')),
                        dict(value="revision",           text="Part Revision", legal_lookup='STR_LOOKUP'),
                        dict(value="unit_cost",              text="Unit Cost", legal_lookup='NUM_LOOKUP'),
                        dict(value="refurbishment_cost",   text="Refurb Cost", legal_lookup='NUM_LOOKUP'),
                        dict(value="note",                       text="Notes", legal_lookup='STR_LOOKUP'),
                        dict(value="inventory__count", text="Inventory Count", legal_lookup='NUM_LOOKUP',
                             col_args=dict(linkify=lambda record: reverse(viewname="search:inventory")+\
                                      '?f=.0.part__part_number&l=.0.exact&q=.0.{}'.format(record.part_number))),

                        dict(value=None, text="--User-Defined-Fields--", disabled=True),
                        dict(value="user_defined_fields__field_name", text="UDF Name", legal_lookup='STR_LOOKUP'),]
        return avail_fields

    def get_queryset(self):
        qs = super().get_queryset()
        self.avail_udf.clear()
        [[self.avail_udf.add(udf.id) for udf in q.user_defined_fields.all()] for q in qs]
        return qs

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs(field_exceptions=['user_defined_fields__field_name'])

        if 'udf' in self.request.GET.getlist('skipcol'):
            return kwargs

        udfname_queries = []
        for card in self.get_search_cards():
            for row in card['rows']:
                if 'user_defined_fields__field_name' in row['fields']:
                    udfname_queries.append(row['query'])  # capture this row's query

        # UDF Cols: these have to be added before the table is made
        # see table_class.set_column_default_show for more
        for udf in Field.objects.all().order_by('id'):

            # don't make a column if no data available for this udf
            if udf.id not in self.avail_udf: continue

            safename =  UDF_Column.prefix+'{:03}'.format(udf.id)
            if any([qry.lower() in udf.field_name.lower() for qry in udfname_queries]):
                safename = 'searchcol-'+safename

            footer_count = 'show-udf-footer-count' in self.request.GET
            bound_coltup = (safename, UDF_Column(udf, accessor='user_defined_fields',footer_count=footer_count))
            kwargs['extra_columns'].append( bound_coltup )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class BuildTableView(GenericSearchTableView):
    model = Build
    table_class = BuildTable
    query_prefetch = ['assembly','assembly__assembly_type','actions','actions__user']
    choice_fields = {'actions__latest__action_type': Action.ACTION_TYPES}

    @staticmethod
    def get_avail_fields():
        avail_fields = [dict(value="assembly__name",                text="Name", legal_lookup='STR_LOOKUP'),
                        dict(value="build_number",          text="Build Number", legal_lookup='STR_LOOKUP'),
                        dict(value="assembly__assembly_type__name", text="Type", legal_lookup='STR_LOOKUP'),
                        dict(value="location__name",            text="Location", legal_lookup='STR_LOOKUP'),
                        dict(value="assembly__description",  text="Description", legal_lookup='STR_LOOKUP'),
                        dict(value="build_notes",                  text="Notes", legal_lookup='STR_LOOKUP'),
                       #dict(value="time_at_sea",            text="Time at Sea", legal_lookup='NUM_LOOKUP'),
                        dict(value="is_deployed",           text="is-deployed?", legal_lookup='BOOL_LOOKUP'),
                        dict(value="flag",                   text="is-flagged?", legal_lookup='BOOL_LOOKUP'),
                        dict(value="created_at",            text="Date Created", legal_lookup='DATE_LOOKUP'),
                        dict(value="updated_at",           text="Date Modified", legal_lookup='DATE_LOOKUP'),

                        dict(value=None, text="--Actions--", disabled=True),
                        dict(value="actions__latest__action_type",    text="Latest Action",           legal_lookup='STR_LOOKUP',
                             col_args=dict(render=lambda value: dict(Action.ACTION_TYPES).get(value,value))),
                        dict(value="actions__latest__user__name",     text="Latest Action: User",     legal_lookup='STR_LOOKUP'),
                        dict(value="actions__latest__created_at",     text="Latest Action: Time",     legal_lookup='DATE_LOOKUP'),
                        dict(value="actions__latest__location__name", text="Latest Action: Location", legal_lookup='STR_LOOKUP'),
                        dict(value="actions__latest__detail",         text="Latest Action: Notes",    legal_lookup='STR_LOOKUP',
                             col_args=dict(render=lambda value: mark_safe(value) )),
                        dict(value="actions__count",                  text="Total Action Count",      legal_lookup='NUM_LOOKUP'),
                        ]
        return avail_fields

    def get_queryset(self):
        qs = super().get_queryset()
        if not 'on' in self.request.GET.getlist('trashtog'):
            qs = qs.exclude(location__root_type='Trash')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trashtog = 'checked' if 'on' in self.request.GET.getlist('trashtog') else 'unchecked'
        context['trashtog'] = trashtog
        return context


class AssemblyTableView(GenericSearchTableView):
    model = Assembly
    table_class = AssemblyTable
    query_prefetch = ['assembly_type']

    @staticmethod
    def get_avail_fields():
        avail_fields = [dict(value="name",                text="Name", legal_lookup='STR_LOOKUP'),
                        dict(value="assembly_number",   text="Number", legal_lookup='STR_LOOKUP',
                             col_args=dict(verbose_name='Assembly Number', attrs={'style':'white-space: nowrap;'},
                                           linkify=dict(viewname='assemblies:assembly_detail',args=[tables.A('pk')]))),
                        dict(value="assembly_type__name", text="Type", legal_lookup='STR_LOOKUP',
                             col_args=dict(verbose_name='Type')),
                        dict(value="description",  text="Description", legal_lookup='STR_LOOKUP'),
                        ]
        return avail_fields

    def get_queryset(self):
        qs = super().get_queryset()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context



class ActionTableView(GenericSearchTableView):
    model = Action
    table_class = ActionTable
    query_prefetch = ['user','inventory','inventory__part','cruise','build','build__assembly_revision__assembly','deployment']
    choice_fields = {'action_type': Action.ACTION_TYPES}

    @staticmethod
    def get_avail_fields():
        avail_fields = [dict(value="object_type", text="Object Type", legal_lookup='STR_LOOKUP'),
                        dict(value="action_type", text="Action Type", legal_lookup='STR_LOOKUP'),
                        dict(value="user__name", text="User", legal_lookup='STR_LOOKUP'),
                        dict(value="created_at", text="Timestamp", legal_lookup='DATE_LOOKUP'),
                        dict(value="detail", text="Detail", legal_lookup='STR_LOOKUP'),
                        dict(value="location__name",text="Location",legal_lookup='STR_LOOKUP'),
                        dict(value="inventory__serial_number", text="Inventory: Serial Number", legal_lookup='STR_LOOKUP'),
                        dict(value="inventory__part__name", text="Inventory: Name", legal_lookup='STR_LOOKUP'),
                        dict(value="build__assembly_revision__assembly__name", text="Build Assembly", legal_lookup='STR_LOOKUP'),
                        dict(value="build__build_number", text="Build Number", legal_lookup='STR_LOOKUP'),
                        dict(value="deployment__deployment_number", text="Deployment Number", legal_lookup='STR_LOOKUP'),
                        dict(value="cruise__CUID", text="Deployed Cruise: ID", legal_lookup='STR_LOOKUP'),
                        dict(value="cruise__friendly_name", text="Deployed Cruise: Name", legal_lookup='STR_LOOKUP'),
                        ]
        return avail_fields
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class CalibrationTableView(GenericSearchTableView):
    model = CoefficientValueSet
    table_class = CalibrationTable
    query_prefetch = ['coefficient_name','calibration_event','calibration_event__inventory','calibration_event__inventory__part','calibration_event__user_approver','calibration_event__user_draft']

    @staticmethod
    def get_avail_fields():
        avail_fields = [dict(value="calibration_event__inventory__serial_number", text="Inventory: SN", legal_lookup='STR_LOOKUP'),
                        dict(value="calibration_event__inventory__part__name", text="Inventory: Name", legal_lookup='STR_LOOKUP'),
                        dict(value="coefficient_name__calibration_name", text="Coefficient Name", legal_lookup='STR_LOOKUP'),
                        dict(value="calibration_event__calibration_date", text="Calibration Event: Date", legal_lookup='DATE_LOOKUP'),
                        dict(value="calibration_event__user_approver__any__username", text="Calibration Event: Approvers", legal_lookup='ITER_LOOKUP'),
                        dict(value="calibration_event__user_draft__any__username", text="Calibration Event: Reviewers", legal_lookup='ITER_LOOKUP'),
                        dict(value="calibration_event__approved", text="Calibration Event: Approved Flag", legal_lookup='BOOL_LOOKUP'),
                        #dict(value="calibration_event__created_at", text="Date Entered", legal_lookup='DATE_LOOKUP'),
                        dict(value="value_set", text="Value", legal_lookup='STR_LOOKUP'),
                        dict(value="notes", text="Notes", legal_lookup='STR_LOOKUP'),
                        #dict(value="calibration_event__is_current", text="Latest Only", legal_lookup='BOOL_LOOKUP'),
                        ]
        return avail_fields
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model'] = 'Calibrations'
        return context
    def get_queryset(self):
        qs = super().get_queryset()
        # since search model is CoefficientValueSet and results table is CalibrationEvents,
        # final query results must be CalibrationEvents.
        calibration_event_ids = qs.values_list('calibration_event__id', flat=True)
        qs = CalibrationEvent.objects.filter(id__in=calibration_event_ids)
        qs = qs.prefetch_related(*[pf.replace('calibration_event__','') for pf in self.query_prefetch if pf.startswith('calibration_event__')])
        qs = qs.select_related('inventory__part__part_type').exclude(inventory__part__part_type__ccc_toggle=False)
        return qs
    def get_table_kwargs(self):
        # since search model is CoefficientValueSet and results are CalibrationEvents,
        # columns must be handled by table_class, not by view_class/avail_fields

        # exclude cols from download
        try: self.exclude_columns = self.request.GET.get('excluded_columns').strip('"').split(',')
        except AttributeError: self.exclude_columns = []

        return {'extra_columns':[]}

class ConfigConstTableView(GenericSearchTableView):
    model = ConfigValue
    table_class = ConfigConstTable
    query_prefetch = ['config_name','config_event','config_event__inventory','config_event__inventory__part','config_event__user_approver','config_event__user_draft']

    @staticmethod
    def get_avail_fields():
        avail_fields = [dict(value="config_event__inventory__serial_number", text="Inventory: SN", legal_lookup='STR_LOOKUP'),
                        dict(value="config_event__inventory__part__name", text="Inventory: Name", legal_lookup='STR_LOOKUP'),
                        dict(value="config_name__name", text="Config/Const Name", legal_lookup='STR_LOOKUP'),
                        dict(value="config_event__configuration_date", text="Config/Const Event: Date", legal_lookup='DATE_LOOKUP'),
                        dict(value="config_event__user_approver__any__username", text="Config/Const Event: Approvers", legal_lookup='ITER_LOOKUP'),
                        dict(value="config_event__user_draft__any__username", text="Config/Const Event: Reviewers", legal_lookup='ITER_LOOKUP'),
                        dict(value="config_event__approved", text="Config/Const Event: Approved Flag", legal_lookup='BOOL_LOOKUP'),
                        #dict(value="config_event__created_at", text="Date Entered", legal_lookup='DATE_LOOKUP'),
                        dict(value="config_value", text="Value", legal_lookup='STR_LOOKUP'),
                        dict(value="notes", text="Notes", legal_lookup='STR_LOOKUP'),
                        ]
        return avail_fields
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model'] = 'Configs_Constants'
        return context
    def get_queryset(self):
        qs = super().get_queryset()
        # since search model is CoefficientValueSet and results table is CalibrationEvents,
        # final query results must be CalibrationEvents.
        config_event_ids = qs.values_list('config_event__id', flat=True)
        qs = ConfigEvent.objects.filter(id__in=config_event_ids)
        qs = qs.prefetch_related(*[pf.replace('config_event__','') for pf in self.query_prefetch if pf.startswith('config_event__')])
        qs = qs.select_related('inventory__part__part_type').exclude(inventory__part__part_type__ccc_toggle=False)
        return qs
    def get_table_kwargs(self):
        # since search model is ConfigValue and results are ConfigEvents,
        # columns must be handled by table_class, not by view_class/avail_fields

        # exclude cols from download
        try: self.exclude_columns = self.request.GET.get('excluded_columns').strip('"').split(',')
        except AttributeError: self.exclude_columns = []

        return {'extra_columns':[]}

