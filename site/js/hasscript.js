'use strict';

// Set a body CSS class to indicate that Javascript is available. Also,
// run all the on-load handlers that have been set on the page.
// (This is a very simple hack. jQuery does it better, but I'm not using
// jQuery.)

var onloadlist = [];

window.addEventListener('load', function(ev) {
    document.body.classList.add('HasScript');

    for (var func of onloadlist) {
        func();
    }
});
