import re
import os
import sys
from bs4 import BeautifulSoup
import urllib.request 
from urllib.parse import urlsplit
import time
import numpy as np
import cssutils
import collections

start = time.time()

#Set to 0 to deactivate logs 
verbose = 1

# Saved file name
outn = 'example_output'

# Data file name
dn = 'example_all_html'

def init_fv():

	'''
	Feature key, number, description.


	General:
	nsuspscript	    # 1.  Number of times suspicious words appear in page script.
	nvideos 	    # 2.  Number of videos in page.
	niframes	    # 3.  Number of iframes in page.
	nscripts		# 4.  Number of scripts in page.

	Comments:
	ncommsuspterm   # 5.  Number of suspicious terms the comment contains.
	commthastxt	    # 6.  Length of comment text without url. 

	Iframes:
	ninvisible      # 7.  Number if iframes hidden with visibility:hidden, z-index < 0, opacity < 0.2.
	nhw1            # 8.  Number of times height and width are 1 in iframe.
	nhw100  		# 9.  Number of times heigth and width are 100% in an iframe. 
	nsmallarea		# 10. Number of times area is < 200.
	nposabs		    # 11. Number of iframes with position absolute.
	nsrcnodom 	    # 12. Number of times iframe src doesn't belong to page domain.
	nhas_fb		    # 13. Number if iframes that contains a Facebook plugin.
	

	URL:
	nowww		    # 14. URL does not contain prefix www.
	lengthurl	    # 15. Length of URL.
	subdomainlen    # 16. Length of subdomain.
	hasipaddr	    # 17. Has IP address in URL.
	urladshort      # 18. Check if URL is ad-based short
	urlshort 	    # 19. URL shortened with no advertisements
	subdomhasnum	# 20. Subdomain contains numbers.
	noccurr			# 21. Number of times comment appears in the dataset.

	'''

	fv = collections.OrderedDict()

	fv['nsuspscript'] = 0
	fv['nvideos'] = 0
	fv['niframes'] = 0
	fv['nscripts'] = 0

	fv['ncommsuspterm'] = 0
	fv['commthastxt'] = 0

	fv['ninvisible'] = 0
	fv['nhw1'] = 0
	fv['nhw100'] = 0
	fv['nsmallarea'] = 0
	fv['nposabs'] = 0
	fv['nsrcnotdom'] = 0
	fv['nhas_fb'] = 0

	fv['nowww'] = 0
	fv['lengthurl'] = 0
	fv['subdomlen'] = 0
	fv['urlhasip'] = 0
	fv['url_adv_short'] = 0
	fv['url_short'] = 0
	fv['subdomhasnum'] = 0

	fv['noccurr'] = 0
	
	fv['filterpred'] = 0

	return fv

def is_url_shortened(url):
	# Check if url was shortened
	shorteners = ['goo.gl', 'tinyurl.com', 'tiny.cc']
	if any(x in url for x in shorteners):
		return 1 
	else: return 0

def is_url_adv_shortened(url):
	# Check if url was shortened in ad-based way
	shorteners = ['bit.ly', 'ow.ly', 'adf.ly', 'sh.st', 'fur.ly', 'cutt.us', 'cur.lv', 'past.is', \
	'po.st', 'adyou.me', 'jota.pm', 'j.gs', 'q.gs']
	if any(x in url for x in shorteners):
		return 1 
	else: return 0

def has_keywords(comment):
	# Find terms that more often correlate with malicious intentions
	keywords = ['kilos', 'kg', 'weight', 'porn', 'sex', 'sexo', 'hot', 'dirty', 'naked', 'naughty', \
	'money', 'click', 'video', 'movie', '$ex', 'earn']
	if any(x in comment.lower() for x in keywords):
		return 1 
	else: return 0

def has_susp_script(scripts):
	# Find terms that more often correlate with malicious activity
	count = 0
	for s in scripts:
		suspterms = ['window', 'iframe', 'mouse', 'click', 'track', 'eval']
		for susp in suspterms:
			if susp in s.lower():
				count += 1

	return count

def has_text(comment, comment_url):
	# Determine whether comment contains text along with url
	comment_text = comment.replace(comment_url, "").strip()
	return len(comment_text)

def inline_transp_check(ifr):
	# Check for transparency
	is_invisible = 0
	if 'visibility' in ifr.attrs:
		if ifr['visibility'] != 'visible':
			is_invisible = 1
	if 'opacity' in ifr.attrs:
		if ifr['opacity'] == '0':
			is_invisible = 1
	if 'z-index' in ifr.attrs:
		if int(ifr['z-index']) < 0:
			is_invisible = 1

	return is_invisible

def analyze_iframes(iframes, page_url, fv):
	for ifr in iframes:
		w = ''
		h = ''
		is_invisible = inline_transp_check(ifr)

		if 'style' in ifr.attrs:
			css = ifr['style']
			s = cssutils.parseStyle(css)
			w = s.width
			h = s.height
			if 'absolute' in s.position:
				cssposabs = 1
			if s.visibility == 'hidden': 
				is_invisible = 1
			if s.opacity == '0':
				is_invisible = 1

		fv['ninvisible'] += is_invisible

		if 'width' in ifr.attrs:
			w = ifr['width'].strip(' ')
		if 'height' in ifr.attrs:
			h = ifr['height'].strip(' ')

		w = re.findall(r'\d+', w)
		h = re.findall(r'\d+', h)

		if len(w) > 0 and len(h) > 0:
			w = int(w[0])
			h = int(h[0])
			area = -1
			if(w == 0 and h == 0) or (w != 0 and h != 0):
				area = w * h
				if area < 250:
					fv['nsmallarea'] += 1 
				elif area == 1:
					fv['nhw1'] += 1
				elif area == 10000:
					fv['nhw100'] += 1

		if 'src' in ifr.attrs:
			src = ifr['src']
			if "facebook" in src:
				fv['nhas_fb'] += 1 

			# Benign domains
			benigndom = ['accounts.google.com', 'youtube.com', 'ulogin', 'blogger.com', 'wix', 'addtoany.com']
			if not any(x in src for x in benigndom):
				# Same domain check
				base_src = urlsplit(src).netloc
				base_url = urlsplit(page_url).netloc
				if base_src != base_url:
					if 'id' in ifr.attrs:
						# Don't pick up google iframes, developers try to hide them
						if 'google' not in ifr.attrs['id']:
							fv['nsrcnotdom'] += 1 
		if 'position' in ifr.attrs:
			if ('absolute' in ifr['position']) or cssposabs == 1:
				fv['nposabs'] += 1 

	return fv

def analyze_url(url, fv):
	# See if subdomain is www
	spl = (url.split('://')[1]).split('.')
	subdom = spl[0]
	fv['lengthurl'] = len(url)
	# Whitelisting twitter
	fv['subdomlen'] = len(subdom)
	if subdom != 'www' and subdom != 'twitter' and spl[1] != 'tumblr' and subdom != 'youtu':
		fv['nowww'] = 1 
	# Find if it contains ip address
	ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}', url)
	if len(ip) > 0:
		fv['urlhasip'] = 1 
	fv['url_adv_short'] = is_url_adv_shortened(url)
	fv['url_short'] = is_url_shortened(url)
	if any(char.isdigit() for char in subdom):
		fv['subdomhasnum'] = 1
	return fv

def labelgen(fv):

	'''
	1: Clickjacking: is malicious AND:
	- one iframe only and w == 100 and h == 100 and srcnotdom
	- w == 1 and h == 1 and is_invisible and script suspicious
	- noccurr > 3 and is_fb true and is_invisible true and there aren't too many iframes to skew up the result
	- urladshort is not true

	3: Benign pages 
	- no bad terms in script
	- url not shortened in any way (urladshort and urlshort == 0)
	- (is_fb == 1 and appears only once in dataset (noccur == 1)) 
	- subdomain present (subdomainlen > 2) and subdomain has no numbers
	- no bad terms in comment (nocommsuspterm == 0)
	- no ip address in URL (hasipaddr == 0)
	- is_invisible never triggered

	Else: 2, malicious

	'''

	label = 0

	if fv['nsuspscript'] <= 1 and (not (fv['noccurr'] > 2 and fv['nhas_fb'] > 0)) and fv['url_adv_short'] == 0 and fv['url_short'] == 0 and \
		fv['ncommsuspterm'] == 0 and fv['urlhasip'] == 0 and (fv['subdomlen'] > 2 and fv['subdomhasnum'] == 0) and fv['ninvisible'] == 0:
		label = 3
	else:
		label = 2
		if fv['url_adv_short'] == 0 and ((fv['nhw1'] > 0 and fv['ninvisible'] > 0 and fv['nsuspscript'] > 0) or \
			(fv['noccurr'] > 3 and fv['nhas_fb'] > 0 and fv['ninvisible'] > 1 and fv['niframes'] <= 20) or \
			(fv['nhw100'] == 1 and fv['nsrcnotdom'] > 0)):
			label = 1

	return label

def process_pages(pages):
	log = {}

	htmls = []
	page_urls = []
	comments = []
	log_entries = []

	for i in range(0, len(pages)):
		# Early termination 
		#if i > 100: break
		if i % 100 == 0: print("processed ", i, " pages")
		html = pages[i].split("<head>")

		if(len(html) > 1):
			nonhtml = html[0].split("comment is: ")
			page_url = nonhtml[0].split("from page: ")[1].split(" ")[0].strip()
			page_url = page_url[:len(page_url)-1]

			# Get comment
			comment = nonhtml[1].split("<!DOCTYPE")[0]
			log_entry = page_url + " " + comment.replace('\n', '') 

			if log_entry not in log:
				log[log_entry] = 1
			else: 
				log[log_entry] += 1

			htmls.append(html)
			page_urls.append(page_url)
			comments.append(comment)
			log_entries.append(log_entry)

	return htmls, page_urls, comments, log_entries, log
			

# --- SCRIPT

pages = open(''.join(("../data/", dn, ".txt"))).read()
if verbose == 1: print("opening file: ", ''.join(("../data", dn)))
pages = pages.split("-------- HTML ")

featurevectors = []
already_processed = []

# Counts non duplicate pages
count = 1

htmls, page_urls, comments, log_entries, log = process_pages(pages)

for i in range(0, len(page_urls)):

	# Feature vector
	fv = init_fv()

	html = htmls[i]
	page_url = page_urls[i]
	comment = comments[i]
	log_entry = log_entries[i]
		
	# Avoid duplicates
	if log_entry not in already_processed: 

		# Extract url from comment (all comments at this point have urls)
		comment_url = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', comment)[0]		

		html = "<head>" + html[1]
		soup = BeautifulSoup(html)
		iframes = soup.findAll('iframe')
		
		if iframes != None:
			fv['niframes'] = len(iframes)

		scripts = soup.find('script')
		
		if scripts != None:
			fv['nscripts'] = len(scripts)
			fv['nsuspscript'] = has_susp_script(scripts)

		videos = soup.find('video')
		if videos != None:
			fv['nvideos'] = len(videos)

		if len(iframes) == 1: 
			fv['niframes'] = len(iframes)

		fv['ncommsuspterm'] = has_keywords(comment)
		fv['commthastxt'] = has_text(comment, comment_url)
		fv = analyze_iframes(iframes, page_url, fv)
		fv = analyze_url(page_url, fv)

		fv['noccurr'] = log[log_entry]

		filter_pred = labelgen(fv)
		fv['filterpred'] = filter_pred

		already_processed.append(log_entry)
		v = list(fv.values())
		featurevectors.append(v)
		if verbose == 1: print(count, "  ", fv)
		if verbose == 1: print("url:  ", page_url)
		if verbose == 1: print(count, "  ", v)
		if verbose == 1: print("filter pred: ", filter_pred)
		if verbose == 1: print("")
		count += 1

with open(''.join(('../gen/data_', outn)), 'wb') as f:	
	np.savetxt(f, featurevectors, fmt='%i')

with open(''.join(('../gen/links_', outn)), 'w') as f:	
	for item in already_processed:
		f.write("%s\n" % item)

if verbose == 1: print("\ntotal entries: ", i + 1, " non duplicates: ", count - 1)
end = time.time()
if verbose == 1: print('\ntime elapsed: ', end - start)