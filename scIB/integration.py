#!/bin/env python

### D. C. Strobl, M. Müller; 2019-07-23

""" This module provides a toolkit for running a large range of single cell data integration methods
    as well as tools and metrics to benchmark them.
"""

import scanpy as sc
import numpy as np
from utils import *

# functions for running the methods

def runScanorama(adata, batch, hvg = None):
    import scanorama
    checkSanity(adata, batch, hvg)
    split = splitBatches(adata.copy(), batch)
    emb, corrected = scanorama.correct_scanpy(split, return_dimred=True)
    corrected = corrected[0].concatenate(corrected[1:])
    emb = np.concatenate(emb, axis=0)

    return emb, corrected

def runScGen(adata, cell_type='louvain', batch='method', model_path='./models/batch', epochs=100, hvg=None):
    checkSanity(adata, batch, hvg)
    import scgen
    
    if 'cell_type' not in adata.obs:
        adata.obs['cell_type'] = adata.obs[cell_type].copy()
    if 'batch' not in adata.obs:
        adata.obs['batch'] = adata.obs[batch].copy()
    
    # TODO: reduce data
    if hvg:
        adata = adata[:, hvg]
    
    network = scgen.VAEArith(x_dimension= adata.shape[1], model_path=model_path)
    network.train(train_data=adata, n_epochs=epochs)
    corrected_adata = scgen.batch_removal(network, adata)
    network.sess.close()
    return corrected_adata

def runSeurat(adata, batch="method", hvg=None):
    checkSanity(adata, batch, hvg)
    import_rpy2()
    ro.r('library(Seurat)')
    ro.r('library(scater)')
    
    ro.globalenv['adata'] = adata
    ro.r('sobj = as.Seurat(adata, counts = "counts", data = "X")')
    ro.r(f'batch_list = SplitObject(sobj, split.by = {batch})')
    ro.r('anchors = FindIntegrationAnchors('+
        'object.list = batch_list, '+
        'anchor.features = 2000,'+
        'scale = T,'+
        'l2.norm = T,'+
        'dims = 1:30,'+
        'k.anchor = 5,'+
        'k.filter = 200,'+
        'k.score = 30,'+
        'max.features = 200,'+
        'eps = 0)'
    )
    ro.r('integrated = IntegrateData('+
        'anchorset = anchors,'+
        'new.assay.name = "integrated",'+
        'features = NULL,'+
        'features.to.integrate = NULL,'+
        'dims = 1:30,'+
        'k.weight = 100,'+
        'weight.reduction = NULL,'+
        'sd.weight = 1,'+
        'sample.tree = NULL,'+
        'preserve.order = F,'+
        'do.cpp = T,'+
        'eps = 0,'+
        'verbose = T)'
    )
    return ro.r('as.SingleCellExperiment(integrated)')

def runHarmony(adata, batch, hvg = None):
    checkSanity(adata, batch, hvg)
    import_rpy2()
    ro.r('library(harmony)')

    pca = sc.pp.pca(adata, svd_solver='arpack', copy=True).obsm['X_pca']
    method = adata.obs[batch]

    ro.globalenv['pca'] = pca
    ro.globalenv['method'] = method

    ro.r(f'harmonyEmb <- HarmonyMatrix(pca, method, "{batch}", do_pca= F)')

    return ro.r('harmonyEmb')

def runMNN(adata, batch, hvg = None):
    import mnnpy
    checkSanity(adata, batch, hvg)
    split = splitBatches(adata, batch)

    corrected = mnnpy.mnn_correct(*split, var_subset=hvg)

    return corrected[0]

def runBBKNN(adata, batch, hvg=None):
    import bbknn
    checkSanity(adata, batch, hvg)
    sc.pp.pca(adata, svd_solver='arpack')
    corrected = bbknn.bbknn(adata, batch_key=batch, copy=True)
    return corrected


if __name__=="__main__":
    adata = sc.read('testing.h5ad')
    #emb, corrected = runScanorama(adata, 'method', False)
    #print(emb)
    #print(corrected)


        

