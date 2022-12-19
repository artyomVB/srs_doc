from xml.dom import minidom
from cairosvg import svg2png
from random import randint, random, choices
from collections import namedtuple
from colorutils import Color, ArithmeticModel
import re

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

def xmlDomToPNG(xmlObject, outputName):
    xmlAsString = xmlObject.toxml()
    svg2png(bytestring=bytes(xmlAsString, 'utf-8'), write_to=outputName)

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

Transform = namedtuple('Transform', ['pivotX', 'pivotY', 'rotation', 'deltaX', 'deltaY', 'scale'])
TRANSFORM = "transform"

def transformFromAngle(pivotX, pivotY, angle):
    return Transform(pivotX, pivotY, angle, 0, 0, 1)

def setElementTransform(element, transform: Transform):
    newRotation = "rotate({} {} {})".format(transform.rotation, transform.pivotX, transform.pivotY)
    newTranslation = "translate({} {})".format(transform.deltaX, transform.deltaY)
    newScale = "scale({})".format(transform.scale)
    element.setAttribute(TRANSFORM, newRotation + newTranslation + newScale)

GREY = Color((100, 100, 100))
ORANGE = Color((255, 128, 0))
CYAN = Color((0, 255, 255))
BLUE = Color((0, 0, 255))
PINK = Color((255, 0, 127))
GREEN = Color((0, 255, 0))

def generateBugColors():
    color, rarity = choices([
        (ORANGE, 1), (GREEN, 2), (BLUE, 4), (CYAN, 6), (PINK, 8)
    ], [40, 30, 15, 10, 5])[0]
    tone = randint(0, 100)
    color = Color((tone, tone, tone), arithmetic=ArithmeticModel.BLEND) + color
    
    wingsColor = Color((tone, tone, tone), arithmetic=ArithmeticModel.BLEND) + color
    
    return color, wingsColor, rarity

def generateBackgroundColor():
    return choices([
        (Color((202, 139, 73)), 1), 
        (Color((128, 193, 218)), 2), 
        (Color((134, 218, 128)), 3)
    ], [60, 30, 10])[0]
    
TRANSFORMER = {
    "P": ["African", "European", "Russian", "American"],
    "B": ["Ladybug", "Bug", "Insect"],
    "T": ["Goliath", "Carpenter", "Paper", "Flying", "Stone", "Sun", "Wolf", "Blood", "Sugar"]
}

def generateName():
    form, rarity = choices([("B", 1), ("T B", 2), ("P B", 2), ("P T B", 4)], [0.5, 0.2, 0.2, 0.1])[0]
    result = [""]
    for symbol in form:
        if symbol not in TRANSFORMER:
            result.append(symbol)
        else:
            result.append(choices(TRANSFORMER[symbol])[0])
    return "".join(result), rarity
    
def setColor(element, color):
    style = element.getAttribute("style")
    element.setAttribute("style", 
        re.sub('fill:#[0-9A-Za-z]{6}', 'fill:'+ color.hex, style))
    
ObjectWithPivot = namedtuple('ObjectWithPivot', ['object', 'pivotX', 'pivotY'])

class BugGenerator:
    def __init__(self, svgName):
        self.doc = minidom.parse(svgName)

        self.svg = self.doc.getElementsByTagName('svg')[0]
        self.layer1 = getChildWithLabel(self.svg, "Layer 1")
        self.layer2 = getChildWithLabel(self.svg, "Layer 2")
        self.background = getChildWithTag(self.svg, "rect")
        self.bug = getChildWithLabel(self.layer1, "GBug")
        self.bodySprite = getChildWithLabel(self.bug, "body")
        leftWing = getChildWithLabel(self.bug, "GLeftWing")
        pivotX, pivotY = takeOutPivot(leftWing)
        self.leftWing = ObjectWithPivot(leftWing, pivotX, pivotY)
        self.leftWingSprite = getChildWithLabel(self.leftWing.object, "leftWing")
        rightWing = getChildWithLabel(self.bug, "GRightWing")
        pivotX, pivotY = takeOutPivot(rightWing)
        self.rightWing = ObjectWithPivot(rightWing, pivotX, pivotY)
        self.rightWingSprite = getChildWithLabel(self.rightWing.object, "rightWing")

        head = getChildWithLabel(self.bug, "GHead")
        pivotX, pivotY = takeOutPivot(head)
        self.head = ObjectWithPivot(head, pivotX, pivotY)
        self.headSprite = getChildWithLabel(self.head.object, "head")
        leftWhisker = getChildWithLabel(self.head.object, "GLeftWhisker")
        pivotX, pivotY = takeOutPivot(leftWhisker)
        self.leftWhisker = ObjectWithPivot(leftWhisker, pivotX, pivotY)
        rightWhisker = getChildWithLabel(self.head.object, "GRightWhisker")
        pivotX, pivotY = takeOutPivot(rightWhisker)
        self.rightWhisker = ObjectWithPivot(rightWhisker, pivotX, pivotY)
        
        self.hands = {'Left': [], 'Right': []}
        for side in ["Left", "Right"]:
            for i in range(1, 4):
                hand = getChildWithLabel(self.bug, "G{}Hand{}".format(side, i))
                pivotX, pivotY = takeOutPivot(hand)
                self.hands[side].append(ObjectWithPivot(hand, pivotX, pivotY))
        
        self.bugNameTextObject = getChildWithLabel(self.layer2, "BugName")
        self.bugNameText = self.bugNameTextObject.childNodes[0].childNodes[0]
        self.rarityTextObject = getChildWithLabel(self.layer2, "RarityText")
        self.rarityText = self.rarityTextObject.childNodes[0].childNodes[0]
    
    def regenerateBug(self):
        backgroundColor, backgroundRarity = generateBackgroundColor()
        self.background.setAttribute("fill", backgroundColor.hex)
        
        bodyColor, wingsColor, bugRarity = generateBugColors()
        setColor(self.bodySprite, bodyColor)
        setColor(self.leftWingSprite, wingsColor)
        setColor(self.rightWingSprite, wingsColor)
        setColor(self.headSprite, wingsColor)

        # apply transformation
        # 1) head
        setElementTransform(
            self.head.object, 
            Transform(self.head.pivotX, self.head.pivotY, getRandomAngle(-20, 20), 0, 0, 1))

        # 2) wings
        rightWingAngle = getRandomAngle(-40, 0)
        leftWingAngle = 360 - rightWingAngle
        setElementTransform(
            self.leftWing.object, 
            transformFromAngle(self.leftWing.pivotX, self.leftWing.pivotY, leftWingAngle))
        setElementTransform(
            self.rightWing.object, 
            transformFromAngle(self.rightWing.pivotX, self.rightWing.pivotY, rightWingAngle))

        # 3) whiskers
        setElementTransform(
            self.leftWhisker.object,
            transformFromAngle(self.leftWhisker.pivotX, self.leftWhisker.pivotY, getRandomAngle(-20, 20)))
        setElementTransform(
            self.rightWhisker.object, 
            transformFromAngle(self.rightWhisker.pivotX, self.rightWhisker.pivotY, getRandomAngle(-20, 20)))

        # 4) legs
        for side in ["Left", "Right"]:
            for i in range(3):
                hand = self.hands[side][i]
                angle = getRandomAngle(-10, 40) if side == "Left" else getRandomAngle(-40, 10)
                setElementTransform(
                    hand.object,
                    transformFromAngle(hand.pivotX, hand.pivotY, angle)
                )

        # 5) bug body
        setElementTransform(
            self.bug, 
            Transform(64, 64, getRandomAngle(0, 360), randint(-10, 10), randint(-10, 10), random() + 0.5))

        # 6) change names
        generatedName, nameRarity = generateName()
        self.bugNameTextObject.setAttribute(TRANSFORM, "rotate({})".format(random()*3.4 - 1.7))
        self.bugNameText.nodeValue = generatedName
        
        totalRarity = bugRarity + backgroundRarity + nameRarity
        rarityTextString = "Common"
        if totalRarity >= 6 and totalRarity < 8:
            rarityTextString = "Uncommon"
        elif totalRarity >= 8 and totalRarity < 12:
            rarityTextString = "Rare!"
        elif totalRarity >= 12:
            rarityTextString = "EPIC RARE!"
        self.rarityTextObject.setAttribute(TRANSFORM, "rotate({})".format(random()*3.4 - 1.7))
        self.rarityText.nodeValue = rarityTextString

    def exportToPNG(self, pngName):
        # 7) export to png
        xmlDomToPNG(self.doc, pngName)
        
    def exportToCSVString(self):
        return self.doc.toxml()
    
    def close(self):
        self.doc.unlink()
        
def generateRandomBug(svgName, pngName):
    doc = minidom.parse(svgName)

    # get objects
    svg = doc.getElementsByTagName('svg')[0]
    layer1 = getChildWithLabel(svg, "Layer 1")
    layer2 = getChildWithLabel(svg, "Layer 2")
    background = getChildWithTag(svg, "rect")
    bug = getChildWithLabel(layer1, "GBug")
    leftWing = getChildWithLabel(bug, "GLeftWing")
    rightWing = getChildWithLabel(bug, "GRightWing")

    head = getChildWithLabel(bug, "GHead")
    leftWhisker = getChildWithLabel(head, "GLeftWhisker")
    rightWhisker = getChildWithLabel(head, "GRightWhisker")
    
    # change colors
    backgroundColor, backgroundRarity = generateBackgroundColor()
    background.setAttribute("fill", backgroundColor.hex)
    
    bodyColor, wingsColor, bugRarity = generateBugColors()
    bodySprite = getChildWithLabel(bug, "body")
    setColor(bodySprite, bodyColor)
    leftWingSprite = getChildWithLabel(leftWing, "leftWing")
    setColor(leftWingSprite, wingsColor)
    rightWingSprite = getChildWithLabel(rightWing, "rightWing")
    setColor(rightWingSprite, wingsColor)
    headSprite = getChildWithLabel(head, "head")
    setColor(headSprite, wingsColor)

    # apply transformation
    # 1) head
    pivotX, pivotY = takeOutPivot(head)
    setElementTransform(head, Transform(pivotX, pivotY, getRandomAngle(-20, 20), 0, 0, 1))

    # 2) wings
    rightWingAngle = getRandomAngle(-40, 0)
    leftWingAngle = 360 - rightWingAngle
    pivotX, pivotY = takeOutPivot(leftWing)
    setElementTransform(leftWing, transformFromAngle(pivotX, pivotY, leftWingAngle))
    pivotX, pivotY = takeOutPivot(rightWing)
    setElementTransform(rightWing, transformFromAngle(pivotX, pivotY, rightWingAngle))

    # 3) whiskers
    pivotX, pivotY = takeOutPivot(leftWhisker)
    setElementTransform(leftWhisker, transformFromAngle(pivotX, pivotY, getRandomAngle(-20, 20)))
    pivotX, pivotY = takeOutPivot(rightWhisker)
    setElementTransform(rightWhisker, transformFromAngle(pivotX, pivotY, getRandomAngle(-20, 20)))

    # 4) legs
    for side in ["Left", "Right"]:
        for i in range(1, 4):
            hand = getChildWithLabel(bug, "G{}Hand{}".format(side, i))
            pivotX, pivotY = takeOutPivot(hand)
            angle = getRandomAngle(-10, 40) if side == "Left" else getRandomAngle(-40, 10)
            setElementTransform(
                hand,
                transformFromAngle(pivotX, pivotY, angle)
            )

    # 5) bug body
    setElementTransform(bug, Transform(64, 64, getRandomAngle(0, 360), randint(-10, 10), randint(-10, 10), random() + 0.5))

    # 6) change name
    generatedName, nameRarity = generateName()
    bugNameTextObject = getChildWithLabel(layer2, "BugName")
    bugNameTextObject.setAttribute(TRANSFORM, "rotate({})".format(random()*3.4 - 1.7))
    bugNameText = bugNameTextObject.childNodes[0].childNodes[0]
    bugNameText.nodeValue = generatedName
    
    totalRarity = bugRarity + backgroundRarity + nameRarity
    rarityTextString = "Common"
    if totalRarity >= 6 and totalRarity < 8:
        rarityTextString = "Uncommon"
    elif totalRarity >= 8 and totalRarity < 12:
        rarityTextString = "Rare!"
    elif totalRarity >= 12:
        rarityTextString = "EPIC RARE!"
    rarityTextObject = getChildWithLabel(layer2, "RarityText")
    rarityTextObject.setAttribute(TRANSFORM, "rotate({})".format(random()*3.4 - 1.7))
    rarityText = rarityTextObject.childNodes[0].childNodes[0]
    rarityText.nodeValue = rarityTextString

    # export to png
    xmlDomToPNG(doc, pngName)
    doc.unlink()
