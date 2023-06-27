'use strict';

//### https://mastodon.gamedev.place/@zarfeblong/110605586119723795

// https://carlschwan.eu/2020/12/29/adding-comments-to-your-static-blog-with-mastodon/

var server = 'mastodon.gamedev.place';

function handle_comments_button(ev, fedipostid)
{
    ev.stopPropagation();
    ev.preventDefault();

    console.log('### loading postid', fedipostid);
    document.getElementById("loadcommentbutton").innerHTML = "Loading";

    var url = 'https://'+server+'/api/v1/statuses/'+fedipostid+'/context';
    
    fetch(url).then(function(response) {
        return response.json();
    }).then(handle_response, handle_failure);
}

function display_comment_status(msg)
{
    console.log(msg); //###
}

var tmpdata = null; //###

function handle_failure(data)
{
    console.log('### failure:', data);
    tmpdata = data; //###
    display_comment_status('Unable to load: ' + data.message);
}

function handle_response(data)
{
    console.log('### success:', data);
    tmpdata = data; //###

    if (data['error']) {
        display_comment_status('Unable to load: ' + data['error']);
        return;
    }
}
