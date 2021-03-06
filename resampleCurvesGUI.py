import sys
import maya.api.OpenMaya as om
import maya.cmds as cmds
import random
from sets import Set
from functools import partial
import copy

##########################################################
# Plug-in
##########################################################
class GUI():

    def __init__(self, CTL_TREE,allStartingWeights,allNeutralWeights,
                 allCurrentGenWeights, strongestShapes, minMaxWeights, allSymmetryNames,OTHER_FACE_IDS, NOISE_OR_DENOISE):

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
        self.lastElite = self.saveFaceCurves()
        self.NextGenePool = []
        self.CurrentGenePool = []
        self.EliteGenes = []
        self.NOISE_OR_DENOISE = NOISE_OR_DENOISE

        self.minSliderTime = int(cmds.playbackOptions(minTime=True, query=True))
        self.maxSliderTime = int(cmds.playbackOptions(maxTime=True, query=True))

        print "strongestShapes"
        print strongestShapes

        newShapes = self.flattenDictToVals(self.strongestShapes)
        targetShapes = self.flattenDictToChildren(self.strongestShapes)
        strongestShapesTree = self.cropTreeToStrongestShapes()
        # strongestShapesNeutrals = self.getStrongestNeutralVals(self.strongestShapes)

        # self.strongestShapesNeutrals = strongestShapesNeutrals

        print "newShapes:"
        print newShapes
        print "targetShapes"
        print targetShapes
        print "strongestShapesTree"
        print strongestShapesTree
        # print "strongestShapesNeutrals"
        # print strongestShapesNeutrals

        self.strongestShapesTree = strongestShapesTree

        flattenedSyms = self.flattenDictToChildren(self.allSymmetryNames)

        newShapesSym = self.correctSymmetryNames(newShapes, flattenedSyms)

        # if self.NOISE_OR_DENOISE == "NOISE":
        #     self.initElite(self.strongestShapesTree, 5)

        self.copyEliteToSamples(self.strongestShapesTree)
        self.EliteGenes = self.saveFaceCurves()

        if self.NOISE_OR_DENOISE == "NOISE":
            self.resampleCurvesNoise(1, [1,2,3])
        elif self.NOISE_OR_DENOISE == "DENOISE":
            self.resampleCurvesDenoise(1, [1,2,3])

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
        cmds.button(label='Reset to Last Elite', command=partial(self.resetToLastElite))
        cmds.text(label="                 ")
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="                 ")
        cmds.button(label='Sample Current Gen', command=partial(self.sampleCurrentGen))
        cmds.text(label="                 ")
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="                 ")
        cmds.button(label='Add Selected to Gene Pool', command=partial(self.addToGenePool))
        cmds.text(label="                 ")
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="                 ")
        cmds.button(label='Breed Next Gen', command=partial(self.breedNextGen))
        cmds.text(label="                 ")
        cmds.setParent('..')

        cmds.setParent('..')

        child1 = cmds.gridLayout(numberOfColumns=4, cellWidthHeight=(300, 32))
        cmds.text(label = "")
        cmds.text("Choose Group to Act on:", font="boldLabelFont", al="center")
        controlGroupSourceGroup = cmds.optionMenu("controlGroupSourceGroup")
        cmds.menuItem(label='All')
        for key1 in strongestShapesTree.keys():
            cmds.menuItem(label=key1)
        cmds.text(label="")

        cmds.text("ELITE:", font="boldLabelFont", al="center")
        cmds.text("Choose Curve to Act on:", font="boldLabelFont", al="center")
        controlGroupSource = cmds.optionMenu("controlGroupSource")
        cmds.menuItem(label='All')
        for key1 in newShapesSym:
            cmds.menuItem(label=key1)
        cmds.text("OPTIONS:", font="boldLabelFont", al="center")

        cmds.text(label='')
        cmds.separator()
        cmds.separator()
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'right', 0)])
        cmds.text("                                ")
        cmds.checkBox(editable=True, label="  Symmetry", value=True)
        cmds.setParent('..')

        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="Set Elite:  ")
        controlGroup2 = cmds.optionMenu("controlGroup2")
        for key in range(1, 4):
            cmds.menuItem(label="SAMPLE " + str(key))
        cmds.button(label='    Set    ', command=partial(self.setFaceAsElite,2))
        cmds.setParent('..')
        cmds.text("Resample Timestep:", font="boldLabelFont", al="center")
        cmds.text("Resample Noise:", font="boldLabelFont", al="center")
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'right', 0)])
        cmds.text("                                ")
        cmds.checkBox("unconstrainedRandom", editable=True, label="  Constrain", value=True)
        cmds.setParent('..')

        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="                 ")
        cmds.button(label='Reset Samples to Elite', command=partial(self.copyEliteToSamples,self.strongestShapesTree))
        cmds.text(label="                 ")
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        if self.NOISE_OR_DENOISE == "NOISE":
            cmds.text(label="                 Sample Step:")
            cmds.intField("sampleStep", minValue=1, maxValue=1000, value=5, editable=True)
        elif self.NOISE_OR_DENOISE == "DENOISE":
            cmds.text(label="            Time Tolerance:")
            cmds.floatField("timeTol", minValue=0.0, maxValue=1.0, value=0.5, editable=True)
        cmds.text(label="                ")
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)], w=100)
        if self.NOISE_OR_DENOISE == "NOISE":
            cmds.text(label='                S.D: ')
            cmds.floatSliderGrp("sdVal", field=True, minValue=0.0, maxValue=0.5, fieldMinValue=0.0,
                            fieldMaxValue=0.5, value=0.01, cw=[(1, 50), (2, 120)])
        elif self.NOISE_OR_DENOISE == "DENOISE":
            cmds.text(label="           Val Tolerance:")
            cmds.floatField("valTol", minValue=0.0, maxValue=0.1, value=0.01, editable=True)
        cmds.text(label='                   ')
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)], w=100)

        cmds.text(label='                Threshold: ')
        cmds.floatSliderGrp("sdThreshold", field=True, minValue=0.0, maxValue=0.003, fieldMinValue=0.0,
                            fieldMaxValue=0.003, value=0.001, cw=[(1, 50), (2, 120)])
        cmds.text(label='                   ')
        cmds.setParent('..')

        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'),
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'right', 0)])
        cmds.text(label="                 ")
        cmds.button(label='Reset to Last Elite', command=partial(self.resetToLastElite))
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
        if self.NOISE_OR_DENOISE == "NOISE":
            cmds.button(label='Sample', command=partial(self.resampleCurvesNoise,-1, [1,2,3]))
        else:
            cmds.button(label='Sample', command=partial(self.resampleCurvesDenoise, -1, [1, 2, 3]))
        cmds.text(label="                 ")
        cmds.setParent('..')
        cmds.text(label="                 ")

        cmds.setParent('..')

        cmds.tabLayout(tabs, edit=True, tabLabel=((child2, '\t\t\t\t\t\t\t\t\tEvolution\t\t\t\t\t\t\t\t\t'),
                                                  (child1, '\t\t\t\t\t\t\tAdvanced Control\t\t\t\t\t\t\t')))

        cmds.showWindow()

    # def initElite(self, blendshapeTargetTree, samplingStep):
    #
    #     startTime = self.minSliderTime
    #     endTime = self.maxSliderTime
    #     for faceGroup, ctlDict in blendshapeTargetTree.iteritems():
    #
    #         for ctlName, ctlVal in ctlDict.iteritems():
    #
    #             for frame in range(startTime,endTime,samplingStep):
    #
    #                 cmds.setKeyframe(ctlName, t=(frame, frame), insert=True)


    def copyEliteToSamples(self, blendshapeTargetTree, *args):

    	print blendshapeTargetTree

        for faceGroup, ctlDict in blendshapeTargetTree.iteritems():

            for ctlName, ctlVal in ctlDict.iteritems():

            	print faceGroup + ":" + ctlName

                nSId = ctlName.find(':')
                if nSId != -1:
                    print "in"
                    out1 = ctlName[:nSId] + str(1) + ctlName[nSId:]
                    out2 = ctlName[:nSId] + str(2) + ctlName[nSId:]
                    out3 = ctlName[:nSId] + str(3) + ctlName[nSId:]
                    print out1

                else:
                    out1 = (self.OTHER_FACE_IDS + ctlName) % 1
                    out2 = (self.OTHER_FACE_IDS + ctlName) % 2
                    out3 = (self.OTHER_FACE_IDS + ctlName) % 3
                    print out1

                cmds.copyKey(ctlName, time=(self.minSliderTime, self.maxSliderTime), option="keys")  # or keys?
                try:
	                cmds.pasteKey(out1, time=(self.minSliderTime, self.maxSliderTime), option="replace")
	                cmds.pasteKey(out2, time=(self.minSliderTime, self.maxSliderTime), option="replace")
	                cmds.pasteKey(out3, time=(self.minSliderTime, self.maxSliderTime), option="replace")
                except:
                	"Curve doesn't exist"
                	continue


    def resampleCurvesNoise(self, FLAG, chosenFaces, *args):



        # if localiseFlag:
        #     self.copyEliteToSamples(self.allStartingWeights)
        # else:

        blendshapeTargetTree = self.strongestShapesTree
        blendshapeSourceTree = self.allNeutralWeights

        print "chosenFaces:"
        print chosenFaces

        for sampleFace in chosenFaces:

            if FLAG < 0:
                SAMPLE_STEP = cmds.intField("sampleStep", value=True, query=True)
                MUTATION_VAL = cmds.floatSliderGrp("sdVal", value=True, query=True)
                MUTATION_THRESHOLD = cmds.floatSliderGrp("sdThreshold", value=True, query=True)
                selectedGroup = cmds.optionMenu("controlGroupSourceGroup", value=True, query=True)
                selectedCurve = cmds.optionMenu("controlGroupSource", value=True, query=True)
                unconstrainedRandom = cmds.checkBox("unconstrainedRandom", query=True, value=True)

            else:
                SAMPLE_STEP = random.choice([random.randint(1, 5), random.randrange(5, 25, 5)])
                MUTATION_VAL = random.uniform(0.00, 0.01)
                MUTATION_THRESHOLD = random.uniform(0.000, 0.002)
                selectedGroup = 'All'
                selectedCurve = 'All'
                unconstrainedRandom = True


            print "Sample Step %i, Mutate Val %f, Mutate Threshold %f" % (SAMPLE_STEP, MUTATION_VAL, MUTATION_THRESHOLD)

            for faceGroup, ctlDict in blendshapeTargetTree.iteritems():

                for ctlName, ctlVal in ctlDict.iteritems():

                    self.individualCurveSample(ctlName, faceGroup, MUTATION_VAL, SAMPLE_STEP, MUTATION_THRESHOLD, sampleFace,unconstrainedRandom)



    def individualCurveSample(self, curveName, faceGroup, mutateSD, samplingStep, MUTATION_THRESHOLD, sampleFace,unconstrainedRandom):

        print "Entered Ind Sample"
        startTime = self.minSliderTime
        endTime = self.maxSliderTime

        nSId = curveName.find(':')
        if nSId != -1:
            outTransform = curveName[:nSId] + str(sampleFace) + curveName[nSId:]
        else:
            outTransform = self.OTHER_FACE_IDS % sampleFace
            outTransform = outTransform + curveName

        cmds.cutKey(outTransform, time=(self.minSliderTime+1, self.maxSliderTime-1), option="keys")
        cmds.copyKey(curveName, time=(self.minSliderTime, self.maxSliderTime), option="keys")  # or keys?
        cmds.pasteKey(outTransform, time=(self.minSliderTime, self.maxSliderTime), option="replace")

        for frame in range(startTime + 1, endTime - 1, samplingStep):

            cmds.setKeyframe(outTransform, t=(frame, frame), insert=True)

        for frame in range(startTime + samplingStep+1, endTime - samplingStep-1, samplingStep):
            currentVal = cmds.keyframe(outTransform, time=(frame, frame), valueChange=True, query=True)
            prevVal = cmds.keyframe(outTransform, time=(frame - samplingStep, frame - samplingStep), valueChange=True, query=True)
            nextVal = cmds.keyframe(outTransform, time=(frame + samplingStep, frame + samplingStep), valueChange=True, query=True)
            print currentVal
            if ( abs(nextVal[0] - currentVal[0]) < MUTATION_THRESHOLD ):
                print "Big Random"
                mutatedVal = random.gauss(currentVal[0], mutateSD)
            elif not unconstrainedRandom:
                mutatedVal = random.gauss(currentVal[0], mutateSD)
            else:
                mutateOrNot = random.uniform(0.0, 1.0)
                if mutateOrNot <= 0.5:
                    mutatedVal = random.uniform(prevVal[0], nextVal[0])
                    mutatedVal = (mutatedVal + currentVal[0]) / 2
                else:
                    mutatedVal = currentVal[0]
            print "Current Val %f -> Mutated: %f" % (currentVal[0],mutatedVal)
            cmds.setKeyframe(outTransform, t=(frame, frame), v=mutatedVal)


    def resampleCurvesDenoise(self, FLAG, chosenFaces, *args):



        # if localiseFlag:
        #     self.copyEliteToSamples(self.allStartingWeights)
        # else:

        blendshapeTargetTree = self.strongestShapesTree
        blendshapeSourceTree = self.allNeutralWeights

        print "chosenFaces:"
        print chosenFaces

        for sampleFace in chosenFaces:

            if FLAG < 0:
                TIME_VAL = cmds.floatField("timeTol", value=True, query=True)
                THRESHOLD_VAL = cmds.floatField("valTol", value=True, query=True)
                selectedGroup = cmds.optionMenu("controlGroupSourceGroup", value=True, query=True)
                selectedCurve = cmds.optionMenu("controlGroupSource", value=True, query=True)

            else:
                TIME_VAL = random.uniform(0.00, 0.8)
                THRESHOLD_VAL = random.uniform(0.000, 0.05)
                selectedGroup = 'All'
                selectedCurve = 'All'


            print "TIME_VAL %f, THRESHOLD_VAL %f" % (TIME_VAL, THRESHOLD_VAL)

            for faceGroup, ctlDict in blendshapeTargetTree.iteritems():

                for ctlName, ctlVal in ctlDict.iteritems():

                    self.individualCurveDenoise(ctlName, faceGroup, TIME_VAL, THRESHOLD_VAL, sampleFace)



    def individualCurveDenoise(self, curveName, faceGroup, TIME_VAL, THRESHOLD_VAL, sampleFace):

        print "Entered Ind Sample"
        startTime = self.minSliderTime
        endTime = self.maxSliderTime

        nSId = curveName.find(':')
        if nSId != -1:
            outTransform = curveName[:nSId] + str(sampleFace) + curveName[nSId:]
        else:
            outTransform = self.OTHER_FACE_IDS % sampleFace
            outTransform = outTransform + curveName

        cmds.cutKey(outTransform, time=(self.minSliderTime+1, self.maxSliderTime-1), option="keys")
        cmds.copyKey(curveName, time=(self.minSliderTime, self.maxSliderTime), option="keys")  # or keys?
        cmds.pasteKey(outTransform, time=(self.minSliderTime, self.maxSliderTime), option="replace")

        cmds.filterCurve(outTransform, filter="simplify", timeTolerance=TIME_VAL, tolerance=THRESHOLD_VAL)



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

    def correctSymmetryNames(self, flattened, flattenedSyms):

        returnList = []
        returnDict = {}

        print "flattened , flattenedSymn"
        print flattened
        print flattenedSyms
        print "end"
        for vid,vals in enumerate(flattened):
            print vals
            symVal = flattenedSyms[vals]
            if (symVal in flattened) and (vals != symVal):
                flattened.pop(vid)
                setVal = Set(vals.split('_'))
                print setVal
                setSymVal = Set(symVal.split('_'))
                print setSymVal
                seq = '_'.join(setVal & setSymVal)
                print "seq:"
                print seq
                returnList.append(seq)
                returnDict[seq] = (vals,symVal)
            else:
                returnList.append(vals)
                returnDict[vals] = (vals,vals)

        self.symGroups = returnDict
        return returnList

    def setFaceAsElite(self, id,*args):

        self.lastElite = self.saveFaceCurves()

        eliteChoice = cmds.optionMenu("controlGroup" + str(id), value=True, query=True)
        eliteNum = int(eliteChoice[-1])

        shapeTree = self.strongestShapesTree

        for faceGroup, ctlDict in shapeTree.iteritems():

            for ctlName, ctlVal in ctlDict.iteritems():

                nSId = ctlName.find(':')
                if nSId != -1:
                    print "in"
                    out1 = ctlName[:nSId] + str(eliteNum) + ctlName[nSId:]

                else:
                    out1 = (self.OTHER_FACE_IDS + ctlName) % eliteNum

                cmds.cutKey(ctlName, time=(self.minSliderTime+1, self.maxSliderTime-1), option="keys")
                cmds.copyKey(out1, time=(self.minSliderTime, self.maxSliderTime), option="keys")  # or keys?
                cmds.pasteKey(ctlName, time=(self.minSliderTime, self.maxSliderTime), option="replace")

        self.EliteGenes = self.saveFaceCurves()

    def saveFaceCurves(self):

        shapeTree = self.strongestShapesTree

        outDict = {}
        for faceGroup, ctlDict in shapeTree.iteritems():
            outGroup = {}
            for ctlName, ctlVal in ctlDict.iteritems():
                keys = cmds.keyframe(ctlName, time=(self.minSliderTime, self.maxSliderTime), valueChange=True, query=True)
                times = cmds.keyframe(ctlName, time=(self.minSliderTime, self.maxSliderTime), timeChange=True, query=True)

                outGroup[ctlName] = (keys, times)
            outDict[faceGroup] = outGroup

        return outDict

    def saveFaceCurvesSamples(self, faceId):

        shapeTree = self.strongestShapesTree

        outDict = {}
        for faceGroup, ctlDict in shapeTree.iteritems():
            outGroup = {}
            for ctlName, ctlVal in ctlDict.iteritems():

                nSId = ctlName.find(':')
                if nSId != -1:
                    print "in"
                    out1 = ctlName[:nSId] + str(faceId) + ctlName[nSId:]

                else:
                    out1 = (self.OTHER_FACE_IDS + ctlName) % faceId

                keys = cmds.keyframe(out1, time=(self.minSliderTime+1, self.maxSliderTime-1), valueChange=True, query=True)
                times = cmds.keyframe(out1, time=(self.minSliderTime+1, self.maxSliderTime-1), timeChange=True, query=True)

                outGroup[ctlName] = (keys, times)
            outDict[faceGroup] = outGroup

        return outDict

    def resetToLastElite(self, *args):

        lastElite = self.lastElite

        outDict = {}
        for faceGroup, ctlDict in lastElite.iteritems():
            for ctlName, ctlVal in ctlDict.iteritems():
                cmds.cutKey(ctlName, time=(self.minSliderTime+1, self.maxSliderTime-1), option="keys")
                for keyId, keys in enumerate(ctlVal[0]):
                    times = ctlVal[1][keyId]

                    cmds.setKeyframe(ctlName, t=(times, times), v=keys)

        self.EliteGenes = self.saveFaceCurves()


    def addToGenePool(self, *args):

        face1cB = cmds.checkBox("face1cB", value=True, query=True)
        face2cB = cmds.checkBox("face2cB", value=True, query=True)
        face3cB = cmds.checkBox("face3cB", value=True, query=True)

        faceToAdd = []

        if face1cB: faceToAdd.append(1)
        if face2cB: faceToAdd.append(2)
        if face3cB: faceToAdd.append(3)

        for face in faceToAdd:
            outDict = self.saveFaceCurvesSamples(face)
            self.NextGenePool.append(outDict)

        print self.NextGenePool


    def breedNextGen(self, *args):

        self.CurrentGenePool = self.NextGenePool
        self.NextGenePool = []

        self.sampleCurrentGen()

    def sampleCurrentGen(self, *args):

        if not self.CurrentGenePool:
            print "Resampling with Empty Gene Pool"
            if self.NOISE_OR_DENOISE == "NOISE":
                self.resampleCurvesNoise(1,[1,2,3])
            elif self.NOISE_OR_DENOISE == "DENOISE":
                self.resampleCurvesDenoise(1, [1, 2, 3])

        else:
            EliteCurves = self.EliteGenes
            currentGenePool = self.CurrentGenePool

            lenGenePool = len(currentGenePool)

            for face in range(1,4):

                SAMPLE_FACE = [face]
                print SAMPLE_FACE

                print "Sampling face: %s" % SAMPLE_FACE

                # Parent handling
                ELITE_THRESHOLD = 0.5

                eliteCoinFlip = random.random()

                if eliteCoinFlip < ELITE_THRESHOLD:
                    print "Elite"
                    parent1 = EliteCurves
                    parent2 = random.sample(currentGenePool,1)
                    parent2 = parent2[0]
                else:
                    parent1,parent2 = random.sample(currentGenePool,2)

                print "Parent 1:"
                print parent1
                print "Parent 2:"
                print parent2

                #Curve Group Selection

                ALL_CURVES_THRESHOLD = 0.4
                GROUP_CURVES_THRESHOLD = 0.8
                SINGLE_CURVE_THRESHOLD = 1.0

                breedOperation = "Swap"

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

                print "curveChoice: %s" % curveChoice

                print "bredCurve:"
                print bredCurve


                self.setSampleFaceAs(bredCurve, SAMPLE_FACE)

                # Curve Modification

                RESAMPLE_THRESHOLD= 0.5
                DO_NOTHING_THRESHOLD = 1.0

                whichOperationCoinFlip = random.random()

                if whichOperationCoinFlip <= RESAMPLE_THRESHOLD:
                    operationChoice = "Resample"
                    self.modifyCurves(bredCurve, curveChoice, operationChoice, SAMPLE_FACE)
                else:
                    operationChoice = "Nothing"

                print "operationChoice: %s" % operationChoice

    def breedCurves(self,parent1,parent2,breedOperation,curveChoice):

        outCurves = copy.deepcopy(parent1)
        print outCurves

        if curveChoice == "Single":
            curveSelection = random.choice(self.symGroups.keys())
            groupSelection = "All"
        elif curveChoice == "Group":
            groupSelection = random.choice(self.strongestShapesTree.keys())
            curveSelection = "All"
        else:
            curveSelection = "All"
            groupSelection = "All"

        for faceGroup, ctlDict in parent1.iteritems():

            if curveChoice == "Group":
                if (faceGroup == groupSelection) and (curveSelection == "All"):
                    print "Swapping Groups: %s" % faceGroup
                    outCurves[faceGroup] = parent2[faceGroup]
            elif curveSelection != "All":

                for ctlName, ctlVal in ctlDict.iteritems():

                    if self.symGroups[curveSelection][0] == ctlName:
                        print "Swapping curve: %s" % ctlName
                        outCurves[faceGroup][ctlName] = parent2[faceGroup][ctlName]
                        outCurves[faceGroup][self.symGroups[curveSelection][1]] = parent2[faceGroup][self.symGroups[curveSelection][1]]
            else:
                for ctlName, ctlVal in ctlDict.iteritems():

                    if breedOperation == "Swap":
                        coinFlip = random.random()
                        if coinFlip < 0.5:
                            print "Swapping All Curves"
                            outCurves[faceGroup][ctlName] = parent2[faceGroup][ctlName]
                            outCurves[faceGroup][self.allSymmetryNames[faceGroup][ctlName]] = parent2[faceGroup][self.allSymmetryNames[faceGroup][ctlName]]

                    else:
                        for keyId, keys in enumerate(ctlVal[0]):

                            print "Averaging curves"

                            outCurves[faceGroup][ctlName][0][keyId] = (keys + parent2[faceGroup][ctlName][0][keyId]) / 2
                            outCurves[faceGroup][ctlName][1][keyId] = (parent1[faceGroup][ctlName][1][keyId] + parent2[faceGroup][ctlName][1][keyId]) / 2
                            outCurves[faceGroup][self.allSymmetryNames[faceGroup][ctlName]][0][keyId] = (keys
                                                                                              + parent2[faceGroup][self.allSymmetryNames[faceGroup][ctlName]][0][keyId]) / 2
                            outCurves[faceGroup][self.allSymmetryNames[faceGroup][ctlName]][1][keyId] = (parent2[faceGroup][ctlName][1][keyId]
                                                                                              + parent2[faceGroup][self.allSymmetryNames[faceGroup][ctlName]][1][keyId]) / 2

        return outCurves

    def modifyCurves(self, bredCurve, curveChoice, operationChoice, sf):
        if curveChoice == "Single":
            curveSelection = random.choice(self.symGroups.keys())
            groupSelection = "All"
        elif curveChoice == "Group":
            groupSelection = random.choice(self.strongestShapesTree.keys())
            curveSelection = "All"
        else:
            curveSelection = "All"
            groupSelection = "All"

        print "Group: %s, Curve: %s" % (groupSelection, curveSelection)
        cmds.optionMenu("controlGroupSourceGroup", edit=True, value = groupSelection)
        cmds.optionMenu("controlGroupSource", edit=True, value=curveSelection)

        if operationChoice == "Resample":
            print sf
            self.resampleCurvesNoise(1, sf)


    def setSampleFaceAs(self, bredCurve, SAMPLE_FACE):

        print "Setting Sample Face:"
        for faceGroup, ctlDict in bredCurve.iteritems():
            outGroup = {}
            for ctlName, ctlVal in ctlDict.iteritems():

                nSId = ctlName.find(':')
                if nSId != -1:
                    print "in"
                    out1 = ctlName[:nSId] + str(SAMPLE_FACE[0]) + ctlName[nSId:]

                else:
                    out1 = (self.OTHER_FACE_IDS + ctlName) % SAMPLE_FACE[0]

                cmds.cutKey(out1, time=(self.minSliderTime+1, self.maxSliderTime-1), option="keys")

                for keyId, keys in enumerate(ctlVal[0]):
                    times = ctlVal[1][keyId]

                    print "Face: %s, Time: %f, Val: %f" % (out1, times, keys)

                    cmds.setKeyframe(out1, t=(times, times), v=keys)












