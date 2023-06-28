'use strict';

//### https://mastodon.gamedev.place/@zarfeblong/110605586119723795

// Liberally based on:
// https://carlschwan.eu/2020/12/29/adding-comments-to-your-static-blog-with-mastodon/

// Uses DOMPurify:
// https://github.com/cure53/DOMPurify

var server = 'mastodon.gamedev.place';

function handle_comments_button(ev, fedipostid)
{
    ev.stopPropagation();
    ev.preventDefault();

    console.log('### loading postid', fedipostid);
    document.getElementById("livecommentload").textContent = "Loading...";

    var url = 'https://'+server+'/api/v1/statuses/'+fedipostid+'/context';
    
    fetch(url).then(function(response) {
        return response.json();
    }).then(obj => handle_response(obj, fedipostid), handle_failure);
}

function display_comment_status(msg)
{
    console.log(msg); //###
    document.getElementById("livecommentload").textContent = msg;
}

function handle_failure(data)
{
    display_comment_status('Unable to load: ' + data.message);
}

function handle_response(obj, fedipostid)
{
    if (obj['error']) {
        display_comment_status('Unable to load: ' + obj['error']);
        return;
    }

    console.log('### success with postid', fedipostid, 'count', obj['descendants'].length);

    var idmap = new Map();
    idmap.set(fedipostid, { _replies: [] });
              
    for (var el of obj['descendants']) {
        idmap.set(el.id, el);
    }

    var setattr = function(nod, attr, val) {
        var anod = document.createAttribute(attr);
        anod.value = val;
        nod.setAttributeNode(anod);
    }

    var depthstep = function(val) {
        if (!val)
            return '0';
        var res = 2.54 * Math.atan(val);
        res = ''+res;
        return res.substring(0,5);
    }

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

        el._body = DOMPurify.sanitize(el.content, {RETURN_DOM_FRAGMENT: true});
    }

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

    var parnod = document.getElementById('livecommentblock');

    var index = 0;
    
    for (var el of flatls) {
        var comnod = document.createElement('div');
        comnod.id = 'comment-live-' + index;
        comnod.className = 'Comment';
        setattr(comnod, 'role', 'comment');
        var depth = depthstep(el._depth);
        setattr(comnod, 'style', 'margin-left: '+depth+'em;');
        
        var nod = document.createElement('hr');
        comnod.insertBefore(nod, null);

        nod = document.createElement('div');
        nod.className = 'CommentHead';
        var span = document.createElement('span');
        span.className = 'CommentAuthor';
        span.textContent = el._authorname;
        nod.insertBefore(span, null);
        var span = document.createElement('span');
        span.textContent = ' ('+el._longpublished+')';
        nod.insertBefore(span, null);
        comnod.insertBefore(nod, null);

        comnod.appendChild(el._body);

        parnod.insertBefore(comnod, null);
        index++;
    }
}
