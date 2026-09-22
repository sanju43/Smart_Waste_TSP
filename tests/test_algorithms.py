from algorithms.nearest_neighbor import nearest_neighbor
from algorithms.two_opt import two_opt

def matrix(coords):
    from math import hypot
    return {i:{j:hypot(coords[i][0]-coords[j][0],coords[i][1]-coords[j][1]) for j in coords} for i in coords}

def test_nn_starts_and_ends_at_depot():
    m=matrix({0:(0,0),1:(1,0),2:(1,1),3:(0,1)})
    r=nearest_neighbor([0,1,2,3],m)
    assert r[0]==0 and r[-1]==0 and set(r)=={0,1,2,3}

def test_two_opt_preserves_nodes():
    m=matrix({0:(0,0),1:(1,1),2:(0,1),3:(1,0)})
    r=two_opt([0,1,2,3,0],m)
    assert r[0]==0 and r[-1]==0 and sorted(r)==[0,0,1,2,3]
