from __future__ import unicode_literals

import random

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView
from django.db.models import F

from candidates.views.mixins import ContributorsMixin
from candidates.models import PostExtra, PostExtraElection
from tasks.models import PersonTask


from elections.models import Election

from ..forms import PostcodeForm
from elections.uk.geo_helpers import (
    get_post_elections_from_postcode, get_post_elections_from_coords
)


class HomePageView(ContributorsMixin, FormView):
    template_name = 'candidates/finder.html'
    form_class = PostcodeForm

    @method_decorator(cache_control(max_age=(60 * 10)))
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(HomePageView, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        if self.request.method == 'GET' and 'q' in self.request.GET:
            return {
                'data': self.request.GET,
                'initial': self.get_initial(),
                'prefix': self.get_prefix(),
            }
        else:
            return super(HomePageView, self).get_form_kwargs()

    def get(self, request, *args, **kwargs):
        if 'q' in request.GET:
            # The treat it like a POST request; we've overridden
            # get_form_kwargs to make sure the GET parameters are used
            # for the form in this case.
            return self.post(request, *args, **kwargs)
        else:
            return super(HomePageView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        postcode = form.cleaned_data['q']
        return HttpResponseRedirect(
            reverse('postcode-view', kwargs={
                'postcode': postcode
            })
        )

    def sopn_progress_by_election_slug_prefix(self, election_slug_prefix):
        election_qs = Election.objects.filter(
            slug__startswith=election_slug_prefix)
        return self.sopn_progress_by_election(election_qs)

    def sopn_progress_by_election(self, election_qs):
        context = {}
        if not election_qs.exists():
            return context
        pee_qs = PostExtraElection.objects.filter(election__in=election_qs)
        context['posts_total'] = pee_qs.count()

        context['sopns_imported'] = pee_qs.filter(
                postextra__base__officialdocument__election=F('election'),
            ).count()
        context['sopns_imported_percent'] = round(
                float(context['sopns_imported']) /
                float(context['posts_total'])
                * 100)

        context['posts_lock_suggested'] = pee_qs.exclude(
            suggestedpostlock=None).count()
        context['posts_locked_suggested_percent'] = round(
                float(context['posts_lock_suggested']) /
                float(context['posts_total'])
                * 100)

        pee_qs = pee_qs.filter(candidates_locked=True)
        context['posts_locked'] = pee_qs.count()
        context['posts_locked_percent'] = round(
                float(context['posts_locked']) /
                float(context['posts_total'])
                * 100)

        return context

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        context['postcode_form'] = kwargs.get('form') or PostcodeForm()
        context['show_postcode_form'] = True
        context['show_name_form'] = False
        context['top_users'] = self.get_leaderboards(all_time=False)[0]['rows'][:8]
        context['recent_actions'] = self.get_recent_changes_queryset()[:5]
        context['election_data'] = Election.objects.current().by_date().last()
        context['hide_search_form'] = True

        from uk_results.models import CouncilElection
        context['council_total'] = CouncilElection.objects.all().count()
        context['council_confirmed'] = CouncilElection.objects.filter(
            confirmed=True).count()

        if context['council_total']:
            context['council_election_percent'] = round(
                float(context['council_confirmed']) /
                float(context['council_total'])
                * 100)
        else:
            context['council_election_percent'] = 0

        from candidates.models import PostExtra
        from uk_results.models import PostElectionResult
        context['votes_total'] = PostExtra.objects.filter(
            postextraelection__election__slug__contains="local").count()
        context['votes_confirmed'] = PostElectionResult.objects.filter(
            confirmed=True).count()

        if float(context['votes_confirmed']):
            context['votes_percent'] = round(
                float(context['votes_confirmed']) /
                float(context['votes_total'])
                * 100)
        else:
            context['votes_percent'] = 0

        # context['council_election_percent'] = council_confirmed / council_total * 100


        election_qs = Election.objects.filter(
            election_date="2017-06-08")
        context['sopn_progress'] = self.sopn_progress_by_election(
            election_qs=election_qs)


        return context

class PostcodeView(TemplateView):
    template_name = "candidates/postcode_view.html"

    def get_context_data(self, **kwargs):
        context = super(PostcodeView, self).get_context_data(**kwargs)
        context['pees'] = get_post_elections_from_postcode(kwargs['postcode'])
        return context


class GeoLocatorView(TemplateView):
    template_name = "candidates/postcode_view.html"

    def get_context_data(self, **kwargs):
        context = super(GeoLocatorView, self).get_context_data(**kwargs)

        latitude = kwargs['latitude']
        longitude = kwargs['longitude']
        coords = ",".join((latitude, longitude))
        context['pees'] = get_post_elections_from_coords(coords)
        # populate the postcode template var with None so the template
        # knows it's a geo-lookup
        context['postcode'] = None
        return context

