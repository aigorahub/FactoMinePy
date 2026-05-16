# HCPC

```{eval-rst}
.. autofunction:: factominer.hcpc.HCPC
```

Hierarchical clustering on the principal components of a PCA / CA / MCA result.
Uses scipy's Ward linkage. When `nb_clust=-1`, picks the cut with the largest
relative loss in within-cluster inertia between consecutive merges. With
`consol=True`, runs a k-means consolidation pass seeded by the hierarchical
centroids.

The returned `HCPCResult` exposes:

- `data_clust`: the input coordinates plus a `clust` column (1-based labels).
- `desc_axes`: per-cluster v-test of each axis (showing axes that
  significantly characterize each cluster).
- `desc_ind`: per-cluster paragons (closest to centroid) and distances.
- `call`: the underlying linkage matrix in `call["t"]["linkage"]`.
