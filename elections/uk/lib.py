from __future__ import unicode_literals

import re

from django.core.exceptions import ObjectDoesNotExist

from popolo.models import Post

from .mapit import get_areas_from_postcode, get_areas_from_coords


def shorten_post_label(post_label):
    result = re.sub(r'^Member of Parliament for ', '', post_label)
    result = re.sub(r'^Member of the Scottish Parliament for ', '', result)
    result = re.sub(r'^Assembly Member for ', '', result)
    result = re.sub(r'^Member of the Legislative Assembly for ', '', result)
    return result


EXTRA_CSV_ROW_FIELDS = [
    'gss_code',
    'parlparse_id',
    'theyworkforyou_url',
    'party_ec_id',
]

def get_extra_csv_values(person, election, post):
    gss_code = ''
    parlparse_id = ''
    theyworkforyou_url = ''
    party_ec_id = ''
    for i in person.identifiers.all():
        if i.scheme == 'uk.org.publicwhip':
            parlparse_id = i.identifier
            m = re.search(r'^uk.org.publicwhip/person/(\d+)$', parlparse_id)
            if not m:
                message = "Malformed parlparse ID found {0}"
                raise Exception(message.format(parlparse_id))
            theyworkforyou_url = 'http://www.theyworkforyou.com/mp/{0}'.format(
                m.group(1)
            )
    for m in person.memberships.all():
        try:
            m_extra = m.extra
        except ObjectDoesNotExist:
            continue
        if not m_extra.election:
            continue
        if m_extra.election != election:
            continue
        expected_role = m_extra.election.candidate_membership_role
        if expected_role != m.role:
            continue
        if m.post != post:
            continue
        # Now m / m_extra should be the candidacy membership:
        for i in m.on_behalf_of.identifiers.all():
            if i.scheme == 'electoral-commission':
                party_ec_id = i.identifier
        for i in m.post.area.other_identifiers.all():
            if i.scheme == 'gss':
                gss_code = i.identifier
        break
    return {
        'gss_code': gss_code,
        'parlparse_id': parlparse_id,
        'theyworkforyou_url': theyworkforyou_url,
        'party_ec_id': party_ec_id
    }


def fetch_area_ids(**kwargs):
    if kwargs['postcode']:
        areas = get_areas_from_postcode(kwargs['postcode'])

    if kwargs['coords']:
        areas = get_areas_from_coords(kwargs['coords'])

    return areas

def fetch_posts_for_area(**kwargs):
    areas = fetch_area_ids(**kwargs)

    area_ids = [area[1] for area in areas]

    posts = Post.objects.filter(
        area__identifier__in=area_ids,
    ).select_related(
        'area', 'area__extra__type', 'organization'
    ).prefetch_related(
        'extra__elections'
    )
    return posts


def is_valid_postcode(postcode):
    outcode_pattern = '[A-PR-UWYZ]([0-9]{1,2}|([A-HIK-Y][0-9](|[0-9]|[ABEHMNPRVWXY]))|[0-9][A-HJKSTUW])'
    incode_pattern = '[0-9][ABD-HJLNP-UW-Z]{2}'
    postcode_regex = re.compile(r'^(GIR 0AA|%s %s)$' % (outcode_pattern, incode_pattern))
    space_regex = re.compile(r' *(%s)$' % incode_pattern)

    postcode = postcode.upper().strip()

    postcode = space_regex.sub(r' \1', postcode)
    if not postcode_regex.search(postcode):
        return False
    return True


def additional_merge_actions(primary_person, secondary_person):
    yield
