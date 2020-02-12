#!/bin/bash

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


# Script to add Copyright/License headers to code:
# .py, .yml, .js., .css, .html, .h, .c, and .cpp files
#
# Note: This script does NOT work on .sh files, so please used
# the header file in
# ooicgsn-roundabout/docs/copyright/gpl2_and_later_header.txt
# to add the header manually to Bash scripts.
#
# This script can be run multiple times, and only one header
# will appear on the affected files.
#
# Usage: ./update_copyright_headers.sh
#

scripts_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
code_dir="${scripts_dir}/.."
header="${code_dir}/docs/copyright/gpl2_and_later_header.txt"

for file_type in "py" "yml" "js_css_h_c_cpp" "html" 
do    
    # all .py, .yml, .js., .css, and .html files
    case $file_type in
        
        py)
            comment_start='"""'
            comment_end='"""'
            regex_match='.*/.*\.\(py\)'
            ;;
        
        yml)
            comment_start='#'
            comment_end='#'
            regex_match='.*/.*\.\(yml\)'
            ;;
        
        js_css_h_c_cpp)
            comment_start='/*'
            comment_end='*/'
            regex_match='.*/.*\.\(js\|css\|h\|c\|cpp\)'
            ;;
        
        html)
            comment_start='<!--'
            comment_end='-->'
            regex_match='.*/.*\.\(html\)'
            ;;
    esac
    
    find $code_dir -regex $regex_match | while read -r file; do    

        if [[ "${file}" != *"__init__.py"* ]]; then # Ignore auto-generated __init__.py
            
            echo -e "$comment_start\n$(cat $header)" > /tmp/copyright_header_tmp
            
            endtext='If not, see <http:\/\/www.gnu.org\/licenses\/>.'
            l=$(grep -n "$endtext" $file | tail -1 | cut -d ":" -f 1)            
            if [[ $l == "" ]]; then
                l=0
                echo -e "$comment_end\n" >> /tmp/copyright_header_tmp
            else
                l=$(($l+1))
            fi
            tail -n +$l $file | sed '/./,$!d' > /tmp/copyright_file_tmp
            
            cat /tmp/copyright_header_tmp /tmp/copyright_file_tmp > $file

            rm /tmp/copyright_header_tmp
            rm /tmp/copyright_file_tmp 
            
            echo "Updated" `realpath $file`
            
        fi
    done
done
