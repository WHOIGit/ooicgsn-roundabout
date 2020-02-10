#!/usr/bin/env bash

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


countdown() {
    declare desc="A simple countdown. Source: https://superuser.com/a/611582"
    local seconds="${1}"
    local d=$(($(date +%s) + "${seconds}"))
    while [ "$d" -ge `date +%s` ]; do
        echo -ne "$(date -u --date @$(($d - `date +%s`)) +%H:%M:%S)\r";
        sleep 0.1
    done
}
