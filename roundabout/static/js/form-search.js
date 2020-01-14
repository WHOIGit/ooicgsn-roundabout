
// PLUS SIGN ON_CLICK, show next (index'd) div block + hide that "+" button

// TYPE DROPDOWN ON_SELECT, show the coresponding div block (by index + id), erase value of prev. selection if any

function qfield_show_next(cindex,findex,and_or) {
            let next_row = 'qfield-row_c{{cindex}}_f{{findex}}';
            let prev_buttons = 'qfield-buttons_c{{cindex}}_f{{findex}}';

            next_row = next_row.replace('{{cindex}}',cindex).replace('{{findex}}',findex+1);
            let next_buttons = prev_buttons.replace('{{cindex}}',cindex).replace('{{findex}}',findex+1);
            prev_buttons = prev_buttons.replace('{{cindex}}',cindex).replace('{{findex}}',findex);

            next_row = document.getElementById(next_row);
            next_row.style.display = "block";

            next_buttons = document.getElementById(next_buttons);
            next_buttons.style.display = "block";

            prev_buttons = document.getElementById(prev_buttons);
            prev_buttons.style.display = "none";
        }
