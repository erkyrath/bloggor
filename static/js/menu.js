'use strict';

function handle_menu_button(ev)
{
    ev.stopPropagation();
    ev.preventDefault();
    console.log('###', ev);
    return true;
}
