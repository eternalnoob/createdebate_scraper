import lxml
from lxml import html, etree
import re
import json
from IPython import embed
from copy import deepcopy


class Debate(object):
    def __init__(self, URL="", topic="", author=""):
        create_debate = html.parse(URL).getroot()
        # topic needs to be passed in because it isn't in HTML
        try:
            left = create_debate.xpath("//div[contains(@class, 'sideL')]")[0]
            right = create_debate.xpath("//div[contains(@class, 'sideR')]")[0]
        except IndexError:
            left = None
            right = None


        self.title = create_debate.find_class('debateTitle')[0].text_content().strip()
        try:
            self.description = create_debate.find_class('debatelongDesc')[0].text_content().strip()
        except IndexError:
            self.description = ""
        self.topic = topic
        self.url = URL
        self.author = author
        debatebox = create_debate.find_class('fadeBox4')[0]

        sides = debatebox.xpath("//div[contains(@class, 'sideTitle')]")

        self.side1 = Side(sides[0], left)
        self.side2 = Side(sides[1], right)

    def to_json(self):
        conversion_dict = {}
        conversion_dict['debate_title'] = self.title
        conversion_dict['debate_description'] = self.description
        conversion_dict['side1'] = self.side1.to_dict()
        conversion_dict['side2'] = self.side2.to_dict()
        conversion_dict['topic'] = self.topic
        conversion_dict['url'] = self.url
        conversion_dict['author'] = self.author
        return json.dumps(conversion_dict)

class Side(object):

    def __init__(self, sideHTML, argumentsHTML):
        self.arguments = []
        self.title = sideHTML.xpath("h2")[0].text_content()
        self.points = int(re.findall(r'\d+', sideHTML.text_content())[0])
        if argumentsHTML is not None and "No arguments found. Add One!" not in argumentsHTML.text_content():
            self.arguments = getChildren(argumentsHTML)
        else:
            self.arguments = []

    def to_dict(self):
        conversion_dict = {}
        conversion_dict['side_title'] = self.title
        conversion_dict['points'] = self.points
        conversion_dict['arguments'] = [x.to_dict() for x in self.arguments]
        return conversion_dict

    def get_conversations(self, commenter1, commenter2, min_length=None, max_length=None):
        """ commenter1 and commenter2 should both be strings corresponding to
        the usernames this will try and find all conversations which involve
        those two usernames conversing back and forth """

        #find something in arguments starting with commenter1 or commenter2
        candidates = []
        for i in self.arguments:
            if i.author == commenter1 or i.author == commenter2:
                candidates.append(i)
        accumulator = []

        for i in candidates:
            i.get_conversations(commenter1, commenter2, min_length, max_length, [], accumulator)
        return accumulator


def getComment(commentHTML, parent):
    points = int(commentHTML.find_class("argPoints")[0].xpath("span")[0].text_content().strip())
    user = commentHTML.find_class("updownTD")[0].xpath("a")[1].text_content()
    body = commentHTML.find_class("argBody")[0].text_content()
    disputed = len(commentHTML.find_class("updownTD")[0].xpath("span")) > 0 #there are 1 or 0 span, and span will
    # only say disputed
    return Argument(author=user, points=points, text=body, parent=parent, disputed=disputed)


def getChildren(argumentsHTML, parent=None):
    children = []
    for element in argumentsHTML.iterchildren():
        if "argBox" in element.classes:
            children.append(getComment(element,parent))
            # this is the start of a new argument
        elif "arg-threaded" in element.classes:
            # this corresponds to the children of the current comment
            if len(children) > 0:
                children[len(children)-1].children = getChildren(element, children[len(children)-1]) #get back element
    return children




class Argument(object):

    def __init__(self, author="", points=0, text="", parent=None, disputed=False):
        self.author = author
        self.points = points
        self.text = text
        self.children = []
        self.parent = parent
        self.disputed = disputed

    def to_dict(self):
        conversion_dict = {}
        conversion_dict['author'] = self.author
        conversion_dict['points'] = self.points
        conversion_dict['text'] = self.text
        conversion_dict['disputed'] = self.disputed
        conversion_dict['children'] = [x.to_dict() for x in self.children]
        return conversion_dict

    def get_conversations(self, commenter1, commenter2, min_length, max_length, path, global_accum): 
        pathlen = len(path)
        path.append(self)
        candidates = [i for i in self.children if (i.author == commenter1 or i.author == commenter2) and i.author != self.author]
        if not candidates:
            global_accum.append(deepcopy(path))
        else:
            for i in candidates: i.get_conversations(commenter1, commenter2, min_length, max_length, path, global_accum)
        path.pop(pathlen)
        
    def __repr__(self):
        return 'Author: {author}\tPoints: {points}\tText: \"{text}\"'.format(author=self.author, points=self.points, text=self.text)


def most_recent_12_debates(topic):
    topic_feed_xml = etree.parse('http://www.createdebate.com/browse/debaterss/mostrecent/all/twosided/alltime/{topic}'.format(topic=topic)+
                                 '/0/12/open/all/xml')
    # the topic field actually doesn't matter because the createdebate API for
    # some reason doesn't actually break them up by topic even if you want to
    # it also always breaks if you request more than 12 at a time, so it
    # appears to be a generally shoddy endpoint
    debates = topic_feed_xml.xpath('//debate')
    parsedDebates = []
    for debate in debates:
        #author = debate.xpath('title')[1].content
        author = ""
        topic = debate.xpath('topic')[0].text
        url = debate.xpath('guid')[0].text
        debate_etree = html.parse(url).getroot()
        if "This debate is private. You do not have access." in debate_etree.text_content():
            print("Private Debate!")
        else:
            parsedDebates.append(Debate(URL=url, topic=topic, author=author))
    return parsedDebates

#Right now this only works with two sided debates
x = most_recent_12_debates('science')
debate = x[0]
