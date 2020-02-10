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


message_newline() {
    echo
}

message_debug()
{
    echo -e "DEBUG: ${@}"
}

message_welcome()
{
    echo -e "\e[1m${@}\e[0m"
}

message_warning()
{
    echo -e "\e[33mWARNING\e[0m: ${@}"
}

message_error()
{
    echo -e "\e[31mERROR\e[0m: ${@}"
}

message_info()
{
    echo -e "\e[37mINFO\e[0m: ${@}"
}

message_suggestion()
{
    echo -e "\e[33mSUGGESTION\e[0m: ${@}"
}

message_success()
{
    echo -e "\e[32mSUCCESS\e[0m: ${@}"
}
