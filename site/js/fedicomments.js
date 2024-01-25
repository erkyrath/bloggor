'use strict';

// Fetch the context of a Mastodon comment (its ancestors and descendants).
// Display the descendants.
// See API: https://docs.joinmastodon.org/entities/Context/

// Liberally based on:
// https://carlschwan.eu/2020/12/29/adding-comments-to-your-static-blog-with-mastodon/

// Uses DOMPurify:
// https://github.com/cure53/DOMPurify

// The page must set the "fediserver", "fediuser", and "fedipostid" globals.
// Also fedicommentids, which should be null or an array of strings.

var comments_loaddelay = 500;
var image_thumbsize = 200;

// window.onloadlist isn't a real thing; it's just a hack I use elsewhere on this site. If you copy this script, use a load eventListener.
if (window.onloadlist == undefined) {
    window.onloadlist = [ handle_comments_onload ];
}
else {
    window.onloadlist.push(handle_comments_onload);
}

// Begin the loading process half a second from now.
function handle_comments_onload() {
    if (window.fedipostid == undefined) {
        display_comment_status('No fedipostid found!');
        return;
    }

    display_comment_status('Loading...');

    setTimeout(handle_comments_doload, comments_loaddelay);
}

// Begin the loading process for real.
function handle_comments_doload()
{
    var url = 'https://'+fediserver+'/api/v1/statuses/'+fedipostid+'/context';
    console.log('Loading '+url);
    
    fetch(url).then(function(response) {
        return response.json();
    }).then(handle_response, handle_failure);
}

// Some failures come here, from the fetch promise failing.
function handle_failure(data)
{
    display_comment_status('Unable to load: ' + data.message);
}

// Handle a successful response.
function handle_response(obj)
{
    if (obj['error']) {
        // Some responses are errors after all.
        display_comment_status('Unable to load: ' + obj['error']);
        return;
    }

    // We now have the comment thread info. Everything after this point is DOM juggling to get it displayed.
    
    var nod = document.getElementById('livereplyblock');
    nod.classList.remove('Hidden');

    // Build a tree of replies, so we can indent properly.
    
    var idmap = new Map();
    idmap.set(fedipostid, { _replies: [] });
              
    for (var el of obj['descendants']) {
        idmap.set(el.id, el);
    }

    // Baked-in comments; we don't need to display these.
    var skipids = new Set(fedicommentids);
    var skippedcount = 0;

    // I use Zeno's indentation for replies.
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
        if (skipids.has(el.id)) {
            skippedcount++;
            continue;
        }
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
        ls.sort((el1, el2) => {
            if (el1.created_at < el2.created_at)
                return -1;
            if (el1.created_at > el2.created_at)
                return 1;
            return 0;
        })
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
        if (!skippedcount) {
            nod.textContent = '(No comments in this thread.)';
        }
        else {
            nod.textContent = '(No recent comments in this thread.)';
        }
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
        span = document.createElement('span');
        span.textContent = ' ';
        nod.appendChild(span);
        if (el.url) {
            span = document.createElement('a');
            span.setAttribute('rel', 'nofollow noopener noreferrer');
            span.setAttribute('href', el.url);
        }
        else {
            span = document.createElement('span');
        }
        span.textContent = '('+el._longpublished+')';
        nod.appendChild(span);
        comnod.appendChild(nod);

        comnod.appendChild(el._body);

        if (el.media_attachments && el.media_attachments.length) {
            var nod = document.createElement('div');
            for (var atel of el.media_attachments) {
                var imgnod = document.createElement('img');
                if (!atel.preview_url || !atel.url) {
                    continue;
                }
                imgnod.setAttribute('src', atel.preview_url);
                if (atel.description) {
                    imgnod.setAttribute('alt', atel.description);
                }
                var aspect = atel.meta.original.aspect;
                if (aspect) {
                    if (aspect > 1.0) {
                        imgnod.setAttribute('width', ''+image_thumbsize);
                        imgnod.setAttribute('height', ''+Math.floor(image_thumbsize/aspect));
                    }
                    else {
                        imgnod.setAttribute('width', ''+Math.floor(image_thumbsize*aspect));
                        imgnod.setAttribute('height', ''+image_thumbsize);
                    }
                }
                var anod = document.createElement('a');
                anod.setAttribute('rel', 'nofollow noopener noreferrer');
                anod.setAttribute('target', '_blank');
                anod.setAttribute('href', atel.url);
                anod.appendChild(imgnod);
                nod.appendChild(anod);
            }
            comnod.appendChild(nod);
        }

        parnod.appendChild(comnod);
        index++;
    }
}

// Display an error or other warning.
function display_comment_status(msg)
{
    document.getElementById('livecommentload').textContent = msg;
}

// Show the "Here's how to reply" pane.
function handle_comments_showreply(ev)
{
    ev.stopPropagation();
    ev.preventDefault();
    
    var nod = document.getElementById('livereply');
    nod.classList.remove('Hidden');
}

// Copy the Mastodon URL and highlight it in the pane.
function handle_comments_copyurl(ev)
{
    ev.stopPropagation();
    ev.preventDefault();
    
    var val = 'https://'+fediserver+'/@'+fediuser+'/'+fedipostid;
    navigator.clipboard.writeText(val);
    document.getElementById('replycommenturl').select();
}

