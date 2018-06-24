import sys
import maya.api.OpenMaya as om
import maya.cmds as cmds
import random
from functools import partial

class CTLnode():

    def __init__(self,longname, translateName, weightDict, weightMinMax,shortGroupName):
        ''' Constructor. '''
        self.DAGpath = longname
        self.name = longname[longname.rfind('|') + 1:]
        self.translateName = self.name + '.' + translateName

        self.weight = weightDict
        self.startingWeight = weightDict
        self.groupName = shortGroupName
        self.weightMinMax = weightMinMax

    def __str__(self):
        return "Group: %s CTL: %s, Val: %s" % (self.groupName, self.name, self.weight)

    @staticmethod
    def createCTLNodePerTranslate(longname,shortGroupName):

        tempMinXYZ = cmds.getAttr(longname + '.minTransLimit')
        tempMaxXYZ = cmds.getAttr(longname + '.maxTransLimit')
        tempWeight = cmds.getAttr(longname + '.translate')

        translateCTLs = []
        try:
            cmds.setAttr(longname + '.translateX', tempWeight[0][0])
            weightDict = tempWeight[0][0]
            weightMinMax = (tempMinXYZ[0][0], tempMaxXYZ[0][0])
            translateCTLs.append(CTLnode(longname, 'translateX', weightDict, weightMinMax,shortGroupName))
        except:
            pass
        try:
            cmds.setAttr(longname + '.translateY', tempWeight[0][1])
            weightDict = tempWeight[0][1]
            weightMinMax = (tempMinXYZ[0][1], tempMaxXYZ[0][1])
            translateCTLs.append(CTLnode(longname, 'translateY', weightDict, weightMinMax,shortGroupName))
        except:
            pass

        return translateCTLs

    def setWeight(self, newWeight):

        cmds.setAttr(self.translateName, newWeight)


class GUI():

    def __init__(self, CTL_TREE,allStartingWeights,allNeutralWeights,strongestShapes):

        self.ctlTree = CTL_TREE
        self.allStartingWeights = allStartingWeights
        self.allNeutralWeights = allNeutralWeights
        self.strongestShapes = strongestShapes

        winID = 'rigUI'

        if cmds.window(winID, exists=True):
            cmds.deleteUI(winID)
        cmds.window(winID, width = 100, height = 100)

        cmds.columnLayout("columnLayout")

        # Add controls into this Layout
        cmds.text(label="Mutate Rate Lower:")
        mRateLower = cmds.floatField("mRateLower", minValue=0.0, maxValue=1.0, value=0.0, editable=True,
                                      parent="columnLayout")
        cmds.text(label="Mutate Rate Upper:")
        mRateUpper = cmds.floatField("mRateUpper", minValue=0.0, maxValue=1.0, value=0.0, editable=True,
                                      parent="columnLayout")
        cmds.text(label="Constrain to Active Shapes:")
        constrainFlag = cmds.checkBox(label='constrainFlag', align='right', editable=True)
        cmds.button(label='Random', command=partial(self.randomMizeCTLs,mRateLower,mRateUpper,constrainFlag))
        cmds.button(label='Reset To Starting', command=partial(self.setCTLTreeTo, allStartingWeights))
        cmds.button(label='Reset To Neutral', command=partial(self.setCTLTreeTo, allNeutralWeights))

        # Display the window
        cmds.showWindow()

    def randomMizeCTLs(self, mRateLower, mRateUpper, cFlag, *args):
        print "Randomise"

        lowerLim = cmds.floatField(mRateLower, query=True, value=True)
        upperLim = cmds.floatField(mRateUpper, query=True, value=True)
        constrainFlag = cmds.checkBox(cFlag, query=True, value=True)

        if constrainFlag:
            for key, value in self.strongestShapes.iteritems():
                for sortedTuple in value:
                    currentNode = self.ctlTree[key][sortedTuple[0]]
                    print currentNode
                    currentWeight = currentNode.weight
                    randWeight = random.gauss(currentWeight,upperLim)
                    self.ctlTree[key][sortedTuple[0]].setWeight(randWeight)

        #else:
            # for key, value in self.ctlTree.iteritems():
            #     print "CTL GROUP: %s" % key
            #     for ctlNode in value:
            #         #print ctlNode
            #         currentWeight = ctlNode.weight
            #         minMaxWeight = ctlNode.weightMinMax
            #         randVal = currentWeight + random.uniform(lowerLim, upperLim)
            #         #random.uniform(mRateLower, mRateLower)
            #         ctlNode.setWeight(randVal)

    def setCTLTreeTo(self, weightTree, *args):
        for groupKey, groupNode in self.ctlTree.iteritems():
            for nodeKey,ctlNode in groupNode.iteritems():
                newWeight = weightTree[groupKey][ctlNode.translateName]
                ctlNode.setWeight(newWeight)


##########################################################
# Plug-in
##########################################################
class Main(om.MPxCommand):

    def __init__(self):
        ''' Constructor. '''
        om.MPxCommand.__init__(self)
        self.NEUTRAL_TIME = 0
        self.STARTING_TIME = 0

    def doIt(self, args):

        # Skeleton working stub
        print "Stub In 3"

        # We recommend parsing your arguments first.
        argVals = self.parseArguments(args)
        ctlId = argVals[0]
        self.NEUTRAL_TIME = argVals[1]

        print "Args... CTLid: %s neutralFrame %i\n" % (ctlId,self.NEUTRAL_TIME)




        selectionList = om.MGlobal.getActiveSelectionList()
        dagIterator = om.MItSelectionList(selectionList, om.MFn.kDagNode)

        CTL_TREE = self.createCTLgroupsList(dagIterator, ctlId)

        allStartingWeights = self.getNodeWeightList(CTL_TREE)

        print "allStartingWeights: %s" % allStartingWeights

        self.STARTING_TIME = cmds.currentTime(query=True)
        print "NEUTRAL_FRAME: %i, STARTING_FRAME: %i" % (self.NEUTRAL_TIME, self.STARTING_TIME)
        allNeutralWeights = self.getNodeWeightAtTime(CTL_TREE, self.NEUTRAL_TIME)

        print "allNeutralWeights: %s" % allNeutralWeights

        strongestShapes = self.getStrongestShapes(allStartingWeights, allNeutralWeights)

        print strongestShapes

        guiTemp = GUI(CTL_TREE,allStartingWeights,allNeutralWeights,strongestShapes)


        # Skeleton working stub
        print "Stub 1"

        # # API 1.0
        # selectionList = om.MSelectionList()
        # om.MGlobal.getActiveSelectionList(selectionList)

    def parseArguments(self, args):
        '''
        The presence of this function is not enforced,
        but helps separate argument parsing code from other
        command code.
        '''

        ctlShortFlagName = '-cis'
        ctlLongFlagName = '-controllerIdentifierString'
        neutralShortFlagName = '-nf'
        neutralLongFlagName = '-neutralFrame'

        # The following MArgParser object allows you to check if specific flags are set.
        argData = om.MArgParser(self.syntax(), args)
        print "argData: %s" % argData

        noFlag = True
        flagParams = []
        if argData.isFlagSet(ctlShortFlagName):
            # In this case, we print the passed flags's three parameters, indexed from 0 to 2.
            flagParams.append(argData.flagArgumentString(ctlShortFlagName, 0))
            noFlag = False
        if argData.isFlagSet(neutralLongFlagName):
            # In this case, we print the passed flags's three parameters, indexed from 0 to 2.
            flagParams.append(argData.flagArgumentDouble(neutralLongFlagName, 0))
            noFlag = False
        if noFlag:
            sys.stderr.write(
                "ERROR: No Control Identifier String Provided with function call e.g -cis 'CTL'\n"
            )

        return flagParams


    def createCTLgroupsList(self, pSelectionListIterator, ctlIdString):
        ''' Create a List of CTL group classes '''
        # Create an MDagPath object which will be populated on each iteration.

        if pSelectionListIterator.isDone():
            sys.stderr.write(
                "ERROR: No CTL groups selected. Select in Outliner View\n"
            )

        CTL_GROUP_OPTIONS = ['eye', 'brow', 'mouth', 'lower', 'upper', 'nose', 'ear', 'neck', 'chin', 'lip']


        dagPath = om.MDagPath()
        CTL_TREE = {}
        while (not pSelectionListIterator.isDone()):
            # Populate our MDagPath object. This will likely provide
            # us with a Transform node.
            dagPath = pSelectionListIterator.getDagPath()
            print dagPath
            dagPathStr = str(dagPath)
            print dagPathStr
            # self.printDagNodeInfo(dagPath)

            # Change Group name to a shorter name
            for cName in CTL_GROUP_OPTIONS:
                if cName in dagPathStr:
                    selectedGroupShort = cName
            print "New group name:%s" % selectedGroupShort

            # Get all Controllers
            leafTransformsLong = cmds.ls(dagPathStr, long=True, dag=True, allPaths=True, leaf=True)

            CTLgroup = {}
            for leaf in leafTransformsLong:
                longName = leaf[:leaf.rfind('|')]
                shortName = leaf[leaf.rfind('|') + 1:leaf.find('Shape')]
                if ctlIdString in shortName:
                    tempNode = CTLnode.createCTLNodePerTranslate(longName, selectedGroupShort)
                    for node in tempNode:
                        print node
                        keyName = node.translateName
                        CTLgroup[keyName] = node

            # Add to Tree and advance to the next item
            CTL_TREE[selectedGroupShort] = CTLgroup
            pSelectionListIterator.next()

        return CTL_TREE


    def getNodeWeightList(self, CTL_tree):


        groupDict = {}
        for key,group in CTL_tree.iteritems():
            nodeDict = {}
            for key2, node in group.iteritems():
                nodeDict[node.translateName] = node.weight

            groupDict[key] = nodeDict

        return groupDict

    def getNodeWeightAtTime(self, CTL_tree, time):

        if time:
            cmds.currentTime(time)

        groupDict = {}
        for key,group in CTL_tree.iteritems():
            nodeDict = {}
            for key2, node in group.iteritems():
                attrWeight = cmds.getAttr(node.translateName)
                nodeDict[node.translateName] = attrWeight

            groupDict[key] = nodeDict

        if time:
            cmds.currentTime(self.STARTING_TIME)

        return groupDict

    def getStrongestShapes(self, currentTree, neutralTree):

        sortedTree = {}
        for key1, group1 in currentTree.iteritems():
            neutralGroup = neutralTree[key1]
            diffDict = {k: abs(group1[k] - neutralTree.get(k, 0)) for k in group1.keys()}
            filteredDict = dict((k, v) for k, v in diffDict.iteritems() if v > 0.05)
            sortedDict = sorted(filteredDict.items(), key=lambda x: x[1], reverse=True)
            sortedTree[key1] = sortedDict

        return sortedTree

