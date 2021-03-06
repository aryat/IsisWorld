
from pandac.PandaModules import NodePath,Vec3,Vec4,TextureStage,TexGenAttrib
import inspect

class Att_base():
    def __init__(self, fReadOnly, name=None, NodeName=None):
        self.fReadOnly = fReadOnly
        if name == None:
            name = "Value"
        self.name = name
        self.NodeName = NodeName

    def getNodeName(self):
        if self.NodeName == None:
            return self.name
        return self.NodeName

    def setNotifier(self, notifier):
        self.notifier = notifier

    def notify(self):
        if hasattr(self,'notifier') and inspect.isroutine(self.notifier):
            self.notifier(self)

class Att_NumRange(Att_base):
    def __init__(self, fReadOnly, name, fInteger, minv, maxv, default, NodeName):
        Att_base.__init__(self, fReadOnly, name, NodeName)
        self.fInteger = fInteger
        self.minv = minv
        self.maxv = maxv
        self.v = default
        self.default = default

    def fix(self):
        if self.minv != self.maxv:
            self.v = max(self.v, self.minv)
            self.v = min(self.v, self.maxv)

    def update(self, v):
        if self.fReadOnly:
            return
        if self.fInteger:
            v = int(v)
        else:
            v = float(v)
        if self.minv >= self.maxv or (v <= self.maxv and v >= self.minv):
            self.v = v

#        if hasattr(self,'notifier') and inspect.isroutine(self.notifier):
#            self.notifier(self)
        self.notify()

class Att_IntRange(Att_NumRange):
    def __init__(self, fReadOnly, name, minv, maxv, default, NodeName=None):
        Att_NumRange.__init__(self,fReadOnly, name, True, minv, maxv, default,NodeName=NodeName)

class Att_FloatRange(Att_NumRange):
    def __init__(self, fReadOnly, name, minv, maxv, default, precision=2,NodeName=None):
        Att_NumRange.__init__(self,fReadOnly, name, False, minv, maxv, default,NodeName=NodeName)
        self.precision = precision
        
class Att_Vecs(Att_base):
    def __init__(self, fReadOnly, name, l, vec, minv, maxv, precision=2, NodeName=None):
        Att_base.__init__(self, fReadOnly, name, NodeName=NodeName)
        self.l = l
        self.minv = minv
        self.maxv = maxv
        self.fInteger = False
        self.precision = precision
        self.vec = []
        self.default = []
        for i in range(l):
            v = Att_FloatRange(fReadOnly, "%d" % (i+1), minv, maxv, vec[i], precision)
            v.setNotifier(self.update)
            self.vec.append(v)
            self.default.append(vec[i])

    def fix(self):
        for i in range(self.l):
            self.vec[i].fix()

    def setValue(self, v):
        if isinstance(v, Att_Vecs):
            for i in range(self.l):
                self.vec[i].v = v.vec[i].v
        else:
            for i in range(self.l):
                self.vec[i].v = v[i]
        self.fix()

    def update(self, object):
#        if hasattr(self,'notifier') and inspect.isroutine(self.notifier):
#            self.notifier(self)
        self.notify()

    def getListValue(self):
        return self.getValue(True)

    def getValue(self, forcevector=False):
        if not forcevector:
            if self.l == 3:
                return Vec3(self.vec[0].v,self.vec[1].v,self.vec[2].v)
            elif self.l == 4:
                return Vec4(self.vec[0].v,self.vec[1].v,self.vec[2].v,self.vec[3].v)

        ret = []
        for i in range(self.l):
            ret.append(self.vec[i].v)
        return ret
        

def Color2RGB(c):
    return (int(c[0] * 255),int(c[1] * 255),int(c[2] * 255))
def RGB2Color(rgb,alpha=1):
    return Vec4(float(float(rgb[0]) / 255.0),float(rgb[1] / 255.0),float(rgb[2] / 255.0),alpha)

class Att_color(Att_base):
    def __init__(self, fReadOnly, name, color):
        if name == None:
            name = "Color"
        Att_base.__init__(self, fReadOnly, name)
        self.color = color

    def getRGBColor(self):
        return Color2RGB(self.color)

    def getColor(self):
        return self.color

    def setRGBColor(self,rgb):
        if self.fReadOnly:
            return
        self.color = RGB2Color(rgb)
        self.notify()

    def setColor(self,c):
        if self.fReadOnly:
            return
        self.color = c
        self.notify()

class SkyDome1(Att_base):
    def __init__(self, scene, rate=(0.005,0.05),
            texturescale=(10,10),
            scale=(400,400,600), texturefile=None):
        Att_base.__init__(self,False, "Sky Dome 1")
        self.skybox = loader.loadModel("models3/dome2")
        self.skybox.setTwoSided(False)
        self.skybox.setScale(scale[0],scale[1],scale[2])
        self.skybox.setLightOff()
        if texturefile == None:
            texturefile = "textures/clouds.jpg"
        texture = loader.loadTexture(texturefile)
        self.textureStage0 = TextureStage("stage0")
        self.textureStage0.setMode(TextureStage.MReplace)
        self.skybox.setTexture(self.textureStage0,texture,1)
        self.skybox.setTexScale(self.textureStage0, texturescale[0], texturescale[1])

        self.skybox.reparentTo(scene)
        self.rate = rate
        self.textureScale = texturescale

        taskMgr.add(self.shiftTextureTask,"skycloudsshifttask" )

    def shiftTextureTask(self, task):
        offsetx = (task.time * self.rate[0]) % 1.0
        offsety = (task.time * self.rate[1]) % 1.0
        self.skybox.setTexOffset(self.textureStage0, offsetx, offsety)
        return task.cont

    def setRate(self, rate):
        self.rate = rate

    def setTextureScale(self, texturescale):
        self.skybox.setTexScale(self.textureStage0, texturescale[0], texturescale[1])

    def Destroy(self):
        self.skybox.removeNode()
        taskMgr.remove("skycloudsshifttask")

    def setPos(self, v):
        self.skybox.setPos(v)

    def show(self):
        self.skybox.show()

    def hide(self):
        self.skybox.hide()

    def setStandardControl(self):
        self.att_rate_x = Att_FloatRange(False, "Speed X", -1.0, 1.0, self.rate[0], 3)
        self.att_rate_y = Att_FloatRange(False, "Speed Y", -1.0, 1.0, self.rate[1], 3)
        self.att_scale_x = Att_FloatRange(False, "Tex-scale X", 0.01, 100.0, self.textureScale[0], 2)
        self.att_scale_y = Att_FloatRange(False, "Tex-scale Y", 0.01, 100.0, self.textureScale[1], 2)
        self.att_rate_x.setNotifier(self.skyboxratechange)
        self.att_rate_y.setNotifier(self.skyboxratechange)
        self.att_scale_x.setNotifier(self.skyboxscalechange)
        self.att_scale_y.setNotifier(self.skyboxscalechange)

    def skyboxratechange(self, object):
        self.setRate((self.att_rate_x.v, self.att_rate_y.v))

    def skyboxscalechange(self,object):
        self.setTextureScale((self.att_scale_x.v, self.att_scale_y.v))



class SkyDome2(Att_base):
    def __init__(self, scene, rate=Vec4(0.004, 0.002, 0.008, 0.010),
                skycolor=Vec4(0.25, 0.5, 1, 0),
                texturescale=Vec4(1,1,1,1),
                scale=(4000,4000,1000),
                texturefile=None):
        Att_base.__init__(self,False, "Sky Dome 2")
        self.skybox = loader.loadModel("models3/dome2")
        self.skybox.reparentTo(scene)
        self.skybox.setScale(scale[0],scale[1],scale[2])
        self.skybox.setLightOff()

        if texturefile == None:
            texturefile = "textures/clouds_bw.png"
        texture = loader.loadTexture(texturefile)
        self.textureStage0 = TextureStage("stage0")
        self.textureStage0.setMode(TextureStage.MReplace)
        self.skybox.setTexture(self.textureStage0,texture,1)
        #self.skybox.setTexScale(self.textureStage0, texturescale[0], texturescale[1])

        self.rate = rate
        self.textureScale = texturescale
        self.skycolor = skycolor
        self.skybox.setShader( loader.loadShader( 'shaders/skydome2.sha' ) )
        self.setShaderInput()

    def setRate(self, rate):
        self.rate = rate

    def setTextureScale(self, texturescale):
        self.skybox.setTexScale(self.textureStage0, texturescale[0], texturescale[1])

    def Destroy(self):
        self.skybox.clearShader()
        self.skybox.removeNode()

    def setPos(self, v):
        self.skybox.setPos(v)

    def show(self):
        self.skybox.show()

    def hide(self):
        self.skybox.hide()

    def setStandardControl(self):
        self.att_rate = Att_Vecs(False,"Cloud Speed",4,self.rate,-1,1,3)
        self.att_scale = Att_Vecs(False, "Tex-scale", 4, self.textureScale, 0.01, 100.0, 2)
        self.att_skycolor = Att_color(False, "Sky Color", self.skycolor)
        self.att_rate.setNotifier(self.changeParams)
        self.att_scale.setNotifier(self.changeParams)
        self.att_skycolor.setNotifier(self.changeParams)

    def changeParams(self, object):
        self.rate = self.att_rate.getValue()
        self.skycolor = self.att_skycolor.getColor()
        self.textureScale = self.att_scale.getValue()
        self.setShaderInput()

    #def skyboxscalechange(self,object):
    #    self.setTextureScale(self.att_scale.getValue())

    def setShaderInput(self):
        self.skybox.setShaderInput("sky", self.skycolor)
        self.skybox.setShaderInput("clouds", self.rate)
        self.skybox.setShaderInput("ts", self.textureScale)
