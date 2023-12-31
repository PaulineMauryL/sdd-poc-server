from .models.mwem import MWEM
from .models.dpctgan import DPCTGAN
from .models.mst import MST
from .models.patectgan import PATECTGAN
from fastapi import HTTPException

import globals  

from typing import Dict
import pandas as pd

synth_map = {
    "MWEM": MWEM,
    "DPCTGAN": DPCTGAN,
    "MST": MST,
    "PATECTGAN": PATECTGAN
}
# synth_map = {
#     'mwem': {
#         'class': 'snsynth.mwem.MWEMSynthesizer'
#     },
#     'dpctgan': {
#         'class': 'snsynth.pytorch.nn.dpctgan.DPCTGAN'
#     },
#     'patectgan': {
#         'class': 'snsynth.pytorch.nn.patectgan.PATECTGAN'
#     },
#     'mst': {
#         'class': 'snsynth.mst.mst.MSTSynthesizer'
#     },
#     'pacsynth': {
#         'class': 'snsynth.aggregate_seeded.AggregateSeededSynthesizer'
#     },
#     'dpgan': {
#         'class': 'snsynth.pytorch.nn.dpgan.DPGAN'
#     },
#     'pategan': {
#         'class': 'snsynth.pytorch.nn.pategan.PATEGAN'
#     }
# }
def synth(synth_inp, params: Dict[str, int] = {}):
    sd = synth_map[synth_inp.model](globals.TRAIN, synth_inp.epsilon+2, synth_inp.delta, synth_inp.select_cols, synth_inp.mul_matrix) #epsilon + 2 for databounds
    try:
        res =  sd.export()
    except Exception as excp:
        globals.LOG.exception(excp)
        globals.LOG.error("Error while generating and exporting synthetic data with Input:\n")
        globals.LOG.error(synth_inp)
        raise HTTPException(400, f"Error while generating data: " + str(excp))

    return res