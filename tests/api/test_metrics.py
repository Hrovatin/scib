from tests.common import *
import numpy as np
import pandas as pd
import warnings

warnings.filterwarnings('ignore')


def test_silhouette(adata_factory):
    adata = adata_factory(pca=True, n_top_genes=2000)
    score = scIB.me.silhouette(adata, group_key='celltype', embed='X_pca', scale=True)
    LOGGER.info(f"score: {score}")
    assert score >= 0
    assert score <= 1


def test_silhouette_batch(adata_factory):
    adata = adata_factory(pca=True, n_top_genes=2000)
    _, sil = scIB.me.silhouette_batch(adata, batch_key='batch', group_key='celltype',
                                      embed='X_pca', scale=True, verbose=False)
    score = sil['silhouette_score'].mean()
    LOGGER.info(f"score: {score}")
    assert score >= 0
    assert score <= 1


def test_nmi(adata_factory, cluster_factory):
    adata = adata_factory(pca=True, n_top_genes=2000, neighbors=True)

    # trivial score
    score = scIB.me.nmi(adata, 'celltype', 'celltype')
    assert score == 1

    # on cell type 
    _, _, nmi_all = cluster_factory(adata, cluster_key='cluster', label_key='celltype', verbose=True)
    for score in nmi_all['score']:
        LOGGER.info(score)
        assert score >= 0
        assert score <= 1


def test_ari(adata_factory, cluster_factory):
    adata = adata_factory(pca=True, n_top_genes=2000, neighbors=True)

    # trivial score
    score = scIB.me.ari(adata, 'celltype', 'celltype')
    assert score == 1

    # on cell type
    cluster_factory(adata, cluster_key='cluster', label_key='celltype')
    score = scIB.me.ari(adata, group1='cluster', group2='celltype')
    LOGGER.info(f"score: {score}")
    assert score >= 0
    assert score <= 1


def test_pcr_comparison(adata_factory, embed_factory, verbose=True):
    # no PCA precomputed
    adata = adata_factory()
    adata_int = adata.copy()
    score = scIB.me.pcr_comparison(
        adata, adata_int,
        covariate='batch', n_comps=50,
        scale=True, verbose=verbose
    )
    LOGGER.info(f"no PCA precomputed: {score}")
    assert score < 1e-6

    # use different embedding
    adata = adata_factory()
    adata_int = embed_factory(adata, type_='full')
    score = scIB.me.pcr_comparison(
        adata, adata_int,
        covariate='batch',
        embed='X_emb', n_comps=50,
        scale=True, verbose=verbose
    )
    LOGGER.info(f"using embedding: {score}")
    assert score >= 0
    assert score <= 1
    assert score < 1e-6

    # precomputed PCA
    adata = adata_factory(pca=True, n_top_genes=2000)
    adata_int = adata.copy()
    score = scIB.me.pcr_comparison(adata, adata_int, covariate='batch', scale=True, verbose=verbose)
    LOGGER.info(f"precomputed PCA: {score}")
    assert score == 0  # same PCA values -> difference should be 0


def test_cell_cycle(adata_factory):
    adata = adata_factory()
    adata_int = adata.copy()

    # only final score implementation
    score = scIB.me.cell_cycle(adata, adata_int, batch_key='batch', organism='mouse',
                          agg_func=np.mean, verbose=True)
    print(f"score: {score}")
    assert score == 1

    # get all intermediate scores
    scores_df = scIB.me.cell_cycle(adata, adata_int, batch_key='batch', organism='mouse',
                              agg_func=None, verbose=True)
    LOGGER.info(f"score: {scores_df}")
    assert isinstance(scores_df, pd.DataFrame)
    for i in scores_df['score']:
        assert i == 1


def test_hvg_overlap(adata_factory):
    adata = adata_factory()
    adata_int = adata.copy()
    score = scIB.me.hvg_overlap(adata_int, adata, batch='batch', n_hvg=500)
    LOGGER.info(f"score: {score}")
    assert score == 1


def test_isolated_labels(adata_factory):
    adata = adata_factory(pca=True, n_top_genes=2000, neighbors=True)

    # test 2 different implementations of score
    for impl in [True, False]:
        score = scIB.me.isolated_labels(adata, label_key='celltype',
                                   batch_key='batch', cluster=impl,
                                   n=4, verbose=True)
        LOGGER.info(f"score: {score}")
        assert score <= 1
        assert score >= 0