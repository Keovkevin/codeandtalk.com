from flask import Flask, render_template, redirect, abort, request, url_for, Response, jsonify
from datetime import datetime
import os
import json
import re

catapp = Flask(__name__)
root = os.path.dirname((os.path.dirname(os.path.realpath(__file__))))

@catapp.route("/")
def main():
    cat = _read_json(root + '/html/cat.json')
    return render_template('index.html',
        h1          = 'Presentations from tech events worth watching',
        title       = 'Conferences, Videos, Podcasts, and People',
        stats       = cat['stats'],
    )

@catapp.route("/about")
def about(filename = None):
    cat = _read_json(root + '/html/cat.json')
    return render_template('about.html',
        h1          = 'About Code And Talk',
        title       = 'About Code And Talk',
        stats       = cat['stats'],
    )

@catapp.route("/conferences")
def conferences():
    cat = _read_json(root + '/html/cat.json')
    return render_template('list.html',
        h1          = 'Open Source conferences',
        title       = 'Open Source conferences',
        conferences = _future(cat),
        stats       = cat['stats'],
    )
@catapp.route("/all-conferences")
def all_conferences():
    cat = _read_json(root + '/html/cat.json')
    return render_template('list.html',
        h1          = 'All the Tech related conferences',
        title       = 'All the Tech related conferences',
        conferences = cat['events'].values(),
    )

@catapp.route("/cfp")
def cfp_conferences():
    cat = _read_json(root + '/html/cat.json')
    now = datetime.now().strftime('%Y-%m-%d')
    cfp = sorted(list(filter(lambda e: 'cfp_date' in e and e['cfp_date'] >= now, cat["events"].values())), key = lambda e: e['start_date'])
    return render_template('list.html',
        h1          = 'Call for Papers',
        title       = 'Call for Papers',
        conferences = cfp,
    )

@catapp.route("/code-of-conduct")
def code_of_conduct():
    cat = _read_json(root + '/html/cat.json')
    now = datetime.now().strftime('%Y-%m-%d')

    no_code = list(filter(lambda e: not e.get('code_of_conduct'), cat['events'].values()))
    return render_template('code-of-conduct.html',
        h1          = 'Code of Conduct',
        title       = 'Code of Conduct (or lack of it)',
        conferences = list(filter(lambda x: x['start_date'] >= now, no_code)),
        earlier_conferences = list(filter(lambda x: x['start_date'] < now, no_code)),
        stats       = cat['stats'],
    )

@catapp.route("/videos")
def videos():
    term = _term()
    videos = _read_json(root + '/html/videos.json')
    results = []
    if term != '':
        for v in videos:
            if term in v['title'].lower():
                results.append(v)
                continue
            if term in v['short_description'].lower():
                results.append(v)
                continue
            if 'tags' in v:
                tags = [x['link'] for x in v['tags']]
                if term in tags:
                    results.append(v)
                    continue

    return render_template('videos.html',
        title            = 'Tech videos worth watching', 
        h1               = 'Videos',
        number_of_videos = len(videos),
        term             = term,
        videos           = results,
    )


@catapp.route("/people")
def people():
    term = _term()
    ppl = _read_json(root + '/html/people.json')
    result = {}
    if term != '':
        for nickname in ppl.keys():
            if re.search(term, ppl[nickname]['name'].lower()):
                result[nickname] = ppl[nickname]
            elif re.search(term, ppl[nickname].get('location', '').lower()):
                result[nickname] = ppl[nickname]
            elif re.search(term, ppl[nickname].get('topics', '').lower()):
                result[nickname] = ppl[nickname]
            elif 'tags' in ppl[nickname] and term in ppl[nickname]['tags']:
                result[nickname] = ppl[nickname]

    return render_template('people.html',
        title            = 'People who talk at conferences or in podcasts', 
        h1               = 'People who talk',
        number_of_people = len(ppl.keys()),
        term             = term,
        people           = result,
        people_ids       = sorted(result.keys()),
    )

@catapp.route("/series")
def series():
    data = _read_json(root + '/html/series.json')
    return render_template('series.html',
        h1     = 'Event Series',
        title  = 'Event Series',
        series = data,
    )

### static page for the time of transition
@catapp.route("/<filename>")
def static_file(filename = None):
    #index.html  redirect

    if not filename:
        filename  = 'index.html'
    mime = 'text/html'
    content = _read(root + '/html/' + filename)
    if filename[-4:] == '.css':
        mime = 'text/css'
    elif filename[-5:] == '.json':
        mime = 'application/javascript'
    elif filename[-3:] == '.js':
        mime = 'application/javascript'
    elif filename[-4:] == '.xml':
        mime = 'text/xml'
    elif filename[-4:] == '.ico':
        mime = 'image/x-icon'
    return Response(content, mimetype=mime)

@catapp.route("/v/<event>/<video>")
def video(event = None, video = None):
    path = root + '/html/v/{}/{}'.format(event, video)
    #html_file = path + '.html'
    data = json.loads(open(path + '.json').read())

    #os.path.exists(html_file):
    #   data['description'] = open(html_file).read()
    return render_template('video.html',
        h1          = data['title'],
        title       = data['title'],
        video       = data,
        blasters    = data.get('blasters'),
    )

@catapp.route("/p/<person>")
def person(person = None):
    path = root + '/html/p/{}'.format(person)
    data = json.load(open(path + '.json'))
    return render_template('person.html',
        h1          = data['info']['name'],
        title       = 'Presentations and podcasts by ' + data['info']['name'],
        person      = data,
        id          = person,
    )

@catapp.route("/cal/all.ics")
def calendar():
    cat = _read_json(root + '/html/cat.json')

    future = _future(cat)
    cal = ""
    cal += "BEGIN:VCALENDAR\r\n"
    cal += "PRODID:https://codeandtalk.com/cal/all.ics\r\n"
    cal += "VERSION:2.0\r\n"
    #PRODID:-//http://XXX//Event
    #METHOD:PUBLISH

    for e in future:
        cal += "BEGIN:VEVENT\r\n"
        cal += "DTSTAMP:{}T000000Z\r\n".format(re.sub(r'-', '', e['start_date']))
        cal += "DTSTART;VALUE=DATE:{}\r\n".format(re.sub(r'-', '', e['start_date']))
        cal += "DTEND;VALUE=DATE:{}\r\n".format(re.sub(r'-', '', e['end_date']))
        uid = re.sub(r'\W+', '-', e['url'])
        uid = re.sub(r'\W+$', '', uid)
        cal += "UID:{}\r\n".format(uid)
        cal += "SUMMARY:{}\r\n".format(e['name'])
        cal += "DESCRIPTION:{}\r\n".format(e['url'])
        try:
            location = e['city']
            if e['state']:
                location += ", " + e['state']
            location += ", " + e['country']
            cal += "LOCATION:{}\r\n".format(location)
        except Exception:
            pass
            # hide Unicode error from beyondtellerrand-2017
        cal += "END:VEVENT\r\n"

    cal += "END:VCALENDAR\r\n"

    return cal
    #return cal.to_ical().decode('UTF-8')

@catapp.route("/t/<tag>")
@catapp.route("/e/<event>")
@catapp.route("/l/<location>")
@catapp.route("/s/<source>")
@catapp.route("/blaster/<blaster>")
def html(event = None, source = None, tag = None, location = None, blaster = None):
    if blaster:
        return _read(root + '/html/blaster/' + blaster)
    if location:
        return _read(root + '/html/l/' + location)
    if source:
        return _read(root + '/html/s/' + source)
    if event:
        return _read(root + '/html/e/' + event)
    if tag:
        return _read(root + '/html/t/' + tag)

###### Helper functions

def _read(filename):
    try:
        return open(filename).read()
    except Exception:
        return render_template('404.html',
            h1          = '404',
            title       = 'Four Oh Four',
        )

        
def _term():
    term = request.args.get('term', '')
    term = term.lower()
    term = re.sub(r'^\s*(.*?)\s*$', r'\1', term)
    return term

def _read_json(filename):
    catapp.logger.debug("Reading '{}'".format(filename))
    try:
        with open(filename) as fh:
            data = json.loads(fh.read())
    except Exception as e:
        catapp.logger.error("Reading '{}' {}".format(search_file, e))
        data = {}
        pass
    return data

def _future(cat):
    now = datetime.now().strftime('%Y-%m-%d')
    return sorted(list(filter(lambda e: e['start_date'] >= now, cat["events"].values())), key = lambda e: e['start_date'])


# vim: expandtab
