'use strict';

// Liberally based on:
// https://carlschwan.eu/2020/12/29/adding-comments-to-your-static-blog-with-mastodon/

// Uses DOMPurify:
// https://github.com/cure53/DOMPurify

var comments_loaddelay = 1000;
// page must set the "fediserver" and "fedipostid" globals

if (window.onloadlist == undefined) {
    window.onloadlist = [ handle_comments_onload ];
}
else {
    window.onloadlist.push(handle_comments_onload);
}

function handle_comments_onload() {
    if (window.fedipostid == undefined) {
        display_comment_status('No fedipostid found!');
        return;
    }

    display_comment_status('Loading...');

    setTimeout(handle_comments_doload, comments_loaddelay);
}

function handle_comments_doload()
{
    var url = 'https://'+fediserver+'/api/v1/statuses/'+fedipostid+'/context';
    
    fetch(url).then(function(response) {
        return response.json();
    }).then(handle_response, handle_failure);
}

function handle_failure(data)
{
    display_comment_status('Unable to load: ' + data.message);
}

function handle_response(obj)
{
    if (obj['error']) {
        display_comment_status('Unable to load: ' + obj['error']);
        return;
    }

    var nod = document.getElementById('livereplyblock');
    nod.classList.remove('Hidden');

    var idmap = new Map();
    idmap.set(fedipostid, { _replies: [] });
              
    for (var el of obj['descendants']) {
        idmap.set(el.id, el);
    }

    var depthstep = function(val) {
        if (!val)
            return '0';
        var res = 2.54 * Math.atan(val);
        res = ''+res;
        return res.substring(0,5);
    }

    DOMPurify.addHook('afterSanitizeAttributes', function (nod) {
        if (nod.tagName.toLowerCase() == 'a' && nod.hasAttribute('href')) {
            nod.setAttribute('rel', 'nofollow noopener noreferrer');
        }
    });

    for (var el of obj['descendants']) {
        var parid = el.in_reply_to_id;
        if (!idmap.has(parid)) {
            console.log('message '+el.id+' in reply to '+parid+', which is not known');
            continue;
        }
        var par = idmap.get(parid);
        if (par._replies == null) {
            par._replies = [ el ];
        }
        else {
            par._replies.push(el);
        }

        el._authorname = 'anonymous';
        el._authoruri = null;
        if (el.account != null) {
            if (el.account.display_name != null)
                el._authorname = el.account.display_name;
            if (el.account.url)
                el._authoruri = el.account.url;
        }

        // This doesn't match the Python date output, sorry.
        // It's also browser-local time instead of Eastern.
        var date = new Date(el.created_at);
        el._longpublished = date.toLocaleString();

        el._body = DOMPurify.sanitize(el.content, {
            RETURN_DOM_FRAGMENT: true,
            FORBID_TAGS: ['style'],
        });
    }

    DOMPurify.removeHook('afterSanitizeAttributes');
    
    var flatls = [];

    function func(ls, depth) {
        for (var el of ls) {
            flatls.push(el);
            el._depth = depth;
            if (el._replies != null) {
                func(el._replies, depth+1);
            }
        }
    }

    func(idmap.get(fedipostid)._replies, 0);

    document.getElementById('livecommentload').textContent = '';
    
    var parnod = document.getElementById('livecommentblock');

    if (flatls.length == 0) {
        var nod = document.createElement('div');
        nod.textContent = '(No comments in this thread.)';
        parnod.appendChild(nod);
        return;
    }

    var index = 0;
    
    for (var el of flatls) {
        var comnod = document.createElement('div');
        comnod.id = 'comment-live-' + index;
        comnod.className = 'Comment';
        comnod.setAttribute('role', 'comment');
        var depth = depthstep(el._depth);
        comnod.setAttribute('style', 'margin-left: '+depth+'em;');
        
        var nod = document.createElement('hr');
        comnod.appendChild(nod);

        nod = document.createElement('div');
        nod.className = 'CommentHead';
        var span;
        if (el._authoruri) {
            span = document.createElement('a');
            span.setAttribute('rel', 'nofollow noopener noreferrer');
            span.setAttribute('href', el._authoruri);
        }
        else {
            span = document.createElement('span');
        }
        span.className = 'CommentAuthor';
        span.textContent = el._authorname;
        nod.appendChild(span);
        var span = document.createElement('span');
        span.textContent = ' ('+el._longpublished+')';
        nod.appendChild(span);
        comnod.appendChild(nod);

        comnod.appendChild(el._body);

        parnod.appendChild(comnod);
        index++;
    }
}

function display_comment_status(msg)
{
    document.getElementById('livecommentload').textContent = msg;
}

function handle_comments_showreply(ev)
{
    ev.stopPropagation();
    ev.preventDefault();
    
    var nod = document.getElementById('livereply');
    nod.classList.remove('Hidden');
}

function handle_comments_copyurl(ev)
{
    ev.stopPropagation();
    ev.preventDefault();
    
    var val = 'https://'+fediserver+'/@'+fediuser+'/'+fedipostid;
    navigator.clipboard.writeText(val);
    document.getElementById('replycommenturl').select();
}

