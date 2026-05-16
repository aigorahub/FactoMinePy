#!/usr/bin/env Rscript
# Regenerate JSON fixtures from R FactoMineR for the parity tests.
#
# Usage: Rscript tools/refresh_r_fixtures.R
#
# Output: tests/fixtures/r_outputs/<method>/<dataset>.json

suppressPackageStartupMessages({
  library(FactoMineR)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = FALSE)
script_arg <- args[grep("^--file=", args)]
if (length(script_arg) == 1) {
  script_path <- normalizePath(sub("^--file=", "", script_arg))
  root <- normalizePath(file.path(dirname(script_path), ".."))
} else if (!is.null(sys.frame(1)$ofile)) {
  root <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."))
} else {
  root <- normalizePath(getwd())
}
out_dir <- function(method) {
  d <- file.path(root, "tests", "fixtures", "r_outputs", method)
  dir.create(d, recursive = TRUE, showWarnings = FALSE)
  d
}

write_json <- function(obj, path) {
  writeLines(toJSON(obj, digits = 10, auto_unbox = TRUE, pretty = FALSE, na = "string"), path)
}

dump_block <- function(block) {
  if (is.null(block)) return(NULL)
  cap <- function(name) if (!is.null(block[[name]])) as.data.frame(block[[name]]) else NULL
  list(
    coord   = cap("coord"),
    cos2    = cap("cos2"),
    contrib = cap("contrib"),
    cor     = cap("cor"),
    dist    = if (!is.null(block$dist)) as.numeric(block$dist) else NULL,
    inertia = if (!is.null(block$inertia)) as.numeric(block$inertia) else NULL,
    v.test  = cap("v.test"),
    eta2    = cap("eta2")
  )
}

dump_pca <- function(res) {
  list(
    eig     = as.data.frame(res$eig),
    var     = dump_block(res$var),
    ind     = dump_block(res$ind),
    ind.sup = dump_block(res$ind.sup),
    quanti.sup = dump_block(res$quanti.sup),
    quali.sup  = dump_block(res$quali.sup),
    svd     = list(vs = as.numeric(res$svd$vs))
  )
}

dump_ca <- function(res) {
  list(
    eig     = as.data.frame(res$eig),
    row     = dump_block(res$row),
    col     = dump_block(res$col),
    row.sup = dump_block(res$row.sup),
    col.sup = dump_block(res$col.sup),
    svd     = list(vs = as.numeric(res$svd$vs))
  )
}

dump_mca <- function(res) {
  list(
    eig = as.data.frame(res$eig),
    var = dump_block(res$var),
    ind = dump_block(res$ind),
    svd = list(vs = as.numeric(res$svd$vs))
  )
}

# ---- PCA on decathlon ------------------------------------------------------
data(decathlon)
res_pca <- PCA(decathlon, scale.unit = TRUE, ncp = 5,
               quanti.sup = 11:12, quali.sup = 13, graph = FALSE)
write_json(dump_pca(res_pca), file.path(out_dir("pca"), "decathlon.json"))
cat("[fixtures] pca/decathlon.json\n")

# Also dump active-only (no sup) variant for cleaner structural checks
res_pca_plain <- PCA(decathlon[, 1:10], scale.unit = TRUE, ncp = 5, graph = FALSE)
write_json(dump_pca(res_pca_plain), file.path(out_dir("pca"), "decathlon_plain.json"))
cat("[fixtures] pca/decathlon_plain.json\n")

# ---- CA on children --------------------------------------------------------
data(children)
res_ca <- CA(children, row.sup = 15:18, col.sup = 6:8, graph = FALSE)
write_json(dump_ca(res_ca), file.path(out_dir("ca"), "children.json"))
cat("[fixtures] ca/children.json\n")

res_ca_plain <- CA(children[1:14, 1:5], graph = FALSE)
write_json(dump_ca(res_ca_plain), file.path(out_dir("ca"), "children_plain.json"))
cat("[fixtures] ca/children_plain.json\n")

# ---- MCA on tea ------------------------------------------------------------
data(tea)
# Use a small slice of tea: 18 active categorical vars, with a few sup numeric/quali
res_mca <- MCA(tea, quanti.sup = 19, quali.sup = c(20:36), ncp = 5, graph = FALSE)
write_json(dump_mca(res_mca), file.path(out_dir("mca"), "tea.json"))
cat("[fixtures] mca/tea.json\n")

# ---- HCPC on PCA(decathlon) -----------------------------------------------
res_hcpc <- HCPC(res_pca_plain, nb.clust = 4, consol = TRUE, graph = FALSE)
write_json(
  list(
    clust = as.character(res_hcpc$data.clust$clust),
    data_clust_index = rownames(res_hcpc$data.clust),
    nb_clust = 4L
  ),
  file.path(out_dir("hcpc"), "decathlon_plain_k4.json")
)
cat("[fixtures] hcpc/decathlon_plain_k4.json\n")

# ---- dimdesc / catdes / condes -------------------------------------------
desc <- dimdesc(res_pca, axes = 1:2, proba = 0.05)
desc_payload <- list()
for (k in seq_along(desc)) {
  axis_name <- names(desc)[k]
  d <- desc[[k]]
  desc_payload[[axis_name]] <- list(
    quanti = if (!is.null(d$quanti)) as.data.frame(d$quanti) else NULL,
    quali  = if (!is.null(d$quali))  as.data.frame(d$quali)  else NULL,
    category = if (!is.null(d$category)) as.data.frame(d$category) else NULL
  )
}
write_json(desc_payload, file.path(out_dir("dimdesc"), "pca_decathlon.json"))
cat("[fixtures] dimdesc/pca_decathlon.json\n")

# catdes on tea (Tea-time as target)
catdes_tea <- catdes(tea, num.var = which(names(tea) == "Tea"), proba = 0.05)
catdes_payload <- list(
  test.chi2 = if (!is.null(catdes_tea$test.chi2)) as.data.frame(catdes_tea$test.chi2) else NULL,
  category  = if (!is.null(catdes_tea$category))  lapply(catdes_tea$category, as.data.frame) else NULL,
  quanti.var = if (!is.null(catdes_tea$quanti.var)) as.data.frame(catdes_tea$quanti.var) else NULL,
  quanti     = if (!is.null(catdes_tea$quanti))     lapply(catdes_tea$quanti, as.data.frame) else NULL
)
write_json(catdes_payload, file.path(out_dir("catdes"), "tea_Tea.json"))
cat("[fixtures] catdes/tea_Tea.json\n")

# condes on decathlon with Points as the continuous target
condes_dec <- condes(decathlon, num.var = which(names(decathlon) == "Points"), proba = 0.05)
condes_payload <- list(
  quanti   = if (!is.null(condes_dec$quanti)) as.data.frame(condes_dec$quanti) else NULL,
  quali    = if (!is.null(condes_dec$quali))  as.data.frame(condes_dec$quali)  else NULL,
  category = if (!is.null(condes_dec$category)) as.data.frame(condes_dec$category) else NULL
)
write_json(condes_payload, file.path(out_dir("condes"), "decathlon_Points.json"))
cat("[fixtures] condes/decathlon_Points.json\n")

cat("\ndone.\n")
