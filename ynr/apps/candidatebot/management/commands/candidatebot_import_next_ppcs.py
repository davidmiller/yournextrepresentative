import csv

import requests

from django.core.management.base import BaseCommand
from django.db import transaction

from elections.models import Election
from people.models import Person
from parties.models import Party
from popolo.models import Membership, NotStandingValidationError


class Command(BaseCommand):
    help = "Import candidates to the next parl election from a Google sheet"

    def add_arguments(self, parser):
        parser.add_argument("--sheet-url", action="store", required=True)

    def get_next_parl_election(self):
        election = (
            Election.objects.filter(slug__contains="parl.")
            .future()
            .order_by("election_date")
            .first()
        )
        if not election:
            raise ValueError("No future parl election found!")

    @transaction.atomic()
    def handle(self, *args, **options):
        self.ballot_cache = {}
        self.party_cache = {}
        self.election = self.get_next_parl_election()
        req = requests.get(options["sheet_url"])
        req.raise_for_status()
        self.parse_csv(req.text)
        raise ValueError("Still testing")

    def parse_csv(self, in_file):
        csv_data = csv.DictReader(in_file.splitlines())
        for line in csv_data:
            self.import_line(line)

    def get_person_from_line(self, line, ballot, party):
        url = line.get("Existing Candidate Profile URL")
        if url:
            # Someone in the sheet has asserted that this is the same person
            # who are we to doubt them?
            person_id = url.split("/")[4]
            try:
                return Person.objects.get(pk=person_id)
            except Person.DoesNotExist:
                return None
        else:
            # All we have is a name. We might create a duplicate person,
            # but we absolutly don't want to make a duplotate person on this
            # ballot. We also have to consider that names might change, or be
            # duplicated on a ballot, so we can't just rely on name alone. Use
            # party too, and accept that there is an error margin. We'll mop
            # this up manually, or at least when the SOPNs are out
            name = line["Candidate Name"]
            # First, find all the people standing for this party and ballot:
            memberships_qs = Membership.objects.filter(
                ballot=ballot, party=party
            )

            exact_name_match = memberships_qs.filter(person__name=name)
            if exact_name_match.exists():
                return exact_name_match.get().person

            other_name_match = memberships_qs.filter(
                person__other_names__name=name
            )
            if other_name_match.exists():
                return other_name_match.get().person

            # If we get here, it looks like we need to create a new person
            # This can always be undone with a merge later
            print(name)
            return Person.objects.create(name=name)

    def get_ballot_from_line(self, line):
        ballot_paper_start = (
            ".".join(line["Ballot paper ID"].split(".")[0:-1]) + "."
        )
        if ballot_paper_start not in self.ballot_cache:
            self.ballot_cache[
                ballot_paper_start
            ] = self.election.ballot_set.get(
                ballot_paper_id__startswith=ballot_paper_start
            )
        return self.ballot_cache[ballot_paper_start]

    def get_party_from_line(self, line):
        party_id = line["Party ID"]
        if party_id not in self.party_cache:
            try:
                self.party_cache[party_id] = Party.objects.get(ec_id=party_id)
            except Party.DoesNotExist:
                print(line)
                raise ValueError("Party not found in line")
        return self.party_cache[party_id]

    def line_has_values(self, line):
        """
        Some lines exist that only have a ballot ID and no actual membership
        info
        """
        return any(
            (line["Candidate Name"], line["Existing Candidate Profile URL"])
        )

    def import_line(self, line):
        if not self.line_has_values(line):
            return
        party = self.get_party_from_line(line)
        ballot = self.get_ballot_from_line(line)
        person = self.get_person_from_line(line, ballot, party)
        if person:
            try:
                Membership.objects.update_or_create(
                    person=person, ballot=ballot, defaults={"party": party}
                )
            except (Membership.DoesNotExist, NotStandingValidationError) as e:
                print(
                    "Error creating membership for line {} ({})".format(line, e)
                )
            except:
                import ipdb

                ipdb.set_trace()
