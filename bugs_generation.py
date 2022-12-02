from xml.dom import minidom

LABEL = "inkscape:label"
TEXT = "#text"

def getChildWithTag(doc, tag):
    assert doc is not None
    for child in doc.childNodes:
        if child.nodeName == tag:
            return child
    return None

def getChildWithLabel(doc, label):
    assert doc is not None
    for child in doc.childNodes:
        if child.nodeName != TEXT and child.getAttribute(LABEL) == label:
                return child
    return None

def removeChildWithLabel(doc, label):
    assert doc is not None
    for child in doc.childNodes:
        if child.nodeName != TEXT and child.getAttribute(LABEL) == label:
                doc.removeChild(child)
                return
    raise Exception("No child with label {}".format(label))

from cairosvg import svg2png

def xmlDomToPNG(xmlObject, outputName):
    xmlAsString = xmlObject.toxml()
    svg2png(bytestring=bytes(xmlAsString, 'utf-8'), write_to=outputName)
    
from random import randint, random

def getRandomAngle(a, b):
    randomAngle = randint(a, b)
    if randomAngle < 0:
        return randomAngle + 360
    else:
        return randomAngle
    
GROUP = 'G'
PIVOT = 'P'

GROUP_ERROR_MESSAGE =  "Can apply transformation only to Groups (start with G)"

def isGroupLabel(label):
    return len(label) >= 1 and label[0] == GROUP

def isPivotLabel(label):
    return len(label) >= 1 and label[0] == PIVOT

def getChildPivotLabel(label):
    assert isGroupLabel(label), GROUP_ERROR_MESSAGE
    return PIVOT + label[1:]

def takeOutPivot(element) -> tuple:
    label = element.getAttribute(LABEL)
    childPivot = getChildWithLabel(element, getChildPivotLabel(label))
    assert childPivot is not None, "Pivot child was not found"
    
    pivotX, pivotY = childPivot.getAttribute("x"), childPivot.getAttribute("y")
    assert pivotX != "" and  pivotY != ""
    element.removeChild(childPivot)
    
    return pivotX, pivotY
    
from collections import namedtuple

Transform = namedtuple('Transform', ['pivotX', 'pivotY', 'rotation', 'deltaX', 'deltaY', 'scale'])
TRANSFORM = "transform"

def transformFromAngle(pivotX, pivotY, angle):
    return Transform(pivotX, pivotY, angle, 0, 0, 1)

def setElementTransform(element, transform: Transform):
    newRotation = "rotate({} {} {})".format(transform.rotation, transform.pivotX, transform.pivotY)
    newTranslation = "translate({} {})".format(transform.deltaX, transform.deltaY)
    newScale = "scale({})".format(transform.scale)
    element.setAttribute(TRANSFORM, newRotation + newTranslation + newScale)
    
from colorutils import Color, ArithmeticModel
import re
from random import choices

GREY = Color((100, 100, 100))
ORANGE = Color((255, 128, 0))
CYAN = Color((0, 255, 255))
BLUE = Color((0, 0, 255))
PINK = Color((255, 0, 127))
GREEN = Color((0, 255, 0))

def generateBugColors():
    color = choices([ORANGE, GREEN, BLUE, CYAN, PINK], [40, 30, 15, 10, 5])[0]
    tone = randint(0, 100)
    color = Color((tone, tone, tone), arithmetic=ArithmeticModel.BLEND) + color
    
    wingsColor = Color((tone, tone, tone), arithmetic=ArithmeticModel.BLEND) + color
    
    return color, wingsColor

def generateBackgroundColor():
    return choices([Color((202, 139, 73)), Color((128, 193, 218)), Color((134, 218, 128))], [60, 30, 10])[0]
    
def setColor(element, color):
    style = element.getAttribute("style")
    element.setAttribute("style", 
        re.sub('fill:#[0-9A-Za-z]{6}', 'fill:'+ color.hex, style))
    
def generateRandomBug(svgName, pngName):
    doc = minidom.parse(svgName)

    # get objects
    svg = doc.getElementsByTagName('svg')[0]
    layer = getChildWithTag(svg, "g")
    background = getChildWithTag(svg, "rect")
    bug = getChildWithLabel(layer, "GBug")
    leftWing = getChildWithLabel(bug, "GLeftWing")
    rightWing = getChildWithLabel(bug, "GRightWing")

    head = getChildWithLabel(bug, "GHead")
    leftWhisker = getChildWithLabel(head, "GLeftWhisker")
    rightWhisker = getChildWithLabel(head, "GRightWhisker")
    
    # change colors
    #svg.setAttribute("fill", generateBackgroundColor().hex)
    #layer.setAttribute("style", 'stroke-width: 0px; background-color: blue;')#+generateBackgroundColor().hex + "ff")
    #layer.setAttribute("color", "green")
    background.setAttribute("fill", generateBackgroundColor().hex)
    
    bodyColor, wingsColor = generateBugColors()
    bodySprite = getChildWithLabel(bug, "body")
    setColor(bodySprite, bodyColor)
    leftWingSprite = getChildWithLabel(leftWing, "leftWing")
    setColor(leftWingSprite, wingsColor)
    rightWingSprite = getChildWithLabel(rightWing, "rightWing")
    setColor(rightWingSprite, wingsColor)
    headSprite = getChildWithLabel(head, "head")
    setColor(headSprite, wingsColor)

    # apply transformation
    pivotX, pivotY = takeOutPivot(head)
    setElementTransform(head, Transform(pivotX, pivotY, getRandomAngle(-30, 0), 0, randint(-4, 0), 1))

    rightWingAngle = getRandomAngle(-40, 0)
    leftWingAngle = 360 - rightWingAngle
    pivotX, pivotY = takeOutPivot(leftWing)
    setElementTransform(leftWing, transformFromAngle(pivotX, pivotY, leftWingAngle))
    pivotX, pivotY = takeOutPivot(rightWing)
    setElementTransform(rightWing, transformFromAngle(pivotX, pivotY, rightWingAngle))

    pivotX, pivotY = takeOutPivot(leftWhisker)
    setElementTransform(leftWhisker, transformFromAngle(pivotX, pivotY, getRandomAngle(-50, 50)))
    pivotX, pivotY = takeOutPivot(rightWhisker)
    setElementTransform(rightWhisker, transformFromAngle(pivotX, pivotY, getRandomAngle(-50, 50)))

    setElementTransform(bug, Transform(64, 64, getRandomAngle(0, 360), randint(-10, 10), randint(-10, 10), random() + 0.5))

    # export to png
    xmlDomToPNG(doc, pngName)
    doc.unlink()
