import CVXcanon
import numpy as np
from  cvxpy.lin_ops.lin_op import *
from pdb import set_trace as bp


def get_sparse_matrix(constrs, id_to_col=None):
    # print constrs
    linOps = [constr.expr for constr in constrs]
    args = CVXcanon.LinOpVector()

    id_to_col_C = CVXcanon.IntIntMap()
    if id_to_col is None:
        id_to_col = {}

    for id, col in id_to_col.items():
        id_to_col_C[id] = col

    # make sure things stay in scope..
    tmp = []
    for lin in linOps:
        tree = build_lin_op_tree(lin, tmp)
        tmp.append(tree)
        args.push_back(tree)

    print "Calling C++ code"
    problemData = CVXcanon.build_matrix(args, id_to_col_C)
    print "Returned from C++ code"

    V, I, J, b = ([], [], [], [])
    for i in range(problemData.V.size()):
        V.append(problemData.V[i])
        I.append(problemData.I[i])
        J.append(problemData.J[i])

    for i in range(problemData.data.size()):
        b.append(problemData.data[i])

    # print V, I, J, b
    return (V, I, J, np.array(b).reshape(-1, 1))


def build_lin_op_tree(linPy, tmp):
    linC = CVXcanon.LinOp()
    # Setting the type of our lin op
    linC.type = eval("CVXcanon." + linPy.type.upper())
    # Loading the data into our array
    if linPy.data is None:
        pass
    elif isinstance(linPy.data, tuple) and isinstance(linPy.data[0], slice):  # Tuple of slices
        for sl in linPy.data:
            vec = CVXcanon.DoubleVector()
            vec.push_back(sl.start)
            vec.push_back(sl.stop)
            if sl.step is None:
                vec.push_back(1.0)
            else:
                vec.push_back(sl.step)
            linC.data.push_back(vec)      
    elif isinstance(linPy.data, float) or isinstance(linPy.data, int):
        vec = CVXcanon.DoubleVector()
        vec.push_back(linPy.data)
        linC.data.push_back(vec)
    elif isinstance(linPy.data, LinOp) and linPy.data.type is 'scalar_const':
        vec = CVXcanon.DoubleVector()
        vec.push_back(linPy.data.data)
        linC.data.push_back(vec)
    elif isinstance(linPy.data, LinOp) and (linPy.data.type is 'sparse_const'
                                            or linPy.data.type is 'dense_const'):

        if linPy.data.type is 'sparse_const':
            data = linPy.data.data.todense()
        else:
            data = linPy.data.data

        rows, cols = data.shape
        for row in xrange(rows):
            vec = CVXcanon.DoubleVector()
            for col in xrange(cols):
                vec.push_back(data[row, col])
            linC.data.push_back(vec)
    else:
        for row in linPy.data:
            vec = CVXcanon.DoubleVector()
            for entry in row:
                vec.push_back(float(entry))
            linC.data.push_back(vec)

    # Setting size
    linC.size.push_back(int(linPy.size[0]))
    linC.size.push_back(int(linPy.size[1]))

    # Updating the arguments
    for argPy in linPy.args:
        tree = build_lin_op_tree(argPy, tmp)
        tmp.append(tree)
        linC.args.push_back(tree)

    return linC