'use strict';

var menuopen = false;

function handle_menu_button(ev)
{
    ev.stopPropagation();
    ev.preventDefault();
    if (!menuopen) {
	menuopen = true;
	document.body.classList.add('MenuOpen');
    }
    else {
	menuopen = false;
	document.body.classList.remove('MenuOpen');
    }
    return true;
}
