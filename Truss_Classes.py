import math
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg


class Position:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


class Rectangle:
    def __init__(self):
        self.left = 0.0
        self.right = 0.0
        self.top = 0.0
        self.bottom = 0.0

    def width(self):
        return self.right - self.left

    def height(self):
        return self.top - self.bottom

    def centerX(self):
        return self.left + self.width() / 2.0

    def centerY(self):
        return self.bottom + self.height() / 2.0


class Material:
    def __init__(self, uts=0.0, ys=0.0, modulus=0.0, staticFactor=1.0):
        self.uts = uts
        self.ys = ys
        self.E = modulus
        self.staticFactor = staticFactor


class Node:
    def __init__(self, name="", position=None):
        self.name = name
        self.position = position if position is not None else Position()
        self.deadLoad = 0.0
        self.supportLoad = 0.0
        self.graphic = None


class Link:
    def __init__(self, name="", node1="", node2="", material="steel", width=1.0, thickness=0.25):
        self.name = name
        self.node1_Name = node1
        self.node2_Name = node2

        self.material = material.lower()
        self.width = float(width)
        self.thickness = float(thickness)

        self.length = 0.0
        self.angleRad = 0.0
        self.weight = 0.0
        self.graphic = None

    def density(self):
        if self.material.lower().startswith("al"):
            return 0.0975
        return 0.283

    def area(self):
        return self.width * self.thickness

    def calcWeight(self):
        self.weight = self.length * self.area() * self.density()
        return self.weight


class TrussModel:
    def __init__(self):
        self.title = ""
        self.links = []
        self.nodes = []
        self.material = Material()
        self.rct = Rectangle()
        self.totalWeight = 0.0

    def getNode(self, name):
        for node in self.nodes:
            if node.name.lower() == name.lower():
                return node
        return None

    def getCenterPt(self):
        if len(self.nodes) == 0:
            return

        self.rct.left = self.nodes[0].position.x
        self.rct.right = self.nodes[0].position.x
        self.rct.top = self.nodes[0].position.y
        self.rct.bottom = self.nodes[0].position.y

        for node in self.nodes:
            self.rct.left = min(self.rct.left, node.position.x)
            self.rct.right = max(self.rct.right, node.position.x)
            self.rct.top = max(self.rct.top, node.position.y)
            self.rct.bottom = min(self.rct.bottom, node.position.y)


class TrussView:
    def __init__(self):
        self.scene = qtw.QGraphicsScene()

        self.te_Report = qtw.QTextEdit()
        self.le_LongLinkName = qtw.QLineEdit()
        self.le_LongLinkNode1 = qtw.QLineEdit()
        self.le_LongLinkNode2 = qtw.QLineEdit()
        self.le_LongLinkLength = qtw.QLineEdit()
        self.gv = qtw.QGraphicsView()
        self.lbl_MousePos = qtw.QLabel()
        self.spnd_Zoom = qtw.QDoubleSpinBox()

        self.setupPensAndBrushes()

    def setupPensAndBrushes(self):
        self.penGrid = qtg.QPen(qtg.QColor.fromHsv(197, 144, 228, 50))
        self.penGrid.setWidth(1)

        self.penLink = qtg.QPen(qtg.QColor("darkGray"))
        self.penLink.setWidth(8)

        self.penNode = qtg.QPen(qtg.QColor("darkBlue"))
        self.penNode.setWidth(2)

        self.penLabel = qtg.QPen(qtg.QColor("darkMagenta"))
        self.penLabel.setWidth(1)

        self.brushGrid = qtg.QBrush(qtg.QColor.fromHsv(87, 98, 245, 128))
        self.brushNode = qtg.QBrush(qtg.QColor.fromRgb(230, 220, 80, 180))
        self.brushSupport = qtg.QBrush(qtg.QColor.fromRgb(200, 200, 200, 150))

    def setDisplayWidgets(self, args):
        self.te_Report = args[0]
        self.le_LongLinkName = args[1]
        self.le_LongLinkNode1 = args[2]
        self.le_LongLinkNode2 = args[3]
        self.le_LongLinkLength = args[4]
        self.gv = args[5]
        self.lbl_MousePos = args[6]
        self.spnd_Zoom = args[7]

        self.gv.setScene(self.scene)
        self.scene.setSceneRect(-180, -140, 360, 260)

    def displayReport(self, truss):
        st = "\tTruss Design Report\n"
        st += f"Title:  {truss.title}\n"
        st += f"Static Factor of Safety:  {truss.material.staticFactor:.2f}\n"
        st += f"Ultimate Strength:  {truss.material.uts:.2f}\n"
        st += f"Yield Strength:  {truss.material.ys:.2f}\n"
        st += f"Modulus of Elasticity:  {truss.material.E:.2f}\n"
        st += f"Total Truss Weight:  {truss.totalWeight:.3f} lb\n"
        st += "_____________Link Summary________________\n"
        st += "Link\t(1)\t(2)\tLength\tAngle\tMat\tWidth\tThick\tWeight\n"

        longest = None

        for link in truss.links:
            if longest is None or link.length > longest.length:
                longest = link

            st += (
                f"{link.name}\t{link.node1_Name}\t{link.node2_Name}\t"
                f"{link.length:.2f}\t{link.angleRad:.2f}\t"
                f"{link.material}\t{link.width:.2f}\t{link.thickness:.2f}\t"
                f"{link.weight:.3f}\n"
            )

        self.te_Report.setText(st)

        if longest is not None:
            self.le_LongLinkName.setText(longest.name)
            self.le_LongLinkNode1.setText(longest.node1_Name)
            self.le_LongLinkNode2.setText(longest.node2_Name)
            self.le_LongLinkLength.setText(f"{longest.length:.2f}")

    def buildScene(self, truss):
        self.scene.clear()
        self.drawGrid()
        self.drawLinks(truss)
        self.drawNodes(truss)

    def drawGrid(self):
        left = -160
        right = 160
        top = -110
        bottom = 110

        rect = qtw.QGraphicsRectItem(left, top, right - left, bottom - top)
        rect.setBrush(self.brushGrid)
        rect.setPen(self.penGrid)
        self.scene.addItem(rect)

        x = left
        while x <= right:
            line = qtw.QGraphicsLineItem(x, top, x, bottom)
            line.setPen(self.penGrid)
            self.scene.addItem(line)
            x += 10

        y = top
        while y <= bottom:
            line = qtw.QGraphicsLineItem(left, y, right, y)
            line.setPen(self.penGrid)
            self.scene.addItem(line)
            y += 10

    def transformPoint(self, truss, node):
        truss.getCenterPt()
        offsetX = truss.rct.centerX()
        offsetY = truss.rct.centerY()

        x = node.position.x - offsetX
        y = -(node.position.y - offsetY)

        return x, y

    def drawLinks(self, truss):
        for link in truss.links:
            n1 = truss.getNode(link.node1_Name)
            n2 = truss.getNode(link.node2_Name)

            if n1 is None or n2 is None:
                continue

            x1, y1 = self.transformPoint(truss, n1)
            x2, y2 = self.transformPoint(truss, n2)

            item = qtw.QGraphicsLineItem(x1, y1, x2, y2)
            item.setPen(self.penLink)
            item.setData(0, f"Link {link.name}")
            item.name = f"Link {link.name}"

            tooltip = (
                f"Link name = {link.name}\n"
                f"Material = {link.material}\n"
                f"Start = {link.node1_Name}\n"
                f"End = {link.node2_Name}\n"
                f"Length = {link.length:.3f} in\n"
                f"Angle = {math.degrees(link.angleRad):.3f} deg\n"
                f"Width = {link.width:.3f} in\n"
                f"Thickness = {link.thickness:.3f} in\n"
                f"Weight = {link.weight:.3f} lb"
            )

            item.setToolTip(tooltip)
            link.graphic = item
            self.scene.addItem(item)

    def drawNodes(self, truss):
        for node in truss.nodes:
            x, y = self.transformPoint(truss, node)

            if node.name.lower() == "left":
                self.drawPinSupport(x, y)
                supportText = f"Left support vertical load = {node.supportLoad:.3f} lb"
            elif node.name.lower() == "right":
                self.drawRollerSupport(x, y)
                supportText = f"Right roller vertical load = {node.supportLoad:.3f} lb"
            else:
                supportText = "Internal joint"

            circle = qtw.QGraphicsEllipseItem(x - 7, y - 7, 14, 14)
            circle.setPen(self.penNode)
            circle.setBrush(self.brushNode)
            circle.setData(0, f"Node {node.name}")
            circle.name = f"Node {node.name}"

            tooltip = (
                f"Node: {node.name}\n"
                f"x = {node.position.x:.3f} in\n"
                f"y = {node.position.y:.3f} in\n"
                f"Dead load from connected links = {node.deadLoad:.3f} lb\n"
                f"{supportText}"
            )

            circle.setToolTip(tooltip)
            node.graphic = circle
            self.scene.addItem(circle)

            self.drawLabel(x, y - 22, node.name)

    def drawPinSupport(self, x, y):
        points = qtg.QPolygonF([
            qtc.QPointF(x, y + 8),
            qtc.QPointF(x - 15, y + 30),
            qtc.QPointF(x + 15, y + 30)
        ])
        tri = qtw.QGraphicsPolygonItem(points)
        tri.setBrush(self.brushSupport)
        tri.setPen(self.penNode)
        self.scene.addItem(tri)

        base = qtw.QGraphicsLineItem(x - 22, y + 30, x + 22, y + 30)
        base.setPen(self.penNode)
        self.scene.addItem(base)

    def drawRollerSupport(self, x, y):
        points = qtg.QPolygonF([
            qtc.QPointF(x, y + 8),
            qtc.QPointF(x - 15, y + 25),
            qtc.QPointF(x + 15, y + 25)
        ])
        tri = qtw.QGraphicsPolygonItem(points)
        tri.setBrush(self.brushSupport)
        tri.setPen(self.penNode)
        self.scene.addItem(tri)

        for dx in [-9, 0, 9]:
            roller = qtw.QGraphicsEllipseItem(x + dx - 3, y + 27, 6, 6)
            roller.setBrush(self.brushSupport)
            roller.setPen(self.penNode)
            self.scene.addItem(roller)

        base = qtw.QGraphicsLineItem(x - 24, y + 36, x + 24, y + 36)
        base.setPen(self.penNode)
        self.scene.addItem(base)

    def drawLabel(self, x, y, text):
        label = qtw.QGraphicsTextItem(text)
        label.setDefaultTextColor(qtg.QColor("darkMagenta"))
        label.setPos(x - label.boundingRect().width() / 2, y - label.boundingRect().height() / 2)
        self.scene.addItem(label)


class TrussController:
    def __init__(self):
        self.truss = TrussModel()
        self.view = TrussView()

    def setDisplayWidgets(self, args):
        self.view.setDisplayWidgets(args)

    def installSceneEventFilter(self, obj):
        self.view.scene.installEventFilter(obj)

    def setZoom(self):
        self.view.gv.resetTransform()
        self.view.gv.scale(self.view.spnd_Zoom.value(), self.view.spnd_Zoom.value())

    def handleSceneEvent(self, obj, event):
        if obj != self.view.scene:
            return

        if event.type() == qtc.QEvent.GraphicsSceneMouseMove:
            scenePos = event.scenePos()
            msg = f"Mouse Position:  x = {scenePos.x():.2f}, y = {-scenePos.y():.2f}"

            items = self.view.scene.items(scenePos)
            names = []

            for item in items:
                if hasattr(item, "name"):
                    names.append(item.name)
                elif item.data(0) is not None:
                    names.append(str(item.data(0)))

            if len(names) > 0:
                msg += " | " + ", ".join(names)

            self.view.lbl_MousePos.setText(msg)

        if event.type() == qtc.QEvent.GraphicsSceneWheel:
            if event.delta() > 0:
                self.view.spnd_Zoom.stepUp()
            else:
                self.view.spnd_Zoom.stepDown()

    def ImportFromFile(self, data):
        self.truss = TrussModel()

        for rawLine in data:
            line = rawLine.strip()

            if len(line) == 0:
                continue

            if line.startswith("#"):
                continue

            cells = [c.strip().replace("'", "").replace('"', "") for c in line.split(",")]

            keyword = cells[0].lower()

            if keyword == "title":
                self.truss.title = cells[1]

            elif keyword == "material":
                sut = float(cells[1])
                sy = float(cells[2])
                E = float(cells[3])
                self.truss.material = Material(uts=sut, ys=sy, modulus=E)

            elif keyword.startswith("static"):
                self.truss.material.staticFactor = float(cells[1])

            elif keyword == "node":
                name = cells[1]
                x = float(cells[2])
                y = float(cells[3])
                self.truss.nodes.append(Node(name=name, position=Position(x=x, y=y)))

            elif keyword == "link":
                name = cells[1]
                n1 = cells[2]
                n2 = cells[3]

                material = "steel"
                width = 1.0
                thickness = 0.25

                if len(cells) >= 5 and cells[4] != "":
                    material = cells[4]

                if len(cells) >= 6 and cells[5] != "":
                    width = float(cells[5])

                if len(cells) >= 7 and cells[6] != "":
                    thickness = float(cells[6])

                self.truss.links.append(
                    Link(
                        name=name,
                        node1=n1,
                        node2=n2,
                        material=material,
                        width=width,
                        thickness=thickness
                    )
                )

        self.calcLinkVals()
        self.calcWeightsAndLoads()
        self.displayReport()
        self.drawTruss()

    def calcLinkVals(self):
        for link in self.truss.links:
            n1 = self.truss.getNode(link.node1_Name)
            n2 = self.truss.getNode(link.node2_Name)

            if n1 is None or n2 is None:
                continue

            dx = n2.position.x - n1.position.x
            dy = n2.position.y - n1.position.y

            link.length = math.sqrt(dx ** 2 + dy ** 2)
            link.angleRad = math.atan2(dy, dx)
            link.calcWeight()

    def calcWeightsAndLoads(self):
        self.truss.totalWeight = 0.0

        for node in self.truss.nodes:
            node.deadLoad = 0.0
            node.supportLoad = 0.0

        for link in self.truss.links:
            self.truss.totalWeight += link.weight

            n1 = self.truss.getNode(link.node1_Name)
            n2 = self.truss.getNode(link.node2_Name)

            if n1 is not None:
                n1.deadLoad += link.weight / 2.0

            if n2 is not None:
                n2.deadLoad += link.weight / 2.0

        left = self.truss.getNode("Left")
        right = self.truss.getNode("Right")

        if left is not None:
            left.supportLoad = self.truss.totalWeight / 2.0

        if right is not None:
            right.supportLoad = self.truss.totalWeight / 2.0

    def displayReport(self):
        self.view.displayReport(self.truss)

    def drawTruss(self):
        self.view.buildScene(self.truss)