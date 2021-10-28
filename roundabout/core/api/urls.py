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

from django.urls import path, include
from rest_framework.authtoken.views import *
from rest_framework.routers import DefaultRouter

from roundabout.assemblies.api.views import (
    AssemblyViewSet,
    AssemblyRevisionViewSet,
    AssemblyPartViewSet,
    AssemblyTypeViewSet,
)
from roundabout.builds.api.views import (
    BuildViewSet,
    DeploymentViewSet,
    DeploymentOmsCustomViewSet,
    DeploymentOmsCustom2ViewSet,
)
from roundabout.calibrations.api.views import *
from roundabout.configs_constants.api.views import *
from roundabout.cruises.api.views import CruiseViewSet, VesselViewSet
from roundabout.inventory.api.views import (
    InventoryViewSet,
    InventoryDeploymentViewSet,
    ActionViewSet,
    PhotoNoteViewSet,
)
from roundabout.locations.api.views import LocationViewSet
from roundabout.parts.api.views import (
    PartViewSet,
    PartTypeViewSet,
    RevisionViewSet,
    DocumentationViewSet,
)
from roundabout.userdefinedfields.api.views import FieldViewSet, FieldValueViewSet
from roundabout.users.api.views import UserViewSet
from roundabout.ooi_ci_tools.api.views import (
    ReferenceDesignatorViewSet,
    ReferenceDesignatorEventViewSet,
    CiRefDesDeploymentCustomViewSet,
)

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"inventory", InventoryViewSet, "inventory")
router.register(
    r"inventory-deployments", InventoryDeploymentViewSet, "inventory-deployments"
)

router.register(r"builds", BuildViewSet, "builds")
router.register(r"deployments", DeploymentViewSet, "deployments")
router.register(r"oms-builds", DeploymentOmsCustomViewSet, "oms-builds")
router.register(r"oms-builds-v2", DeploymentOmsCustom2ViewSet, "oms-builds-v2")
router.register(r"cruises", CruiseViewSet, "cruises")
router.register(r"vessels", VesselViewSet, "vessels")

router.register(r"locations", LocationViewSet, "locations")

router.register(r"part-templates/parts", PartViewSet, "part-templates/parts")
router.register(
    r"part-templates/part-types", PartTypeViewSet, "part-templates/part-types"
)
router.register(
    r"part-templates/revisions", RevisionViewSet, "part-templates/revisions"
)
router.register(
    r"part-templates/documents", DocumentationViewSet, "part-templates/documents"
)

router.register(
    r"assembly-templates/assemblies", AssemblyViewSet, "assembly-templates/assemblies"
)
router.register(
    r"assembly-templates/assembly-revisions",
    AssemblyRevisionViewSet,
    "assembly-templates/assembly-revisions",
)
router.register(
    r"assembly-templates/assembly-types",
    AssemblyTypeViewSet,
    "assembly-templates/assembly-types",
)
router.register(
    r"assembly-templates/assembly-parts",
    AssemblyPartViewSet,
    "assembly-templates/assembly-parts",
)

router.register(
    r"calibrations/calibration-events",
    CalibrationEventViewSet,
    "calibrations/calibration-events",
)
router.register(
    r"calibrations/coefficent-name-events",
    CoefficientNameEventViewSet,
    "calibrations/coefficent-name-events",
)
router.register(
    r"calibrations/coefficent-names",
    CoefficientNameViewSet,
    "calibrations/coefficent-names",
)
router.register(
    r"calibrations/coefficent-value-sets",
    CoefficientValueSetViewSet,
    "calibrations/coefficent-value-sets",
)
router.register(
    r"calibrations/coefficent-values",
    CoefficientValueViewSet,
    "calibrations/coefficent-values",
)

router.register(
    r"configs-constants/config-events",
    ConfigEventViewSet,
    "configs-constants/config-events",
)
router.register(
    r"configs-constants/config-name-events",
    ConfigNameEventViewSet,
    "configs-constants/config-name-events",
)
router.register(
    r"configs-constants/config-names",
    ConfigNameViewSet,
    "configs-constants/config-names",
)
router.register(
    r"configs-constants/config-values",
    ConfigValueViewSet,
    "configs-constants/config-values",
)
router.register(
    r"configs-constants/const-default-events",
    ConstDefaultEventViewSet,
    "configs-constants/const-default-events",
)
router.register(
    r"configs-constants/const-defaults",
    ConstDefaultViewSet,
    "configs-constants/const-defaults",
)
router.register(
    r"configs-constants/config-default-events",
    ConfigDefaultEventViewSet,
    "configs-constants/config-default-events",
)
router.register(
    r"configs-constants/config-defaults",
    ConfigDefaultViewSet,
    "configs-constants/config-defaults",
)

router.register(r"actions", ActionViewSet, "actions")
router.register(r"photos", PhotoNoteViewSet, "photos")

router.register(
    r"user-defined-fields/fields", FieldViewSet, "user-defined-fields/fields"
)
router.register(
    r"user-defined-fields/field-values",
    FieldValueViewSet,
    "user-defined-fields/field-values",
)

router.register(r"users", UserViewSet, "users")

router.register(
    r"reference-designator-events",
    ReferenceDesignatorEventViewSet,
    "reference-designator-events",
)
router.register(
    r"reference-designators", ReferenceDesignatorViewSet, "reference-designators"
)
router.register(
    r"ci-deployment-refdes", CiRefDesDeploymentCustomViewSet, "ci-deployment-refdes"
)

app_name = "api_v1"
urlpatterns = [
    path("", include(router.urls)),
    path("api-token-auth/", obtain_auth_token),
]
