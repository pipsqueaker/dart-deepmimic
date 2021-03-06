import numpy as np
from math import sin, cos, atan2, sqrt, pi, asin

# Calculates Rotation Matrix given euler angles.
def angular_transform(theta) :

    # Sourced from https://www.learnopencv.com/rotation-matrix-to-euler-angles/

    R_x = np.array([[1,         0,                  0                   ],
                    [0,         cos(theta[0]), -sin(theta[0]) ],
                    [0,         sin(theta[0]), cos(theta[0])  ]
                    ])



    R_y = np.array([[cos(theta[1]),    0,      sin(theta[1])  ],
                    [0,                     1,      0                   ],
                    [-sin(theta[1]),   0,      cos(theta[1])  ]
                    ])

    R_z = np.array([[cos(theta[2]),    -sin(theta[2]),    0],
                    [sin(theta[2]),    cos(theta[2]),     0],
                    [0,                     0,                      1]
                    ])


    R = np.matmul(R_z, np.matmul( R_y, R_x ))

    return R

def get_transform_matrix(theta, translation):

    dimension = len(translation)
    matrix = np.zeros([dimension + 1] * 2)
    matrix[:,dimension] = np.append(translation, [1])
    matrix[:dimension, :dimension] = angular_transform(theta)

    return matrix, np.linalg.inv(matrix)

# Checks if a matrix is a valid rotation matrix.
def isRotationMatrix(R) :
    Rt = np.transpose(R)
    shouldBeIdentity = np.dot(Rt, R)
    I = np.identity(3, dtype = R.dtype)
    n = np.linalg.norm(I - shouldBeIdentity)
    return n < 1e-6


def rotationMatrixToEulerAngles(R) :
    """
    Calculates rotation matrix to euler angles
    The result is the same as MATLAB except the order
    of the euler angles ( x and z are swapped ).
    """

    assert(isRotationMatrix(R))

    sy = sqrt(R[0,0] * R[0,0] +  R[1,0] * R[1,0])

    singular = sy < 1e-6

    if  not singular :
        x = atan2(R[2,1] , R[2,2])
        y = atan2(-R[2,0], sy)
        z = atan2(R[1,0], R[0,0])
    else :
        x = atan2(-R[1,2], R[1,1])
        y = atan2(-R[2,0], sy)
        z = 0

    return np.array([x, y, z])

def to_radians(degrees):
    """
    Takes in a numpy
    """
    return np.multiply(pi / 180, degrees)

def from_radians(radians):
    """
    Takes in a numpy
    """
    return np.multiply(180 / pi, degrees)

def rmatrix_x2v(vector):
    """
    Gives the rotation matrix which will rotate x axis to the given vector
    vector should be a unit 3d vector

    Sourced from https://goo.gl/ZGjFEs
    """
    x, y, z = vector
    theta = -atan2(-1 * z, y)
    alpha = -atan2((z * sin(theta) - y * cos(theta)), x)

    return np.array([[cos(alpha), -1 * sin(alpha) * cos(theta), sin(alpha) * sin(theta)],
                        [sin(alpha), cos(alpha) * cos(theta), -1 * cos(alpha) * sin(theta)],
                        [0, sin(theta), cos(theta)]])

