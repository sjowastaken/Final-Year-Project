/* PhantomJS Facebook crawler */

var fbgraph = 'https://graph.facebook.com/';
var access_token = '1391011097865724|9yZSQMjmMpFa22BlY1JIndukLaA';

/* Customizable variables */
var posts_limit = '10';
var comments_limit = '5000';
var loops = 100000000;
/* Set to 0 to deactivate logs */
var verbose = 1

/* Initialize filesystem for comment and HTML writing. */
var fs = require('fs');
var commentsPath = "../data/all_comments.txt";
if(fs.exists(commentsPath)){
    fs.remove(commentsPath);
}

var htmlPath = "../data/all_html.txt";
if(fs.exists(htmlPath)){
    fs.remove(htmlPath);
}

var i = 0;
var j = 0;
var n = -1;
var urlRegex = /(https?:\/\/[^\s]+)/g;

/* Contains name of pages to be searched next_page. */
var next_page = [];
var post_ids = [];
var comments_to_search = [];
var comments_to_check = [];
var links = [];

var nextindex = 0;
var postsindex = 0;
var page_id_index = 0;

/* All seed pages used, taken from: http://fanpagelist.com/category/top_users/

 f4ep, facebook, shakira, Cristiano, eminem, VinDiesel, cocacola, michaeljackson,
 TheSimpsons, rihanna, JustinBieber, LeoMessi, BobMarley, harrypottermovie, WillSmith, TaylorSwift, 
 beyonce, TexasHoldEm, linkinPark, jackie, manchesterunited, ladygaga, MrBean, adele, pitbull, 
 brunomars, Selena, McDonaldsUS, TitanicMovie, DavidGuetta, spongebob, avrillavigne, AKON, neymarjr,
 FamilyGuy, LilWayne, MeganFox, AvatarMovie.UK, Beckham, JasonStatham, Enrique, usher.
*/

/* Initialize seed pages */
next_page[0] = 'f4ep';
next_page[1] = 'facebook';
next_page[2] = 'shakira';

crawl();

function crawl() {
    n++;
    if(verbose == 1) console.log('n = ' + n);
    if(n <= loops & n < next_page.length){
        getPosts(function(){
            if(verbose == 1) console.log('posts ids found: ' + post_ids);
            commentsHandler() 
            if(verbose == 1) console.log('comments to check: ' + comments_to_check);
        });
    }
    else {
        if(verbose == 1) console.log('THE END.');
        phantom.exit(0);
    }
}

/* Gets post IDs from a Facebook page */
function getPosts(callback) {
    var page = require('webpage').create();
    if(verbose == 1) console.log('enter crawl');
    var url = fbgraph + next_page[n].toString() + '/posts?access_token=' + access_token + '&limit=' + posts_limit;

    /* Wait 30 seconds before deciding that the page is unreachable and move on */
    page.settings.resourceTimeout = 30000;

    page.onResourceTimeout = function(e) {
        if(verbose == 1) console.log('\n\nPAGE DIDN\'T OPEN\n\n');
        if(verbose == 1) console.log(e.errorCode);
        if(verbose == 1) console.log(e.errorString);
        if(verbose == 1) console.log(e.url);
        page.release();
        htmlHandler();
    }

    if(verbose == 1) console.log('opening url: ' + url);
    
    page.open(url);
    page.onLoadFinished = function(status) {
        if (status === 'success') {
            var data = JSON.parse(page.plainText);               

            if(data.error) {
                if(verbose == 1) console.log('----- page had error, skipping it -----');
                if(verbose == 1) console.log(page.plainText);
                if(verbose == 1) console.log('---------------------------------------');

                crawl();
                return;
            }
            if(!data.data) {
                if(verbose == 1) console.log('no posts found in page');
                if(verbose == 1) console.log(page.plainText);
                page.close();
                crawl();
                return;
            }
            if(verbose == 1) console.log('data length = ' + data.data.length);
            for(i = 0; i < data.data.length; i++){
                if(verbose == 1) console.log('pushing data: ' + data.data[i].id);
                post_ids.push(data.data[i].id);
                postsindex++;
            }
        }   
        else {
            if(verbose == 1) console.log('error crawling page ' );
            if(verbose == 1) console.log(
                "Error opening url \"" + page.reason_url
                + "\": " + page.reason
                );
        } 
        page.release();

        if(verbose == 1) console.log('closing crawl page');
        page.close();

        callback();
    };

    page.onResourceError = function(resourceError) {
        page.reason = resourceError.errorString;
        page.reason_url = resourceError.url;
    };

}

function commentsHandler(){
    if(verbose == 1) console.log("STARTING COMMENTS HANDLER");
    if(post_ids.length > 0) {
        getComments(commentsHandler);
    }
    else{
        if(post_ids.length == 0){
            if(verbose == 1) console.log('number of comments to check: ' + comments_to_check.length);
            if(verbose == 1) console.log('READY FOR HTML SEARCH');
            htmlHandler();
        }
    }
}

/* Get comments from Facebook posts using post ID and save them to file. If a
   comment contains a URL, save it in a queue for it to be searched on Google later */
 function getComments(callback) {
    if(verbose == 1) console.log('entering getComments');

    var page = require('webpage').create();
    comment_url = fbgraph + post_ids.shift() + '/comments?limit=' + comments_limit;
    jsonComments = '';
    if(verbose == 1) console.log('opening comments url: ' + comment_url);

    page.settings.userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:35.0) Gecko/20100101 Firefox/35.0';

    page.open(comment_url);
    page.onLoadFinished = function(status) {
        if (status === 'success') {
            if(verbose == 1) console.log('saving comments...');
            text = page.plainText;
            fs.write(commentsPath, text, 'a');
            jsonComments = JSON.parse(text);
            if(verbose == 1) console.log('length = ' + jsonComments.data.length);

            if(jsonComments.data.length == 0) {
                if(verbose == 1) console.log('no comments found in post');
                page.close();
                commentsHandler();
                return;
            }
            for(k = 0; k < jsonComments.data.length; k++) {
                /* If message contains a url, search the whole message on google to see if
                   it's been posted in other pages */
                message = jsonComments.data[k].message;
                if(message.indexOf("http") > -1){ 
                    comments_to_check.push(message);
                }
            }
        }
        else {
            if(verbose == 1) console.log('error in getComments page ' );
            if(verbose == 1) console.log(
                "Error opening url \"" + page.reason_url
                + "\": " + page.reason
                );
        } 
        page.release();
        if(verbose == 1) console.log('closing getComments page');
        page.close();
        callback.apply();
        
    }; 
}


function htmlHandler() {
    if(verbose == 1) console.log('STARTING HTML HANDLER'); 
    if(verbose == 1) console.log('comments_to_check length is ' + comments_to_check.length);
    if(comments_to_check.length > 0) {
        iframeCheck();
    }
    else {
        if(comments_to_check.length == 0){
            searchHandler();
        }
    }
}

/* Check if a given webpage contains inline iframes */
function iframeCheck() {
    if(verbose == 1) console.log('STARTING IFRAMECHECK');
    comment = comments_to_check.shift();
    if(verbose == 1) console.log('\nchecking comment: ' + comment);

    var page = require('webpage').create();
    page.settings.resourceTimeout = 30000;

    page.onResourceTimeout = function(e) {
        if(verbose == 1) console.log('\n\nPAGE DIDN\'T OPEN\n\n');
        if(verbose == 1) console.log(e.errorCode);
        if(verbose == 1) console.log(e.errorString);
        if(verbose == 1) console.log(e.url);
        page.release();
        htmlHandler();
    }
    
    page.onResourceError = function(resourceError) {
        page.reason = resourceError.errorString;
        page.reason_url = resourceError.url;
    };

    var url = comment.match(urlRegex);
    if(url != null) {
        url = url.toString();

        if(url.match(/www\.facebook/) === null & url.match(/www\.youtube/) === null & url.match(/m\.facebook/) === null & url.match(/m\.youtube/) === null & url.match(/play\.google/) === null & url.match(/youtu\.be/) === null) { //& url.indexOf('http') > 1) {
            if(verbose == 1) console.log('this link passed the test: ' + url);
            if(verbose == 1) console.log('opening url: ' + url);

            page.settings.userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:35.0) Gecko/20100101 Firefox/35.0';
            
            page.open(url, function(status) {
                if(verbose == 1) console.log('iframecheck page loaded');
                if (status === 'success') {
                    var html = page.content;
                    if(html != null){
                        if(html.indexOf("<iframe") > -1) {
                            if(verbose == 1) console.log('writing html for page ' + url + '...');
                            fs.write(htmlPath, '\n\n\n-------- HTML from page: ' + url + '.\n\ncomment is: ' + comment + '\n\n' + html, 'a');
                            if(verbose == 1) console.log('done writing html');
                            comments_to_search.push(comment);
                            if(verbose == 1) console.log('pushed comment: ' + comment);
                        }
                    }
                }   
                else {
                    if(verbose == 1) console.log('error in iframecheck page ' );
                    if(verbose == 1) console.log(
                        "Error opening url \"" + page.reason_url
                        + "\": " + page.reason
                        );
                } 
                page.release();
                if(verbose == 1) console.log('closing iframecheck page');
                page.close();
                htmlHandler();
            });
        }
        else {
            if(verbose == 1) console.log('url didn\'t pass the test');
            page.release();
            htmlHandler();
        }
    }
    else {
        if(verbose == 1) console.log('url null');
        page.release();
        htmlHandler();
    }

}


function searchHandler() {
    if(verbose == 1) console.log('STARTING SEARCH HANDLER');
    if(verbose == 1) console.log('comments to search length: ' + comments_to_search.length);
    if(comments_to_search.length > 0) {
        googleSearch();
    }
    else {
        if(comments_to_search.length == 0){
            if(verbose == 1) console.log('next page: ' + next_page);
            if(verbose == 1) console.log('CRAWL AGAIN');
            crawl();
        }
    }
}

/* Search suspicious comments on Google and save other Facebook pages that contain it */
function googleSearch() {
    if(verbose == 1) console.log('entering googleSearch');
    comment = comments_to_search.shift();

    var url = 'http://www.google.com/search?q=' + comment + '+facebook';

    if(verbose == 1) console.log('google search for comment: ' + comment);

    var temp = '';
    var page = require('webpage').create();

    page.settings.userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:35.0) Gecko/20100101 Firefox/35.0';

    page.open(url, function(status) {
        if (status === 'success') {
            var links = page.plainText.match(/https:\/\/www.facebook.com\/(.*?)\n/g);
            if(links != null){
                for(i = 0; i < links.length; i++) {
                    temp = links[i].split("/")[3];

                    /* Remove duplicates and any entry that contains a dot.*/
                    if(temp.indexOf("pages") == -1 && temp.indexOf(".") == -1 && next_page.indexOf(temp) == -1) {
                        next_page.push(temp.replace(/(\r\n|\n|\r)/gm,''));
                        nextindex++;

                    }        
                }
            }
        }   
        else {
            if(verbose == 1) console.log('error in googleSearch page ' );
            if(verbose == 1) console.log(
                "Error opening url \"" + page.reason_url
                + "\": " + page.reason
                );
        } 
        page.release();
        if(verbose == 1) console.log('closing googleSearch page');

        page.close();
        searchHandler();

    });
}

