#!/bin/bash

scripts_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
code_dir="${scripts_dir}/.."

#declare -a file_type_list = ("py_yml" "js_css" "html")

for file_type in "py_yml" "js_css" "html"
#for file_type in "${file_type_list[@]}"
do
    echo "$file_type"
    
    # all .py, .yml, .js., .css, and .html files
    case $file_type in
        
        py_yml)
            comment_start = '"""'
            comment_end = '"""'
            regex_match = 'py\|yml\'
            ;;
        js_css)
            comment_start = '/*'
            comment_end = '*/'
            regex_match = 'js\|css\'
            ;;
        html)
            comment_start = '<!--'
            comment_end = '-->'
            regex_match = 'html\'
            ;;
        *) # default to C/C++ commenting (already in header file)
            comment_start = ''
            comment_end = ''
            regex_match = 'h\|cpp\|c\'
            ;;
    esac
    
    find $code_dir -regex '.*/.*\.\($regex_match)' | while read -r file; do    

        if [ "$file" != "__init__.py" ];

           endtext='If not, see <http:\/\/www.gnu.org\/licenses\/>.'
           l=$(grep -n "$endtext" $file | tail -1 | cut -d ":" -f 1)    
           if [[ $l == "" ]]; then
               l=0
           else
               l=$(($l+1))
           fi
           tail -n +$l $file | sed '/./,$!d' > /tmp/copyright_tmp

           cat $comment_start $code_dir/docs/copyright/gpl2_and_later_header.txt $comment_end /tmp/copyright_tmp > $file
           
           rm /tmp/copyright_tmp 
           
           echo "Updated" `realpath $file`
           
        fi
    done
done
