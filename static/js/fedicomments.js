'use strict';

//### https://mastodon.gamedev.place/@zarfeblong/110605586119723795

// https://carlschwan.eu/2020/12/29/adding-comments-to-your-static-blog-with-mastodon/

var server = 'mastodon.gamedev.place';

function handle_comments_button(ev, fedipostid)
{
    ev.stopPropagation();
    ev.preventDefault();

    console.log('### loading postid', fedipostid);
    document.getElementById("loadcommentbutton").textContent = "Loading...";

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

    for (var el of flatls) {
    }
}
