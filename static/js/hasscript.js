'use strict';

var onloadlist = [];

window.addEventListener('load', function(ev) {
    document.body.classList.add('HasScript');

    for (var func of onloadlist) {
        func();
    }
});
