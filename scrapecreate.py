import lxml
from lxml import html
import re
import json
from IPython import embed


class Debate(object):
    def __init__(self, URL):
        create_debate = html.parse(URL).getroot()
        left = create_debate.xpath("//div[contains(@class, 'sideL')]")[0]
        right = create_debate.xpath("//div[contains(@class, 'sideR')]")[0]
        self.title = create_debate.find_class('debateTitle')[0].text_content().strip()
        self.description = create_debate.find_class('debatelongDesc')[0].text_content().strip()
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
        return json.dumps(conversion_dict)

class Side(object):

    def __init__(self, sideHTML, argumentsHTML):
        self.arguments = []
        self.title = sideHTML.xpath("h2")[0].text_content()
        print(self.title)
        self.points = int(re.findall(r'\d+', sideHTML.text_content())[0])
        print(self.points)
        self.arguments = getChildren(argumentsHTML)
        #print(self.title)

    def to_dict(self):
        conversion_dict = {}
        conversion_dict['side_title'] = self.title
        conversion_dict['points'] = self.points
        conversion_dict['arguments'] = [x.to_dict() for x in self.arguments]
        return conversion_dict

def getComment(commentHTML):
    points = int(commentHTML.find_class("argPoints")[0].xpath("span")[0].text_content().strip())
    user = commentHTML.find_class("updownTD")[0].xpath("a")[1].text_content()
    body = commentHTML.find_class("argBody")[0].text_content()
    return Argument(author=user, points=points, text=body)


def getChildren(argumentsHTML):
    children = []
    for element in argumentsHTML.iterchildren():
        if "argBox" in element.classes:
            children.append(getComment(element))
            # this is the start of a new argument
        elif "arg-threaded" in element.classes:
            # this corresponds to the children of the current comment
            if len(children) > 0:
                children[len(children)-1].children = getChildren(element) #get back element
    return children




class Argument(object):

    def __init__(self, author="", points=0, text=""):
        self.author = author
        self.points = points
        self.text = text
        self.children = []

    def to_dict(self):
        conversion_dict = {}
        conversion_dict['author'] = self.author
        conversion_dict['points'] = self.points
        conversion_dict['text'] = self.text
        conversion_dict['children'] = [x.to_dict() for x in self.children]
        return conversion_dict


create_debate = html.parse("http://www.createdebate.com/debate/show/Does_Andrew_Jackson_deserve_to_be_on_the_20_bill_3")
test_debate = Debate('http://www.createdebate.com/debate/show/Does_Andrew_Jackson_deserve_to_be_on_the_20_bill_3')
s = test_debate.to_json()
print(s)
