from dataclasses import dataclass, field
from enum import Enum
import re

@dataclass
class InfoEntry:
    lineno: int
    text: str

CalibrateDirection = Enum("CalibrateDirection", "West East Backlash North South")

@dataclass
class CalibrateStep:
    lineno: int
    direction: CalibrateDirection
    step: int
    dx: float
    dy: float
    x: float
    y: float
    dist: float

@dataclass
class CalibrateResult:
    direction: CalibrateDirection
    angle: float
    rate: float
    parity: str

@dataclass
class CalibrateSection:
    lineno: int
    date: str
    time: str
    profile: str = ''
    dither: str = ''
    ditherScale: float = 0.0
    pixelScale: float = 0.0
    binning: int = 0
    focalLength: int = 0
    searchRegion: int = 0
    massTolerance: float = 0.0
    mode: str = ''
    listSize: int = 0
    camera: str = ''
    gain: int = 0
    frameSize: tuple[int, int] = (0, 0)
    darks: str = ''
    darkDur: int = 0
    defectMap: str = ''
    pixelSize: float = 0.0
    exposure: int = 0
    mount: str = ''
    calStep: int = 0
    calDistance: int = 0
    assumeOrthogonal: str = ''
    raSpeed: float = 0.0
    decSpeed: float = 0.0
    ra: float = 0.0
    dec: float = 0.0
    ha: float = 0.0
    pierSide: str = ''
    rotator: str = ''
    alt: float = 0.0
    az: float = 0.0
    lockPosition: tuple[float, float] = (0.0, 0.0)
    starPosition: tuple[float, float] = (0.0, 0.0)
    hfd: float = 0.0
    steps: list[CalibrateStep] = field(default_factory=list)
    results: list[CalibrateResult] = field(default_factory=list)
    infos: list[InfoEntry] = field(default_factory=list)


@dataclass
class GuideStep:
    lineno: int
    frame: int
    time: float
    mount: str
    dx: float
    dy: float
    raraw: float
    decraw: float
    raguide: float
    decguide: float
    radur: int
    raDir: str
    decdur: int
    decDir: str
    xstep: int
    ystep: int
    starMass: int
    snr: float
    err: int

@dataclass
class GuideSection:
    lineno: int
    date: str
    time: str
    profile: str = ''
    dither: str = ''
    ditherScale: float = 0.0
    pixelScale: float = 0.0
    binning: int = 0
    focalLength: int = 0
    searchRegion: int = 0
    massTolerance: float = 0.0
    mode: str = ''
    listSize: int = 0
    camera: str = ''
    gain: int = 0
    frameSize: tuple[int, int] = (0, 0)
    darks: str = ''
    darkDur: int = 0
    defectMap: str = ''
    pixelSize: float = 0.0
    exposure: int = 0
    mount: str = ''
    mountStatus: str = ''
    guidingStatus: str = ''
    xAngle: float = 0.0
    xRate: float = 0.0
    yAngle: float = 0.0
    yRate: float = 0.0
    parity: str = ''
    normRA: float = 0.0
    normRADec: float = 0.0
    normDec: float = 0.0
    orthoErr: float = 0.0
    xAlgorithm: str = ''
    yAlgorithm: str = ''
    backlashComp: str = ''
    pulse: int = 0
    raMaxDur: int = 0
    decMaxDur: int = 0
    decMode: str = ''
    raSpeed: float = 0.0
    decSpeed: float = 0.0
    calDec: float = 0.0
    ra: float = 0.0
    dec: float = 0.0
    ha: float = 0.0
    pierSide: str = ''
    rotator: str = ''
    alt: float = 0.0
    az: float = 0.0
    lockPosition: tuple[float, float] = (0.0, 0.0)
    starPosition: tuple[float, float] = (0.0, 0.0)
    hfd: float = 0.0
    steps: list[GuideStep] = field(default_factory=list)
    infos: list[InfoEntry] = field(default_factory=list)

@dataclass
class PHDLogFile:
    path: str
    version: str = ''
    sections: list[CalibrateSection | GuideSection] = field(default_factory=list)
    infos: list[InfoEntry] = field(default_factory=list)

    def __post_init__(self):

        State = Enum("State", "VERSION SECTION CALIBRATE CALIBRATE_STEPS GUIDE GUIDE_STEPS")
        state = State.VERSION

        reVersion = re.compile(r"PHD2 version (?P<maj>\d+)\.(?P<min>\d+)\.(?P<rel>\d+) (?P<str>.*),.*")
        reInfo = re.compile(r"INFO: (?P<text>.*)")
        reCalBegin = re.compile(r"Calibration Begins at (?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2})")
        reCalProfile = re.compile(r"Equipment Profile = (?P<profile>.*)")
        reCalDither = re.compile(r"Dither = (?P<dither>[^,]*), Dither scale = (?P<ditherScale>[^,]*),*")
        reCalPixel = re.compile(r"Pixel scale = (?P<pixelScale>\d*\.\d*) arc-sec/px, Binning = (?P<binning>\d), Focal length = (?P<focalLength>\d+) mm")
        reCalSearch = re.compile(r"Search region = (?P<searchRegion>\d*) px, Star mass tolerance = (?P<massTolerance>\d*\.\d*)%, (?P<mode>[^,]*), list size = (?P<listSize>\d*)")
        reCalCamera = re.compile(r" Camera = (?P<camera>[^,]*), gain = (?P<gain>\d*), full size = (?P<frameWidth>\d*) x (?P<frameHeight>\d*), (?P<darks>[^,]*), dark dur = (?P<darkDur>\d*), (?P<defectMap>[^,]*), pixel size = (?P<pixelSize>\d*\.\d*) um")
        reCalExposure = re.compile(r"Exposure = (?P<exposure>\d*) ms")
        reCalMount = re.compile(r"Mount = (?P<mount>[^,]*), Calibration Step = (?P<calStep>\d*) ms, Calibration Distance = (?P<calDistance>\d*) px, Assume orthogonal axes = (?P<assumeOrthogonal>.*)")
        reCalRates = re.compile(r"RA Guide Speed = (?P<raSpeed>\d*\.\d*) a-s/s, Dec Guide Speed = (?P<decSpeed>\d*\.\d*) a-s/s")
        reCalPosition = re.compile(r"RA = (?P<ra>\d*\.\d*) hr, Dec = (?P<dec>[-+]?\d*\.\d*) deg, Hour angle = (?P<ha>[-+]?\d*\.\d*) hr, Pier side = (?P<pierSide>[^,]*), Rotator pos = (?P<rotator>[^,]*), Alt = (?P<alt>\d*\.\d*) deg, Az = (?P<az>\d*\.\d*) deg")
        reCalLock = re.compile(r"Lock position = (?P<lockx>\d*\.\d*), (?P<locky>\d*\.\d*), Star position = (?P<starx>\d*\.\d*), (?P<stary>\d*\.\d*), HFD = (?P<hfd>\d*\.\d*) px")
        reCalStepHeader = re.compile(r"Direction,Step,dx,dy,x,y,Dist")
        reCalStep = re.compile(r"(?P<direction>[^,]*),(?P<step>\d*),(?P<dx>[-+]?\d*\.\d*),(?P<dy>[-+]?\d*\.\d*),(?P<x>[-+]?\d*\.\d*),(?P<y>[-+]?\d*\.\d*),(?P<dist>[-+]?\d*\.\d*)")
        reCalResult = re.compile(r"(?P<direction>\w*) calibration complete\. Angle = (?P<angle>[-+]?\d*\.\d*) deg, Rate = (?P<rate>\d*\.\d*) px/sec, Parity = (?P<parity>\w*)")
        reCalComplete = re.compile(r"Calibration complete, mount = (?P<mount>.*)")
        reGuideBegin = re.compile(r"Guiding Begins at (?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2})")
        reGuideProfile = re.compile(r"Equipment Profile = (?P<profile>.*)")
        reGuideDither = re.compile(r"Dither = (?P<dither>[^,]*), Dither scale = (?P<ditherScale>[^,]*),*")
        reGuidePixel = re.compile(r"Pixel scale = (?P<pixelScale>\d*\.\d*) arc-sec/px, Binning = (?P<binning>\d), Focal length = (?P<focalLength>\d+) mm")
        reGuideSearch = re.compile(r"Search region = (?P<searchRegion>\d*) px, Star mass tolerance = (?P<massTolerance>\d*\.\d*)%, (?P<mode>[^,]*), list size = (?P<listSize>\d*)")
        reGuideCamera = re.compile(r" Camera = (?P<camera>[^,]*), gain = (?P<gain>\d*), full size = (?P<frameWidth>\d*) x (?P<frameHeight>\d*), (?P<darks>[^,]*), dark dur = (?P<darkDur>\d*), (?P<defectMap>[^,]*), pixel size = (?P<pixelSize>\d*\.\d*) um")
        reGuideExposure = re.compile(r"Exposure = (?P<exposure>\d*) ms")
        reGuideMount = re.compile(r"Mount = (?P<mount>[^,]*), (?P<mountStatus>[^,]*), (?P<guideStatus>[^,]*), xAngle = (?P<xAngle>[-+]?\d*\.\d*), xRate = (?P<xRate>\d*\.\d*), yAngle = (?P<yAngle>[-+]?\d*\.\d*), yRate = (?P<yRate>\d*\.\d*), parity = (?P<parity>\w*)")
        reGuideNormRates = re.compile(r'Norm rates RA = (?P<normRA>\d*\.\d*)"/s @ dec (?P<normRADec>\d*), Dec = (?P<normDec>\d*\.\d*)"/s; ortho\.err\. = (?P<orthoErr>\d*\.\d*) deg')
        reGuideLock = re.compile(r"Lock position = (?P<lockx>\d*\.\d*), (?P<locky>\d*\.\d*), Star position = (?P<starx>\d*\.\d*), (?P<stary>\d*\.\d*), HFD = (?P<hfd>\d*\.\d*) px")
        reGuideXAlgorithm = re.compile(r"X guide algorithm = (?P<xalgorithm>.*)")
        reGuideYAlgorithm = re.compile(r"Y guide algorithm = (?P<yalgorithm>.*)")
        reGuideBacklash = re.compile(r"Backlash comp = (?P<backlashComp>[^,]*), pulse = (?P<pulse>\d*) ms")
        reGuideMaxDuration = re.compile(r"Max RA duration = (?P<raMaxDur>\d*), Max DEC duration = (?P<decMaxDur>\d*), DEC guide mode = (?P<decMode>.*)")
        reGuideSpeed = re.compile(r"RA Guide Speed = (?P<raSpeed>\d*\.\d*) a-s/s, Dec Guide Speed = (?P<decSpeed>\d*\.\d*) a-s/s, Cal Dec = (?P<calDec>[-+]?\d*\.\d*)")
        reGuideStepHeader = re.compile(r"Frame,Time,mount,dx,dy,RARawDistance,DECRawDistance,RAGuideDistance,DECGuideDistance,RADuration,RADirection,DECDuration,DECDirection,XStep,YStep,StarMass,SNR,ErrorCode")
        reGuidePosition = re.compile(r"RA = (?P<ra>\d*\.\d*) hr, Dec = (?P<dec>[-+]?\d*\.\d*) deg, Hour angle = (?P<ha>[-+]?\d*\.\d*) hr, Pier side = (?P<pierSide>[^,]*), Rotator pos = (?P<rotator>[^,]*), Alt = (?P<alt>\d*\.\d*) deg, Az = (?P<az>\d*\.\d*) deg")
        reGuideStep = re.compile(r"(?P<frame>\d*),(?P<time>\d*\.\d*),(?P<mount>\".*\"),(?P<dx>[-+]?\d*(\.\d*)?),(?P<dy>[-+]?\d*(\.\d*)?),(?P<raraw>[-+]?\d*(\.\d*)?),(?P<decraw>[-+]?\d*(\.\d*)?),(?P<raguide>[-+]?\d*(\.\d*)?),(?P<decguide>[-+]?\d*(\.\d*)?),(?P<radur>\d*),(?P<radir>[^,]*),(?P<decdur>\d*),(?P<decdir>[^,]*),(?P<xstep>\d*),(?P<ystep>\d*),(?P<starMass>\d*),(?P<snr>\d*\.\d*),(?P<err>\d*)")
        reGuideEnd = re.compile(r"Guiding Ends at (?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2})")

        with open(self.path, "r") as f:
            lineno = 0
            section = None
            for line in f:

                # bump line index
                lineno += 1

                # Skip empty lines
                if len(line.strip()) == 0:
                    continue

                # Simple state machine controls types of record allowed
                if state == State.VERSION:
                    m = reVersion.match(line)
                    if m:
                        self.version = f"{m.group('maj')}.{m.group('min')}.{m.group('rel')} {m.group('str')}"
                        state = State.SECTION
                        continue

                elif state == State.SECTION:
                    m = reCalBegin.match(line)
                    if m:
                        section = CalibrateSection(lineno, m.group('date'), m.group('time'))
                        state = State.CALIBRATE
                        continue
                    m = reGuideBegin.match(line)
                    if m:
                        section = GuideSection(lineno, m.group('date'), m.group('time'))
                        state = State.GUIDE
                        continue
                    m = reInfo.match(line)
                    if m:
                        self.infos.append(InfoEntry(lineno, m.group('text')))
                        continue

                elif state == State.CALIBRATE:
                    m = reCalProfile.match(line)
                    if m:
                        section.profile = m.group('profile')
                        continue
                    m = reCalDither.match(line)
                    if m:
                        section.dither = m.group('dither')
                        section.ditherScale = float(m.group('ditherScale'))
                        continue
                    m = reCalPixel.match(line)
                    if m:
                        section.pixelScale = float(m.group('pixelScale'))
                        section.binning = int(m.group('binning'))
                        section.focalLength = int(m.group('focalLength'))
                        continue
                    m = reCalSearch.match(line)
                    if m:
                        section.searchRegion = int(m.group('searchRegion'))
                        section.massTolerance = float(m.group('massTolerance'))
                        section.mode = m.group('mode')
                        section.listSize = int(m.group('listSize'))
                        continue
                    m = reCalCamera.match(line)
                    if m:
                        section.camera = m.group('camera')
                        section.gain = int(m.group('gain'))
                        section.frameSize = (int(m.group('frameWidth')), int(m.group('frameHeight')))
                        section.darks = m.group('darks')
                        section.darkDur = int(m.group('darkDur'))
                        section.defectMap = m.group('defectMap')
                        section.pixelSize = float(m.group('pixelSize'))
                        continue
                    m = reCalExposure.match(line)
                    if m:
                        section.exposure = int(m.group('exposure'))
                        continue
                    m = reCalMount.match(line)
                    if m:
                        section.mount = m.group('mount')
                        section.calStep = int(m.group('calStep'))
                        section.calDistance = int(m.group('calDistance'))
                        section.assumeOrthogonal = m.group('assumeOrthogonal')
                        continue
                    m = reCalRates.match(line)
                    if m:
                        section.raSpeed = float(m.group('raSpeed'))
                        section.decSpeed = float(m.group('decSpeed'))
                        continue
                    m = reCalPosition.match(line)
                    if m:
                        section.ra = float(m.group('ra'))
                        section.dec = float(m.group('dec'))
                        section.ha = float(m.group('ha'))
                        section.pierSide = m.group('pierSide')
                        section.rotator = m.group('rotator')
                        section.alt = float(m.group('alt'))
                        section.az = float(m.group('az'))
                        continue
                    m = reCalLock.match(line)
                    if m:
                        section.lockPosition = (float(m.group('lockx')), float(m.group('locky')))
                        section.starPosition = (float(m.group('starx')), float(m.group('stary')))
                        section.hfd = float(m.group('hfd'))
                        continue
                    m = reCalStepHeader.match(line)
                    if m:
                        state = State.CALIBRATE_STEPS
                        continue
                
                elif state == State.CALIBRATE_STEPS:
                    m = reCalStep.match(line)
                    if m:
                        step = CalibrateStep(
                            lineno,
                            CalibrateDirection[m.group('direction')],
                            int(m.group('step')),
                            float(m.group('dx')),
                            float(m.group('dy')),
                            float(m.group('x')),
                            float(m.group('y')),
                            float(m.group('dist'))
                        )
                        section.steps.append(step)
                        continue
                    m = reCalResult.match(line)
                    if m:
                        result = CalibrateResult(
                            direction=CalibrateDirection[m.group('direction')],
                            angle=float(m.group('angle')),
                            rate=float(m.group('rate')),
                            parity=m.group('parity')
                        )
                        section.results.append(result)
                        continue
                    m = reInfo.match(line)
                    if m:
                        section.infos.append(InfoEntry(lineno, m.group('text')))
                        continue
                    m = reCalComplete.match(line)
                    if m:
                        self.sections.append(section)
                        section = None
                        state = State.SECTION
                        continue

                elif state == State.GUIDE:
                    m = reGuideProfile.match(line)
                    if m:
                        section.profile = m.group('profile')
                        continue
                    m = reGuideDither.match(line)
                    if m:
                        section.dither = m.group('dither')
                        section.ditherScale = float(m.group('ditherScale'))
                        continue
                    m = reGuidePixel.match(line)
                    if m:
                        section.pixelScale = float(m.group('pixelScale'))
                        section.binning = int(m.group('binning'))
                        section.focalLength = int(m.group('focalLength'))
                        continue
                    m = reGuideSearch.match(line)
                    if m:
                        section.searchRegion = int(m.group('searchRegion'))
                        section.massTolerance = float(m.group('massTolerance'))
                        section.mode = m.group('mode')
                        section.listSize = int(m.group('listSize'))
                        continue
                    m = reGuideCamera.match(line)
                    if m:
                        section.camera = m.group('camera')
                        section.gain = int(m.group('gain'))
                        section.frameSize = (int(m.group('frameWidth')), int(m.group('frameHeight')))
                        section.darks = m.group('darks')
                        section.darkDur = int(m.group('darkDur'))
                        section.defectMap = m.group('defectMap')
                        section.pixelSize = float(m.group('pixelSize'))
                        continue
                    m = reGuideExposure.match(line)
                    if m:
                        section.exposure = int(m.group('exposure'))
                        continue
                    m = reGuideMount.match(line)
                    if m:
                        section.mount = m.group('mount')
                        section.mountStatus = m.group('mountStatus')
                        section.guidingStatus = m.group('guideStatus')
                        section.xAngle = float(m.group('xAngle'))
                        section.xRate = float(m.group('xRate'))
                        section.yAngle = float(m.group('yAngle'))
                        section.yRate = float(m.group('yRate'))
                        section.parity = m.group('parity')
                        continue
                    m = reGuideNormRates.match(line)
                    if m:
                        section.normRA = float(m.group('normRA'))
                        section.normRADec = float(m.group('normRADec'))
                        section.normDec = float(m.group('normDec'))
                        continue
                    m = reGuidePosition.match(line)
                    if m:
                        section.ra = float(m.group('ra'))
                        section.dec = float(m.group('dec'))
                        section.ha = float(m.group('ha'))
                        section.pierSide = m.group('pierSide')
                        section.rotator = m.group('rotator')
                        section.alt = float(m.group('alt'))
                        section.az = float(m.group('az'))
                        continue
                    m = reGuideLock.match(line)
                    if m:
                        section.lockPosition = (float(m.group('lockx')), float(m.group('locky')))
                        section.starPosition = (float(m.group('starx')), float(m.group('stary')))
                        section.hfd = float(m.group('hfd'))
                        continue
                    m = reGuideXAlgorithm.match(line)
                    if m:
                        section.xAlgorithm = m.group('xalgorithm')
                        continue
                    m = reGuideYAlgorithm.match(line)
                    if m:
                        section.yAlgorithm = m.group('yalgorithm')
                        continue
                    m = reGuideBacklash.match(line)
                    if m:
                        section.backlashComp = m.group('backlashComp')
                        section.pulse = int(m.group('pulse'))
                        continue
                    m = reGuideMaxDuration.match(line)
                    if m:   
                        section.raMaxDur = int(m.group('raMaxDur'))
                        section.decMaxDur = int(m.group('decMaxDur'))
                        section.decMode = m.group('decMode')
                        continue
                    m = reGuideSpeed.match(line)
                    if m:
                        section.raSpeed = float(m.group('raSpeed'))
                        section.decSpeed = float(m.group('decSpeed'))
                        section.calDec = float(m.group('calDec'))
                        continue
                    m = reGuideStepHeader.match(line)
                    if m:
                        state = State.GUIDE_STEPS
                        continue
                
                elif state == State.GUIDE_STEPS:
                    m = reGuideStep.match(line)
                    if m:
                        step = GuideStep(
                            lineno,
                            int(m.group('frame')),
                            float(m.group('time')),
                            m.group('mount'),
                            float(m.group('dx')) if len(m.group('dx')) > 0 else 0.0,
                            float(m.group('dy')) if len(m.group('dy')) > 0 else 0.0,
                            float(m.group('raraw')) if len(m.group('raraw')) > 0 else 0.0,
                            float(m.group('decraw')) if len(m.group('decraw')) > 0 else 0.0,
                            float(m.group('raguide')) if len(m.group('raguide')) > 0 else 0.0,
                            float(m.group('decguide')) if len(m.group('decguide')) > 0 else 0.0,
                            int(m.group('radur')) if len(m.group('radur')) > 0 else 0,
                            m.group('radir'),
                            int(m.group('decdur')) if len(m.group('decdur')) > 0 else 0,
                            m.group('decdir'),
                            (int(m.group('xstep')) if len(m.group('xstep')) > 0 else 0),
                            (int(m.group('ystep')) if len(m.group('ystep')) > 0 else 0),
                            int(m.group('starMass')),
                            float(m.group('snr')),
                            int(m.group('err'))
                        )
                        section.steps.append(step)
                        continue
                    m = reInfo.match(line)
                    if m:
                        section.infos.append(InfoEntry(lineno, m.group('text')))
                        continue
                    m = reGuideEnd.match(line)
                    if m:
                        self.sections.append(section)
                        section = None
                        state = State.SECTION
                        continue

                print(f"Line {lineno}: Unmatched line in state {state.name}: {line.strip()}")