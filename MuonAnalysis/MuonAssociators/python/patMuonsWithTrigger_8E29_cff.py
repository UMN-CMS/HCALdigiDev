import FWCore.ParameterSet.Config as cms

##    __  __       _          ____   _  _____   __  __                       
##   |  \/  | __ _| | _____  |  _ \ / \|_   _| |  \/  |_   _  ___  _ __  ___ 
##   | |\/| |/ _` | |/ / _ \ | |_) / _ \ | |   | |\/| | | | |/ _ \| '_ \/ __|
##   | |  | | (_| |   <  __/ |  __/ ___ \| |   | |  | | |_| | (_) | | | \__ \
##   |_|  |_|\__,_|_|\_\___| |_| /_/   \_\_|   |_|  |_|\__,_|\___/|_| |_|___/
##                                                                           
##   
### ==== Make PAT Muons ====
import PhysicsTools.PatAlgos.producersLayer1.muonProducer_cfi
patMuonsWithoutTrigger = PhysicsTools.PatAlgos.producersLayer1.muonProducer_cfi.patMuons.clone(
    muonSource = 'muons',
    # embed the tracks, so we don't have to carry them around
    embedTrack          = True,
    embedCombinedMuon   = True,
    embedStandAloneMuon = True,
    # then switch off some features we don't need
    #addTeVRefits = False, ## <<--- this doesn't work. PAT bug ??
    embedPickyMuon = False,
    embedTpfmsMuon = False, 
    userIsolation = cms.PSet(),   # no extra isolation beyond what's in reco::Muon itself
    isoDeposits = cms.PSet(), # no heavy isodeposits
    addGenMatch = False,       # no mc: T&P doesn't take it from here anyway.
)

##    __  __       _       _       ____      ___        __  _     _ 
##   |  \/  | __ _| |_ ___| |__   |  _ \    / \ \      / / | |   / |
##   | |\/| |/ _` | __/ __| '_ \  | |_) |  / _ \ \ /\ / /  | |   | |
##   | |  | | (_| | || (__| | | | |  _ <  / ___ \ V  V /   | |___| |
##   |_|  |_|\__,_|\__\___|_| |_| |_| \_\/_/   \_\_/\_/    |_____|_|
##                                                                  
##   
from MuonAnalysis.MuonAssociators.muonL1Match_cfi import muonL1Match as muonL1Info
muonL1Info.src = "muons"
muonL1Info.matched = "l1extraParticles"
muonL1Info.preselection = ""
muonL1Info.writeExtraInfo = True

## Define a generic function, so that it can be used with existing PAT Muons
def addL1UserData(patMuonProducer, l1ModuleLabel = "muonL1Info"):
    "Load variables inside PAT muon, from module <l1ModuleLabel> that you must run before it"
    patMuonProducer.userData.userInts.src += [
        cms.InputTag(l1ModuleLabel, "quality"), # will be -999 in case of no match
    ]
    patMuonProducer.userData.userFloats.src += [  
        cms.InputTag(l1ModuleLabel, "deltaR"),  # will be 999 in case of no match
    ]
    patMuonProducer.userData.userCands.src += [
        cms.InputTag(l1ModuleLabel)
    ]

## Do it for this collection of pat Muons
addL1UserData(patMuonsWithoutTrigger, "muonL1Info")

##    __  __       _       _       _   _ _   _____ 
##   |  \/  | __ _| |_ ___| |__   | | | | | |_   _|
##   | |\/| |/ _` | __/ __| '_ \  | |_| | |   | |  
##   | |  | | (_| | || (__| | | | |  _  | |___| |  
##   |_|  |_|\__,_|\__\___|_| |_| |_| |_|_____|_|  
##                                                 
##   

### ==== Unpack trigger, and match ====
from PhysicsTools.PatAlgos.triggerLayer1.triggerProducer_cfi import patTrigger
patTrigger.onlyStandAlone = True

### ==== Then perform a match for all HLT triggers of interest
from PhysicsTools.PatAlgos.triggerLayer1.triggerMatcher_cfi import muonTriggerMatchHLTMu3
muonTriggerMatchHLT = cms.EDFilter( "PATTriggerMatcherDRDPtLessByR",
    src     = cms.InputTag( "patMuonsWithoutTrigger" ),
    matched = cms.InputTag( "patTrigger" ),
    andOr          = cms.bool( False ),
    filterIdsEnum  = cms.vstring( '*' ),
    filterIds      = cms.vint32( 0 ),
    filterLabels   = cms.vstring( '*' ),
    pathNames      = cms.vstring( '*' ),
    collectionTags = cms.vstring( '*' ),
    maxDPtRel = cms.double( 0.5 ),
    maxDeltaR = cms.double( 0.5 ),
    resolveAmbiguities    = cms.bool( True ),
    resolveByMatchQuality = cms.bool( False )
)

### == For HLT triggers which are just L1s, we need a different matcher
from MuonAnalysis.MuonAssociators.muonHLTL1Match_cfi import muonHLTL1Match
muonMatchL1 = muonHLTL1Match.clone(
    src     = muonTriggerMatchHLT.src,
    matched = muonTriggerMatchHLT.matched,
    maxDeltaR   = cms.double(0.3),
)

### Single Mu L1
muonMatchHLTL1 = muonMatchL1.clone(collectionTags = [ 'hltL1extraParticles::HLT' ])
muonMatchHLTL2 = muonTriggerMatchHLT.clone(collectionTags = [ 'hltL2MuonCandidates::HLT' ], maxDeltaR = 1.2, maxDPtRel = 10.0) # L2 muons have poor resolution
muonMatchHLTL3 = muonTriggerMatchHLT.clone(collectionTags = [ 'hltL3MuonCandidates::HLT' ], maxDeltaR = 0.5, maxDPtRel = 10.0)
muonMatchHLTCtfTrack  = muonTriggerMatchHLT.clone(collectionTags = ['hltMuTrackJpsiCtfTrackCands::HLT'])

patTriggerMatchers1Mu = cms.Sequence(
      muonMatchHLTL1 +
      muonMatchHLTL2 +
      muonMatchHLTL3 
)
patTriggerMatchers1MuInputTags = [
    cms.InputTag('muonMatchHLTL1','propagatedReco'), # fake, will match if and only if he muon did propagate to station 2
    cms.InputTag('muonMatchHLTL1'),
    cms.InputTag('muonMatchHLTL2'),
    cms.InputTag('muonMatchHLTL3'),
]

patTriggerMatchers2Mu = cms.Sequence(
    muonMatchHLTCtfTrack
)
patTriggerMatchers2MuInputTags = [
    cms.InputTag('muonMatchHLTCtfTrack'),
]

## ==== Embed ====
patMuonsWithTrigger = cms.EDProducer( "PATTriggerMatchMuonEmbedder",
    src     = cms.InputTag(  "patMuonsWithoutTrigger" ),
    matches = cms.VInputTag()
)
patMuonsWithTrigger.matches += patTriggerMatchers1MuInputTags



## ==== Trigger Sequence ====
patTriggerMatching = cms.Sequence(
    patTrigger * 
    patTriggerMatchers1Mu *
    patMuonsWithTrigger
)

patMuonsWithTriggerSequence = cms.Sequence(
    muonL1Info             *
    patMuonsWithoutTrigger *
    patTriggerMatching
)


def changeTriggerProcessName(process, triggerProcessName, oldProcessName="HLT"):
    "Change the process name under which the trigger was run"
    patTrigger.processName = triggerProcessName
    process.muonMatchHLTL1.collectionTags[0] = process.muonMatchHLTL1.collectionTags[0].replace('::'+oldProcessName,'::'+triggerProcessName)
    process.muonMatchHLTL2.collectionTags[0] = process.muonMatchHLTL2.collectionTags[0].replace('::'+oldProcessName,'::'+triggerProcessName)
    process.muonMatchHLTL3.collectionTags[0] = process.muonMatchHLTL3.collectionTags[0].replace('::'+oldProcessName,'::'+triggerProcessName)
    process.muonMatchHLTCtfTrack.collectionTags[0] = process.muonMatchHLTCtfTrack.collectionTags[0].replace('::'+oldProcessName,'::'+triggerProcessName)

def useExistingPATMuons(process, newPatMuonTag, addL1Info=False):
    "Start from existing pat Muons instead of producing them"
    process.patMuonsWithTriggerSequence.remove(process.patMuonsWithoutTrigger)
    process.patMuonsWithTrigger.src = newPatMuonTag
    from PhysicsTools.PatAlgos.tools.helpers import massSearchReplaceParam
    massSearchReplaceParam(process.patMuonsWithTriggerSequence, 'src', cms.InputTag('patMuonsWithTrigger'), newPatMuonTag)
    if addL1Info:
        process.muonL1Info.src = newPatMuonTag.muonSource
        addL1UserData(getattr(process,newPatMuonTag.moduleLabel), 'muonL1Info')

def addPreselection(process, cut):
    "Add a preselection cut to the muons before matching (might be relevant, due to ambiguity resolution in trigger matching!"
    process.patMuonsWithoutTriggerUnfiltered = process.patMuonsWithoutTrigger.clone()
    process.globalReplace('patMuonsWithoutTrigger', cms.EDFilter("PATMuonSelector", src = cms.InputTag('patMuonsWithoutTriggerUnfiltered'), cut = cms.string(cut))) 
    process.patMuonsWithTriggerSequence.replace(process.patMuonsWithoutTrigger, process.patMuonsWithoutTriggerUnfiltered * process.patMuonsWithoutTrigger)

def addMCinfo(process):
    process.load("PhysicsTools.PatAlgos.mcMatchLayer0.muonMatch_cfi")
    process.patMuonsWithTriggerSequence.replace(process.patMuonsWithoutTrigger, process.muonMatch + process.patMuonsWithoutTrigger)
    process.patMuonsWithoutTrigger.addGenMatch = True
    process.patMuonsWithoutTrigger.embedGenMatch = True
    process.patMuonsWithoutTrigger.genParticleMatch = 'muonMatch'

def addDiMuonTriggers(process):
    process.patTriggerMatching.replace(process.patTriggerMatchers1Mu, process.patTriggerMatchers1Mu + process.patTriggerMatchers2Mu)
    process.patMuonsWithTrigger.matches += patTriggerMatchers2MuInputTags
