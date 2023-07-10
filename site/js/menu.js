'use strict';

var menuopen = false;

function handle_menu_button(ev)
{
    ev.stopPropagation();
    ev.preventDefault();
    if (!menuopen) {
        menuopen = true;
        var nod = document.getElementById('menucolumn');
        nod.textContent = '';
        var newnod = document.getElementById('sidebar').cloneNode(true);
        newnod.id = 'sidebarclone';
        newnod.className = 'MenuContent Sidebar';
        nod.insertBefore(newnod, null);
        document.body.classList.add('MenuOpen');
    }
    else {
        menuopen = false;
        document.body.classList.remove('MenuOpen');
        var nod = document.getElementById('menucolumn');
        nod.textContent = '';
    }
    return true;
}
