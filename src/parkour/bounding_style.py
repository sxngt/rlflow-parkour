"""Pair-synchronous support incentive, inspired by reference paper Table S4.

This style signal alone does not establish a jump, progress or course success.
"""
def bounding_mask(contact,terminal=None):
    if contact.shape[-1]!=4:raise ValueError('FL FR RL RR contact order required')
    mask=(contact[:,0]==contact[:,1])&(contact[:,2]==contact[:,3])&~contact.all(dim=1)
    return mask if terminal is None else mask&~terminal
