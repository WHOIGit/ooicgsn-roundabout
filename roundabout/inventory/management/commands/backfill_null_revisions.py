"""Set Inventory items that have no Revision to their Part's Revision "A".

Dry-run by default; pass --apply to write. Items whose Part has no Revision
(or more than one) with the given code are skipped and listed. Each change is logged in the item's
History as a Revision Change (same as Bulk Import).

    python manage.py backfill_null_revisions            # report only
    python manage.py backfill_null_revisions --apply
"""
from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from roundabout.inventory.models import Inventory
from roundabout.inventory.utils import _create_revision_change_history


class Command(BaseCommand):
    help = "Backfill blank Inventory Revisions to a Revision code (default A)."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Write changes.")
        parser.add_argument("--code", default="A", help="Revision code to set.")

    def handle(self, *args, **opts):
        code, apply = opts["code"], opts["apply"]
        items = (
            Inventory.objects.filter(revision__isnull=True, part__isnull=False)
            .select_related("part")
            .order_by("serial_number")
        )
        updated, skipped, per_part = 0, [], Counter()
        for item in items.iterator():
            matches = list(item.part.revisions.filter(revision_code=code)[:2])
            if len(matches) != 1:
                reason = "no" if not matches else "multiple"
                skipped.append((item, reason))
                continue
            rev = matches[0]
            per_part[item.part.name] += 1
            if apply:
                with transaction.atomic():
                    item.revision = rev
                    item.save()
                    _create_revision_change_history(item, None, rev, None)
            updated += 1

        verb = "Updated" if apply else "Would update"
        self.stdout.write(f"{verb} {updated} item(s) to Revision {code}.")
        for name, n in sorted(per_part.items()):
            self.stdout.write(f"  {n:5d}  {name}")
        self.stdout.write(f"Skipped {len(skipped)} (Part has none or several Revision {code}):")
        for item, reason in skipped:
            self.stdout.write(f"  {item.serial_number} | {item.part.name} | {reason} Rev {code}")
        if not apply:
            self.stdout.write("Dry run only. Re-run with --apply to write.")
