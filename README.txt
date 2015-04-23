This document explains how to run the code and the format of the output.

1. Collect HTML data: crawler.js

Settings are in the top part of the code, lines 7 to 11:

var posts_limit    = '10';
var comments_limit = '5000';
var loops          = 100000000;
var verbose        = 1

Change according to need.

The command to execute the crawler with a log as output (after setting verbose == 1):
phantomjs crawler.js > ../out/crawler_log.txt

Else (not recommended)
phantomjs crawler.js

PhantomJS will deliver errors to the stderr while processing the data. This is normal and should just be ignored.

The crawler will automatically create two files: 
- all_comments.txt, which contains all comments encountered by the crawler saved in JSON format.
- all_html.txt, which contains the HTML of all suspicious pages for which a link was found in a comment.

In all_html.txt, each page entry starts as follows:

-------- HTML from page: http://sh.st/hdfRZ.

comment is: All deceived Facebook 2015  http://sh.st/hdfRZ

<!DOCTYPE html><html><head><script type="text/javascript">
function customwl_onload_fb62bbf2e9() {
   if (typeof(jQuery) === "undefined") {
   ...
   ...
   ...

This format is then used in the feature generation script to separate each entry from the other. 


-----------------------------------------------------------------------------------------------------------------


2. Generate feature matrix: featuregen.py

Set the verbose parameter to 0 if desired. If left as 1, it will output the data index number and the feature vector for each entry in both dictionary and list form, along with the filter prediction. An example is given below:


1    OrderedDict([('nsuspscript', 0), ('nvideos', 0), ('niframes', 2), ('nscripts', 1), ('ncommsuspterm', 0), ('commthastxt', 26), ('ninvisible', 0), ('nhw1', 0), ('nhw100', 1), ('nsmallarea', 0), ('nposabs', 0), ('nsrcnotdom', 1), ('nhas_fb', 0), ('nowww', 1), ('lengthurl', 18), ('subdomlen', 2), ('urlhasip', 0), ('url_adv_short', 1), ('url_short', 0), ('subdomhasnum', 0), ('noccurr', 1), ('filterpred', 2)])
url:   http://sh.st/hdfRZ
1    [0, 0, 2, 1, 0, 26, 0, 0, 1, 0, 0, 1, 0, 1, 18, 2, 0, 1, 0, 0, 1, 2]
filter pred:  2

The python library cssutils used to parse inline CSS usually produces many errors. Ignore them, as they do not affect the results in any way.

Chose a name for the output in line 18:
outn = 'output'

Enter the file name for the HTML file produced by the crawler in line 21:
dn = 'all_html'

To execute the file in verbose mode, enter:
python featuregen.py > ../out/featuregen_log.txt

Else just run:
python featuregen.py


-----------------------------------------------------------------------------------------------------------------


3. Run the classifier on the data: learn.py


Again the verbose setting allows to turn on or off console output. If left on, it will output the analysis results for the training set and the feature importance list. The output is a list of entries:


[1, '  pred:', '3', ' prob:', array([ 0. ,  0.2,  0.8])]
[2, '  pred:', '3', ' prob:', array([ 0.,  0.,  1.])]
[3, '  pred:', '3', ' prob:', array([ 0.  ,  0.04,  0.96])]
...

In order: data index, classifier prediction (3 benign, 2 malicious, 1 clickjacking) and the probability assigned to each class by the model.

To run the code in verbose mode:
python learn.py > ../out/learn_log.txt

Else:
python learn.py

