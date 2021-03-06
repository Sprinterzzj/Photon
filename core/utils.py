import math
import re
import argparse

import tld

from core.colors import info
from core.config import VERBOSE, BAD_TYPES

from urllib.parse import urlparse
from urllib.request import ProxyHandler, build_opener, install_opener, Request, urlopen
import urllib.error



def regxy(pattern, response, supress_regex, custom):
    """Extract a string based on regex pattern supplied by user."""
    try:
        matches = re.findall(r'%s' % pattern, response)
        for match in matches:
            verb('Custom regex', match)
            custom.add(match)
    except:
        supress_regex = True


def is_link(url, processed, files):
    """
    Determine whether or not a link should be crawled
    A url should not be crawled if it
        - Is a file
        - Has already been crawled

    Args:
        url: str Url to be processed
        processed: list[str] List of urls that have already been crawled

    Returns:
        bool If `url` should be crawled
    """
    if url not in processed:
        is_file = url.endswith(BAD_TYPES)
        if is_file:
            files.add(url)
            return False
        return True
    return False


def remove_regex(urls, regex):
    """
    Parse a list for non-matches to a regex.

    Args:
        urls: iterable of urls
        regex: string regex to be parsed for

    Returns:
        list of strings not matching regex
    """

    if not regex:
        return urls

    # To avoid iterating over the characters of a string
    if not isinstance(urls, (list, set, tuple)):
        urls = [urls]

    try:
        non_matching_urls = [url for url in urls if not re.search(regex, url)]
    except TypeError:
        return []

    return non_matching_urls


def writer(datasets, dataset_names, output_dir):
    """Write the results."""
    for dataset, dataset_name in zip(datasets, dataset_names):
        if dataset:
            filepath = output_dir + '/' + dataset_name + '.txt'
            with open(filepath, 'w+') as out_file:
                joined = '\n'.join(dataset)
                out_file.write(str(joined.encode('utf-8').decode('utf-8')))
                out_file.write('\n')


def timer(diff, processed):
    """Return the passed time."""
    # Changes seconds into minutes and seconds
    minutes, seconds = divmod(diff, 60)
    try:
        # Finds average time taken by requests
        time_per_request = diff / float(len(processed))
    except ZeroDivisionError:
        time_per_request = 0
    return minutes, seconds, time_per_request


def entropy(string):
    """Calculate the entropy of a string."""
    entropy = 0
    for number in range(256):
        result = float(string.encode('utf-8').count(
            chr(number))) / len(string.encode('utf-8'))
        if result != 0:
            entropy = entropy - result * math.log(result, 2)
    return entropy


def xml_parser(response):
    """Extract links from .xml files."""
    # Regex for extracting URLs
    return re.findall(r'<loc>(.*?)</loc>', response)


def verb(kind, string):
    """Enable verbose output."""
    if VERBOSE:
        print('%s %s: %s' % (info, kind, string))


def extract_headers(headers):
    """This function extracts valid headers from interactive input."""
    sorted_headers = {}
    matches = re.findall(r'(.*):\s(.*)', headers)
    for match in matches:
        header = match[0]
        value = match[1]
        try:
            if value[-1] == ',':
                value = value[:-1]
            sorted_headers[header] = value
        except IndexError:
            pass
    return sorted_headers


def top_level(url, fix_protocol=True):
    """Extract the top level domain from an URL."""
    ext = tld.get_tld(url, fix_protocol=fix_protocol)
    toplevel = '.'.join(urlparse(url).netloc.split('.')[-2:]).split(
        ext)[0] + ext
    return toplevel


def ProxyType(v):
    """ Match IP:PORT or DOMAIN:PORT in a losse manner """
    if re.match(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})", v):
        return v
    elif re.match(r"[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}", v.split(':')[0]):
        return v
    else:
        raise argparse.ArgumentTypeError(
            "Proxy should follow IP:PORT or DOMAIN:PORT format")


def luhn(purported):

    # sum_of_digits (index * 2)
    LUHN_ODD_LOOKUP = (0, 2, 4, 6, 8, 1, 3, 5, 7, 9)

    if not isinstance(purported, str):
        purported = str(purported)
    try:
        evens = sum(int(p) for p in purported[-1::-2])
        odds = sum(LUHN_ODD_LOOKUP[int(p)] for p in purported[-2::-2])
        return (evens + odds) % 10 == 0
    except ValueError:  # Raised if an int conversion fails
        return False


def is_good_proxy(pip):
    try:
        proxy_handler = ProxyHandler(pip)
        opener = build_opener(proxy_handler)
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        install_opener(opener)
        # change the URL to test here
        req = Request('http://www.example.com')
        sock = urlopen(req, timeout=3)
    except urllib.error.HTTPError as e:
        return False
    except Exception as detail:
        return False
    return True
