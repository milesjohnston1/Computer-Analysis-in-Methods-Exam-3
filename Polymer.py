#region imports
import math
import random as rnd
from datetime import datetime
from copy import deepcopy as dc
#endregion

#region class definitions
class Position():
    """
    by Jim Smay, last edit: 04/27/2022
    I made this position for holding a position in 3D space (i.e., a point).  I've given it some ability to do
    vector arithmitic and vector algebra (i.e., a dot product).  I could have used a numpy array, but I wanted
    to create my own.  This class uses operator overloading as explained in the class.
    """
    def __init__(self, pos=None, x=None, y=None, z=None):
        """
        x, y, and z have the expected meanings
        :param pos: a tuple (x,y,z)
        :param x: float
        :param y: float
        :param z: float
        """
        # set default values
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        # unpack position from a tuple if given
        if pos is not None:
            self.x, self.y, self.z = pos
        # override the x,y,z defaults if they are given as arguments
        self.x = x if x is not None else self.x
        self.y = y if y is not None else self.y
        self.z = z if z is not None else self.z

    # region operator overloads $NEW$ 4/7/21
    # this is overloading the addition operator.  Allows me to add Position objects with simple math: c=a+b, where
    # a, b, and c are all position objects.
    def __add__(self, other):
        return Position((self.x + other.x, self.y + other.y, self.z + other.z))

    # this overloads the iterative add operator
    def __iadd__(self, other):
        if other in (float, int):
            self.x += other
            self.y += other
            self.z += other
            return self
        if type(other) == Position:
            self.x += other.x
            self.y += other.y
            self.z += other.z
            return self

    # this is overloading the subtract operator.  Allows me to subtract Positions. (i.e., c=b-a)
    def __sub__(self, other):
        return Position((self.x - other.x, self.y - other.y, self.z - other.z))

    # this overloads the iterative subtraction operator
    def __isub__(self, other):
        if type(other) in (float, int):
            self.x -= other
            self.y -= other
            self.z -= other
            return self
        if type(other) == Position:
            self.x -= other.x
            self.y -= other.y
            self.z -= other.z
            return self

    # this is overloading the multiply operator.  Allows me to multiply a scalar or do a dot product (i.e., b=s*a or c=b*a)
    def __mul__(self, other):
        if type(other) in (float, int):
            return Position((self.x * other, self.y * other, self.z * other))
        if type(other) is Position:
            return Position((self.x * other.x, self.y * other.y, self.z * other.z))

    # this is overloading the __rmul__ operator so that s*Pt works.
    def __rmul__(self, other):
        return self * other

    # this is overloading the *= operator.  Same as a = Position((a.x*other, a.y*other, a.z*other))
    def __imul__(self, other):
        if type(other) in (float, int):
            self.x *= other
            self.y *= other
            self.z *= other
            return self

    # this is overloading the division operator.  Allows me to divide by a scalar (i.e., b=a/s)
    def __truediv__(self, other):
        if type(other) in (float, int):
            return Position((self.x / other, self.y / other, self.z / other))

    # this is overloading the /= operator.  Same as a = Position((a.x/other, a.y/other, a.z/other))
    def __idiv__(self, other):
        if type(other) in (float, int):
            self.x /= other
            self.y /= other
            self.z /= other
            return self

    def __round__(self, n=None):
        if n is not None:
            return Position(x=round(self.x, n), y=round(self.y, n), z=round(self.z, n))
        return self

    # endregion

    def set(self, strXYZ=None, tupXYZ=None, SI=True):
        # set position by string or tuple
        lenCF = 1 if SI else 3.3
        if strXYZ is not None:
            cells = strXYZ.replace('(', '').replace(')', '').strip().split(',')
            x, y, z = float(cells[0]), float(cells[1]), float(cells[2])
            self.x = lenCF*float(x)
            self.y = lenCF*float(y)
            self.z = lenCF*float(z)
        elif tupXYZ is not None:
            x, y, z = tupXYZ  # [0], strXYZ[1],strXYZ[2]
            self.x = lenCF*float(x)
            self.y = lenCF*float(y)
            self.z = lenCF*float(z)

    def getTup(self):  # return (x,y,z) as a tuple
        return (self.x, self.y, self.z)

    def getStr(self, nPlaces=3, SI=True, scientific=False):
        """
        Get a string representation of the position
        :param nPlaces: number of decimal places in formatted string
        :param SI: default is True, otherwise multipy by 3.3
        :param scientific: bool for scientific notation
        :return: a formatted, comma delimited string
        """
        lenCF=1 if SI else 3.3
        fmtStr='{:.'+str(nPlaces)+('e}' if scientific else 'f}')
        return ''+fmtStr.format(self.x*lenCF)+', '+fmtStr.format(self.y*lenCF)+', '+fmtStr.format(self.z*lenCF)+''

    def mag(self):  # normal way to calculate magnitude of a vector
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5

    def normalize(self):  # typical way to normalize to a unit vector
        l = self.mag()
        if l <= 0.0:
            return
        self.__idiv__(l)

    def normalize2D(self):
        self.z = 0.0
        self.normalize()

    def getAngleRad_XYPlane(self):
        """
        Gets angle of position relative to an origin (0,0) in the x-y plane
        :return: angle in x-y plane in radians
        """
        l = self.mag()
        if l <= 0.0:
            return 0
        if self.y >= 0.0:
            return math.acos(self.x / l)
        return 2.0 * math.pi - math.acos(self.x / l)

    def getAngleDeg_XYPlane(self):
        """
        Gets angle of position relative to an origin (0,0) in the x-y plane
        :return: angle in x-y plane in degrees
        """
        return 180.0 / math.pi * self.getAngleRad()

    def midPt(self, p2=None):
        """
        find midpoint between self and p2.
        :param p2: a position
        :return: position in middle between self and p2
        """
        return Position(x=self.x+0.5*(p2.x-self.x), y=self.y+0.5*(p2.y-self.y), z=self.z+0.5*(p2.z-self.z))

    def distTo(self, p2=None):
        """
        Calculates the distance to another position p2
        :param p2:
        :return:
        """
        if p2==None:
            return self.mag()
        return (self-p2).mag()

    def getRndDir(self):
        """
        calculate a unit vector in a random direction.
        :return: a unit vector in a random direction as Position()
        """
        rnd.seed(datetime.now().second)
        d=Position(x=rnd.random(), y=rnd.random(), z=rnd.random())
        d-=0.5
        d.normalize()
        return d

    def getRndPosOnSphere(self, radius=1.0):
        """
        Calculates a random place on the sphere surrounding self at a radius as given.
        :param radius:
        :return: a random position radius away from self.
        """
        rndVec=radius*self.getRndDir()
        return self+rndVec
class molecule():
    def __init__(self, molecularWeight=12, position=Position()):
        """
        For modeling particles.
        :param molecularWeight: in units of Daltons (or g/mol)
        :param position: location of the particle in 3D Space
        """
        self.MW=molecularWeight
        self.position=position

class macroMolecule():
    def __init__(self, degreeOfPolymerization=1000, segmentLength=0.154E-9, merWt=14):
        """
        For modeling polymer molecules.
        :param molecularWeight:  in units of Daltons (or g/mol)
        :param segmentLength:  the average bond length of segments (for CH2-CH2 = 154nm)
        """
        self.merWt = merWt
        self.N = degreeOfPolymerization  #degree of polymerization or number of links
        self.MW = self.N*merWt
        self.segmentLength=segmentLength
        self.centerOfMass = Position()
        self.radiusOfGyration = 0
        self.radiusOfInfluence = 0
        self.endToEndDistance = 0
        self.mers = []  # a list of mers for polyethylene.  Note that first and last mer have one extra hydrogen

    def freelyJointedChainModel(self):
        """
        This function is used to mimic the nature of a polymer molecule by executing the freely jointed chain model.
        Step 1:  pin the initial mer to location 0,0,0
        Step 2:  use Position.getRndDir() to return a random direction from a uniform random distribution of directions.
        Step 3:  place second mer at a distance of segmentLength from position of current location in direction from step 2.
        Step 4:  repeat steps 2&3 for remaining links
        Step 5:  calculate center of mass, radius of gyration, end to end distance
        :return:
        """
        #Step 1:
        lastPosition=Position(x=0,y=0,z=0)
        self.mers=[]
        #Steps 2,3,4
        M=int(self.N)
        for n in range(M):
            m=molecule(molecularWeight=self.merWt)
            m.MW += 1 if (n==0 or n==(self.N-1)) else 0
            m.position = lastPosition.getRndPosOnSphere(self.segmentLength)
            self.mers.append(m)
            lastPosition=m.position

        #Step 5
        for m in self.mers:
            self.centerOfMass+=m.MW*m.position
        self.centerOfMass/=self.MW
        self.endToEndDistance = (self.mers[0].position-self.mers[-1].position).mag()
        self.radiusOfGyration=(sum([mer.MW*(mer.position.distTo(self.centerOfMass)) for mer in self.mers])/(self.merWt*self.N+2))**0.5
#endregion