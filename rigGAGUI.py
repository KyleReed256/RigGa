import sys
import maya.api.OpenMaya as om
import maya.cmds as cmds
import random
import numpy as np
from sets import Set
from functools import partial
import copy

##########################################################
# Plug-in
##########################################################
class GUI():

    def __init__(self, CTL_TREE,allStartingWeights,allNeutralWeights,
                 allCurrentGenWeights, strongestShapes, minMaxWeights, allSymmetryNames,
                 OTHER_FACE_IDS,MESH_NAME,AUTOMATE):

        self.ctlTree = CTL_TREE
        self.allStartingWeights = allStartingWeights
        self.allCurrentGenWeights = allCurrentGenWeights
        self.allCurrentWeights = allCurrentGenWeights
        self.allNeutralWeights = allNeutralWeights
        self.allMinMaxWeights = minMaxWeights
        self.strongestShapes = strongestShapes
        self.strongestShapesTree = {}
        self.generationSelection = []
        self.nextGeneration = []
        self.allSymmetryNames = allSymmetryNames
        self.buttonList = []
        self.newShapes = {}
        self.startingCurves = {}
        self.currentGenCurves = {}
        self.OTHER_FACE_IDS = OTHER_FACE_IDS
        self.originalStrongest = strongestShapes
        self.symGroups = {}
        self.lastElite = []
        self.NextGenePool = []
        self.CurrentGenePool = []
        self.EliteGenes = []
        self.MESH_NAME = MESH_NAME
        self.EliteGenErrors = []
        self.AUTOMATE = AUTOMATE

        self.STARTING_MESH_VERTS = self.getVertexPositions(0)

        print "strongestShapes"
        print strongestShapes

        self.newShapes = self.flattenDictToVals(self.strongestShapes)
        targetShapes = self.flattenDictToChildren(self.strongestShapes)
        strongestShapesTree = self.cropTreeToStrongestShapes()
        # strongestShapesNeutrals = self.getStrongestNeutralVals(self.strongestShapes)

        # self.strongestShapesNeutrals = strongestShapesNeutrals

        print "newShapes:"
        print self.newShapes
        print "targetShapes"
        print targetShapes
        print "strongestShapesTree"
        print strongestShapesTree
        # print "strongestShapesNeutrals"
        # print strongestShapesNeutrals

        self.strongestShapesTree = strongestShapesTree

        flattenedSyms = self.flattenDictToChildren(self.allSymmetryNames)

        # newShapesSym = self.correctSymmetryNames(newShapes, flattenedSyms)


        #self.linearBlendshape(self.strongestShapesTree)
        self.EliteGenes = self.getFaceWeights(self.allStartingWeights, 0)
        self.lastElite.append(self.getFaceWeights(self.allStartingWeights, 0))
        #self.sampleNonLinear(2,[1,2,3])

        self.sampleNewFaces(1, [1,2,3], "Sample")

        selectionUI = 'altUI'

        if cmds.window(selectionUI, exists=True):
            cmds.deleteUI(selectionUI)

        cmds.window(selectionUI, width=1000, height=200)
        form = cmds.formLayout()
        tabs = cmds.tabLayout(innerMarginWidth=10, innerMarginHeight=10, mcw=400, width=750, height=100)
        cmds.formLayout(form, edit=True,
                        attachForm=((tabs, 'top', 0), (tabs, 'left', 0), (tabs, 'bottom', 0), (tabs, 'right', 0)))

        child2 = cmds.gridLayout(numberOfColumns=4, cellWidthHeight=(300, 32))
        cmds.text("ELITE:", font="boldLabelFont", al="center")
        cmds.text("SAMPLE 1:", font="boldLabelFont", al="center")
        cmds.text("SAMPLE 2:", font="boldLabelFont", al="center")
        cmds.text("SAMPLE 3:", font="boldLabelFont", al="center")

        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="Set Elite:  ")
        controlGroup1 = cmds.optionMenu("controlGroup1")
        for key in range(1, 4):
            cmds.menuItem(label="SAMPLE " + str(key))
        cmds.button(label='    Set    ', command=partial(self.setFaceAsElite,1))
        cmds.setParent('..')

        cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'right', 0)])
        cmds.text("                                ")
        cmds.checkBox("face1cB", editable=True, label="  Select")
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'right', 0)])
        cmds.text("                                ")
        cmds.checkBox("face2cB", editable=True, label="  Select")
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'right', 0)])
        cmds.text("                                ")
        cmds.checkBox("face3cB", editable=True, label="  Select")
        cmds.setParent('..')

        cmds.text(label='')
        cmds.separator()
        cmds.separator()
        cmds.separator()

        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="                 ")
        cmds.button(label='Reset to Last Elite' , command=partial(self.resetToLastElite))
        cmds.text(label="                 ")
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="                 ")
        cmds.button(label='Sample Current Gen' , command=partial(self.sampleCurrentGen))
        cmds.text(label="                 ")
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="                 ")
        cmds.button(label='Add Selected to Gene Pool' , command=partial(self.addToGenePool, 0))
        cmds.text(label="                 ")
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="                 ")
        cmds.button(label='Breed Next Gen' , command=partial(self.breedNextGen))
        cmds.text(label="                 ")
        cmds.setParent('..')

        cmds.setParent('..')

        child1 = cmds.gridLayout(numberOfColumns=4, cellWidthHeight=(300, 32))
        cmds.text(label = "")
        cmds.text("Choose Group to Act on:", font="boldLabelFont", al="center")
        controlGroupSourceGroup = cmds.optionMenu("controlGroupSourceGroup")
        cmds.menuItem(label='All')
        for key1 in self.allStartingWeights.keys():
            cmds.menuItem(label=key1)
        cmds.text(label="")

        cmds.text("ELITE:", font="boldLabelFont", al="center")
        cmds.text("Choose Curve to Act on:", font="boldLabelFont", al="center")
        controlGroupSource = cmds.optionMenu("controlGroupSource")
        cmds.menuItem(label='All')
        for key1 in flattenedSyms:
            cmds.menuItem(label=key1)
        cmds.text("OPTIONS:", font="boldLabelFont", al="center")

        cmds.text(label='')
        cmds.separator()
        cmds.separator()
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'right', 0)])
        cmds.text("                                ")
        cmds.checkBox("symFlag", editable=True, label="  Symmetry", value=True)
        cmds.setParent('..')

        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="Set Elite:  ")
        controlGroup2 = cmds.optionMenu("controlGroup2")
        for key in range(1, 4):
            cmds.menuItem(label="SAMPLE " + str(key))
        cmds.button(label='    Set    ' , command=partial(self.setFaceAsElite,2))
        cmds.setParent('..')
        cmds.text("New Curves:", font="boldLabelFont", al="center")
        cmds.text(label='')
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'right', 0)])
        cmds.text("                                ")
        cmds.checkBox("activeOnlyFlag",editable=True, label="  Active blendshapes only")
        cmds.setParent('..')

        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="                 ")
        cmds.button(label='Reset Samples to Elite' , command=partial(self.copyEliteToSamples))
        cmds.text(label="                 ")
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="                 Number of BS's to sample:")
        cmds.intField("numKeys",minValue=1, maxValue=5, value=3, editable=True)
        cmds.text(label="                ")
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="                 ")
        cmds.button(label='Sample around Elite' , command=partial(self.sampleNewFaces, -1, [1,2,3], "Sample"))
        cmds.text(label="                 ")
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)], w=100)

        cmds.text(label="                          ")
        cmds.checkBox("localiseFlag", editable=True, label="  Localise sampling")
        cmds.text(label='                   ')
        cmds.setParent('..')

        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="                 ")
        cmds.button(label='Reset to Last Elite' , command=partial(self.resetToLastElite))
        cmds.text(label="                 ")
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="                 ")
        cmds.text(label="                 ")
        cmds.text(label="                 ")
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="                 ")
        cmds.button(label='Sample around Current', command=partial(self.sampleNewFaces,-1,[1,2,3],"Mutate"))
        cmds.text(label="                 ")
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)], w=100)

        cmds.text(label='                S.D: ')
        cmds.floatSliderGrp("sdVal", field=True, minValue=0.0, maxValue=1.0, fieldMinValue=0.0,
                            fieldMaxValue=1.0, value=0.3, cw=[(1, 50), (2, 120)])
        cmds.text(label='                ')
        cmds.setParent('..')

        cmds.setParent('..')

        cmds.tabLayout(tabs, edit=True, tabLabel=((child2, '\t\t\t\t\t\t\t\t\tEvolution\t\t\t\t\t\t\t\t\t'),
                                                  (child1, '\t\t\t\t\t\t\tAdvanced Control\t\t\t\t\t\t\t')))

        cmds.showWindow()

    def flattenDictToVals(self, dicto):

        returnList = []
        for vals in dicto.values():
            print vals
            if vals:
                for nodes in vals:
                    returnList.append(nodes[0])

        return returnList

    def flattenDictToChildren(self, dicto):

        returnDict = {}
        for vals in dicto.values():
            if vals:
                print "vals:"
                print vals
                returnDict.update(vals)

        return returnDict

    # def getStrongestNeutralVals(self, strongestShapes):
    #
    #     neutralTree = self.allNeutralWeights
    #     returnDict = {}
    #     for keys, vals in strongestShapes.iteritems():
    #         for keys2, vals2 in vals.iteritems():
    #             returnDict[keys][keys2] = neutralTree[keys][keys2]
    #
    #     return returnDict

    def cropTreeToStrongestShapes(self):

        startingTree = self.allStartingWeights
        strongestShapes = self.strongestShapes
        returnDict = {}
        for keys, vals in strongestShapes.iteritems():
            if vals:
                returnDict[keys] = {}
                for keys2 in vals:
                    print keys
                    print keys2
                    print keys2[0]
                    print startingTree[keys][keys2[0]]
                    returnDict[keys][keys2[0]] = startingTree[keys][keys2[0]]

        return returnDict

    def getFaceWeights(self, CTL_tree, faceID):

        groupDict = {}
        for key, group in CTL_tree.iteritems():
            nodeDict = {}
            for key2, node in group.iteritems():

                if faceID == 0:
                    outTransform = key2
                else:
                    nSId = key2.find(':')
                    if nSId != -1:
                        outTransform = key2[:nSId] + str(faceID) + key2[nSId:]
                    else:
                        outTransform = self.OTHER_FACE_IDS % faceID
                        outTransform = outTransform + key2

                attrWeight = cmds.getAttr(outTransform)
                nodeDict[key2] = attrWeight

            groupDict[key] = nodeDict

        return groupDict

    def setFaceWeights(self, CTL_tree, faceID):

        for key, group in CTL_tree.iteritems():
            for key2, node in group.iteritems():

                if faceID == 0:
                    outTransform = key2
                else:
                    nSId = key2.find(':')
                    if nSId != -1:
                        outTransform = key2[:nSId] + str(faceID) + key2[nSId:]
                    else:
                        outTransform = self.OTHER_FACE_IDS % faceID
                        outTransform = outTransform + key2
                try:
                    cmds.setAttr(outTransform, node)
                except:
                    # print "Symmetrical object doesn't exist"
                    continue

    def transferFaceWeights(self,sourceID,targetID):

        CTL_tree = self.allStartingWeights
        sourceTree = self.getFaceWeights(CTL_tree,sourceID)
        self.setFaceWeights(sourceTree,targetID)
        # print "Transferring FACE %i to FACE %i" % (sourceID, targetID)

    def copyEliteToSamples(self,*args):

        for face in range(1,4):
            self.transferFaceWeights(0,face)

    def setFaceAsElite(self,id, *args):

        self.lastElite.append(self.getFaceWeights(self.allStartingWeights,0))
        eliteChoice = cmds.optionMenu("controlGroup" + str(id), value=True, query=True)
        eliteNum = int(eliteChoice[-1])
        self.transferFaceWeights(eliteNum,0)
        self.EliteGenes = self.getFaceWeights(self.allStartingWeights, 0)

        if self.AUTOMATE:
            errorWeights = self.getSampledMeshError()
            self.EliteGenErrors.append(errorWeights[eliteNum-1])

        # print "Current EliteGenErrors %f" % self.EliteGenErrors

        if self.AUTOMATE and (len(self.EliteGenErrors) == 1):
            self.lastElite.append(self.getFaceWeights(self.allStartingWeights,0))
            self.automateRoutine(5,5)



    def resetToLastElite(self, *args):

        if len(self.lastElite) > 0:
            lastElite = self.lastElite[-1]
            self.lastElite = self.lastElite[:-1]
            self.setFaceWeights(lastElite, 0)
            self.EliteGenes = self.getFaceWeights(self.allStartingWeights, 0)
        else:
            print "First Elite Reached"



    def getVertexPositions(self, faceID):

        meshName = self.MESH_NAME
        if faceID != 0:
            nSId = meshName.find(':')
            if nSId != -1:
                meshName = meshName[:nSId] + str(faceID) + meshName[nSId:]
            else:
                outTransform = self.OTHER_FACE_IDS % faceID
                meshName = outTransform + meshName

        numVerts = cmds.polyEvaluate(meshName, v=True)
        # print meshName
        pointPositions = []
        for i in range(numVerts):
            p = cmds.pointPosition('%s.vtx[%i]' % (meshName,i), l=True)
            pointPositions.append(p)

        return pointPositions


    def getSampledMeshError(self):

        targetVerts = self.STARTING_MESH_VERTS
        self.transferFaceWeights(1,0)
        mesh1 = self.getVertexPositions(0)
        self.transferFaceWeights(2,0)
        mesh2 = self.getVertexPositions(0)
        self.transferFaceWeights(3,0)
        mesh3 = self.getVertexPositions(0)

        self.setFaceWeights(self.lastElite[-1], 0)

        mesh1Error = abs(np.array(targetVerts) - np.array(mesh1)).sum()
        mesh2Error = abs(np.array(targetVerts) - np.array(mesh2)).sum()
        mesh3Error = abs(np.array(targetVerts) - np.array(mesh3)).sum()

        print "Sample errors:"
        print "%f %f %f" % (mesh1Error,mesh2Error,mesh3Error)

        return [mesh1Error,mesh2Error,mesh3Error]

    def automateRoutine(self, numGens, numSamps):

        for gen in range(numGens):

            print "Processing Current Gen %i" % (gen+1)

            print "Current EliteGenErrors :"
            print self.EliteGenErrors
            currentBestSSE = self.EliteGenErrors[gen]
            print "currentBestSSE %f" % currentBestSSE
            currentGenePoolErrors = []
            sample = 1
            threshold = 1.1
            while len(currentGenePoolErrors) <= numSamps:

                print "Sample: %i" % (sample+1)
                self.sampleCurrentGen()
                sampleErrors = self.getSampledMeshError()

                for s,val in enumerate(sampleErrors):
                    if val < (currentBestSSE*threshold):
                        self.addToGenePool([s+1])
                        currentGenePoolErrors.append(val)

                sample = sample + 1

                if sample > 20:
                    threshold = threshold + 0.2
                    sample = 1

            # print "NextGenePool:"
            # print self.NextGenePool
            print "currentPoolErrors:"
            print currentGenePoolErrors

            bestSample = np.argmin(currentGenePoolErrors)
            bestSampleVal = currentGenePoolErrors[bestSample]
            print "bestSampleVal: %f" % bestSampleVal
            if(bestSampleVal < currentBestSSE):
                print "Changing bestSampleVal"
                eliteTree = self.NextGenePool[bestSample]
                self.setFaceWeights(eliteTree, 0)
                self.lastElite.append(self.getFaceWeights(self.allStartingWeights,0))

                mesh1 = self.getVertexPositions(0)
                mesh1Error = abs(np.array(self.STARTING_MESH_VERTS) - np.array(mesh1)).sum()
                print "Check bestSampleVal:%f = mesh1Error:%f " % (bestSampleVal, mesh1Error)
                self.EliteGenes = self.getFaceWeights(self.allStartingWeights, 0)
                self.EliteGenErrors.append(bestSampleVal)

            else:
                self.EliteGenErrors.append(currentBestSSE)

            self.breedNextGen()

        print "EliteGenErrors:"
        print self.EliteGenErrors

        self.resetToLastElite()
        mesh1 = self.getVertexPositions(0)
        mesh1Error = abs(np.array(self.STARTING_MESH_VERTS) - np.array(mesh1)).sum()
        print "mesh1Error:%f " % (mesh1Error)




    def sampleNewFaces(self, preGuiFlag, chosenFaces, mutateOrSample,*args):

        if preGuiFlag < 0:
            symFlag = cmds.checkBox("symFlag", value=True, query=True)
            numKeys = cmds.intField("numKeys", value=True, query=True)
            localiseFlag = cmds.checkBox("localiseFlag", value=True, query=True)
            activeOnlyFlag = cmds.checkBox("activeOnlyFlag", value=True, query=True)
            selectedGroup = cmds.optionMenu("controlGroupSourceGroup", value=True, query=True)
            selectedCurve = cmds.optionMenu("controlGroupSource", value=True, query=True)
            sdVal = cmds.floatSliderGrp("sdVal", value=True, query=True)

        else:
            symFlag = True
            numKeys = 3
            if not self.newShapes:
                localiseFlag = False
                activeOnlyFlag = False
            else:
                localiseFlag = True
                activeOnlyFlag = True
            sdVal = 0.5
            selectedGroup = 'All'
            selectedCurve = 'All'

        for sampleFace in chosenFaces:


            if activeOnlyFlag:
                parseTree = self.getFaceWeights(self.strongestShapesTree,0)
            else:
                parseTree = self.getFaceWeights(self.allStartingWeights, 0)

            if mutateOrSample == "Sample":

                self.transferFaceWeights(0,sampleFace)
                parseTree = self.getFaceWeights(self.allStartingWeights, 0)
            else:
                parseTree = self.getFaceWeights(self.allStartingWeights, sampleFace)

            # print "parseTree"
            # print parseTree
            # print "parseTreeWeights"
            # print parseTreeWeights

            for key, value in parseTree.iteritems():
                if selectedGroup != 'All' and selectedGroup != key:
                    continue
                if not value:
                    continue
                randKeys = random.sample(list(value), min(numKeys, len(value)))
                # print "RandKeys: %s" % randKeys
                for ctlKey in randKeys:
                    currentWeight = parseTree[key][ctlKey]
                    if localiseFlag:
                        randWeight = random.gauss(currentWeight, sdVal)
                    else:
                        minMaxWeight = self.allMinMaxWeights[key][ctlKey]
                        randWeight = random.uniform(minMaxWeight[0], minMaxWeight[1])

                    if symFlag:
                        opposite = self.allSymmetryNames[key][ctlKey]
                        try:
                            m = cmds.getAttr(opposite)
                        except:
                            continue
                        if (opposite == ctlKey) and (ctlKey[-1] == 'X'):
                            # print "Key: %s, Opposite: %s" % (ctlKey, opposite)
                            continue
                        if ctlKey[-1] == 'Y':
                            parseTree[key][opposite] = randWeight
                        elif ctlKey[-1] == 'X':
                            parseTree[key][opposite] = randWeight * -1
                        # else:
                            # print "Error with symmetry"

                    parseTree[key][ctlKey] = randWeight
                    self.setFaceWeights(parseTree,sampleFace)

        # errorWeights = self.getSampledMeshError()


    def addToGenePool(self, faceID, *args):

        faceToAdd = []

        if faceID == 0:

            face1cB = cmds.checkBox("face1cB", value=True, query=True)
            face2cB = cmds.checkBox("face2cB", value=True, query=True)
            face3cB = cmds.checkBox("face3cB", value=True, query=True)


            if face1cB: faceToAdd.append(1)
            if face2cB: faceToAdd.append(2)
            if face3cB: faceToAdd.append(3)

        else:

            faceToAdd = faceID

        for face in faceToAdd:
            outDict = self.getFaceWeights(self.allStartingWeights,face)
            self.NextGenePool.append(outDict)

        print "Next Gene Pool"
        for ng in self.NextGenePool:
            print ng


    def breedNextGen(self, *args):

        self.CurrentGenePool = copy.deepcopy(self.NextGenePool)
        self.NextGenePool = []

        self.sampleCurrentGen()

    def sampleCurrentGen(self, *args):

        if not self.CurrentGenePool:
            # print "Resampling with Empty Gene Pool"
            self.sampleNewFaces(-1,[1,2,3], "Sample")

        else:
            EliteCurves = self.EliteGenes
            currentGenePool = self.CurrentGenePool

            lenGenePool = len(currentGenePool)

            for face in range(1,4):

                SAMPLE_FACE = face
                # print SAMPLE_FACE

                # print "Sampling face: %s" % SAMPLE_FACE

                # Parent handling
                ELITE_THRESHOLD = 0.5

                eliteCoinFlip = random.random()

                if eliteCoinFlip < ELITE_THRESHOLD:
                    # print "Elite"
                    parent1 = EliteCurves
                    parent2 = random.sample(currentGenePool,1)
                    parent2 = parent2[0]
                else:
                    parent1,parent2 = random.sample(currentGenePool,2)

                # print "Parent 1:"
                # print parent1
                # print "Parent 2:"
                # print parent2

                #Curve Group Selection

                ALL_CURVES_THRESHOLD = 0.4
                GROUP_CURVES_THRESHOLD = 0.8
                SINGLE_CURVE_THRESHOLD = 1.0

                SWAP_AVG_THRESHOLD = 0.7
                swapAvgCoinFlip = random.random()
                if swapAvgCoinFlip < SWAP_AVG_THRESHOLD:
                    breedOperation = "Swap"
                else:
                    breedOperation = "Avg"

                # print "breedOperation: %s" % breedOperation

                whichCurvesCoinFlip = random.random()

                if whichCurvesCoinFlip <= ALL_CURVES_THRESHOLD:
                    curveChoice = "All"
                    bredCurve = self.breedCurves(parent1,parent2,breedOperation,curveChoice)
                elif whichCurvesCoinFlip <= GROUP_CURVES_THRESHOLD:
                    curveChoice = "Group"
                    bredCurve = self.breedCurves(parent1, parent2, breedOperation, curveChoice)
                elif whichCurvesCoinFlip <= SINGLE_CURVE_THRESHOLD:
                    curveChoice = "Single"
                    bredCurve = self.breedCurves(parent1, parent2, breedOperation, curveChoice)

                # print "curveChoice: %s" % curveChoice
                #
                # print "bredCurve:"
                # print bredCurve


                self.setFaceWeights(bredCurve, SAMPLE_FACE)



                # Curve Modification

                # THREE_RESAMPLE = 0.2
                # ONE_RESAMPLE = 0.6
                # DO_NOTHING_THRESHOLD = 1.0
                #
                # whichOperationCoinFlip = random.random()
                #
                # if whichOperationCoinFlip <= THREE_RESAMPLE:
                #     operationChoice = "Three resample"
                #     cmds.intField("numKeys", value=3, edit=True)
                # elif whichOperationCoinFlip <= ONE_RESAMPLE:
                #     operationChoice = "One resample"
                #     cmds.intField("numKeys", value=1, edit=True)
                # else:
                #     operationChoice = "Nothing"

                # print "operationChoice: %s" % operationChoice
                self.sampleNewFaces(-1, [SAMPLE_FACE], "Mutate")

        errorWeights = self.getSampledMeshError()

    def breedCurves(self,parent1,parent2,breedOperation,curveChoice):

        outCurves = copy.deepcopy(parent1)
        # print outCurves

        # if curveChoice == "Single":
        #     curveSelection = random.choice(self.symGroups.keys())
        #     groupSelection = "All"
        if curveChoice == "Group":
            groupSelection = random.choice(self.allStartingWeights.keys())
            curveSelection = "All"
        else:
            curveSelection = "All"
            groupSelection = "All"

        for faceGroup, ctlDict in parent1.iteritems():

            if curveChoice == "Group":
                if (faceGroup == groupSelection) and (curveSelection == "All"):
                    # print "Swapping Groups: %s" % faceGroup
                    outCurves[faceGroup] = parent2[faceGroup]
            # elif curveSelection != "All":
            #
            #     for ctlName, ctlVal in ctlDict.iteritems():
            #
            #         if self.symGroups[curveSelection][0] == ctlName:
            #             print "Swapping curve: %s" % ctlName
            #             outCurves[faceGroup][ctlName] = parent2[faceGroup][ctlName]
            #             outCurves[faceGroup][self.symGroups[curveSelection][1]] = parent2[faceGroup][self.symGroups[curveSelection][1]]
            else:
                for ctlName, ctlVal in ctlDict.iteritems():

                    if breedOperation == "Swap":
                        coinFlip = random.random()
                        if coinFlip < 0.5:
                            # print "Swapping All Curves"
                            outCurves[faceGroup][ctlName] = parent2[faceGroup][ctlName]
                            try:
                                outCurves[faceGroup][self.allSymmetryNames[faceGroup][ctlName]] = parent2[faceGroup][self.allSymmetryNames[faceGroup][ctlName]]
                            except:
                                continue

                    else:
                        # for keyId, keys in enumerate(ctlVal[0]):

                        # print "Averaging curves"

                        outCurves[faceGroup][ctlName] = (ctlVal + parent2[faceGroup][ctlName]) / 2
                        try:
                            outCurves[faceGroup][self.allSymmetryNames[faceGroup][ctlName]] = (ctlVal + parent2[faceGroup][ctlName]) / 2
                        except:
                            continue

        return outCurves

    # def modifyCurves(self, bredCurve, curveChoice, operationChoice, sf):
    #     if curveChoice == "Single":
    #         curveSelection = random.choice(self.symGroups.keys())
    #         groupSelection = "All"
    #     elif curveChoice == "Group":
    #         groupSelection = random.choice(self.strongestShapesTree.keys())
    #         curveSelection = "All"
    #     else:
    #         curveSelection = "All"
    #         groupSelection = "All"
    #
    #     print "Group: %s, Curve: %s" % (groupSelection, curveSelection)
    #     cmds.optionMenu("controlGroupSourceGroup", edit=True, value = groupSelection)
    #     cmds.optionMenu("controlGroupSource", edit=True, value=curveSelection)
    #
    #     if operationChoice == "Resample":
    #         print sf
    #         self.sampleNonLinear(2, sf)
    #     elif operationChoice == "Amp" or operationChoice == "Phase":
    #         self.sampleAmpPhase(operationChoice,sf)





